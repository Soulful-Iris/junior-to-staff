# Backend

[Curriculum](../../README.md) · [Backend and APIs](README.md)

> Project connection · feeds **P1 (it works)**

## At the whiteboard

> “Our save-link API fetches the page title before replying. One destination
> accepts connections but never answers. Soon nobody can save a link. Where
> would you put time and capacity limits, and what would the API promise?”

A backend converts an untrusted request into an authorized state change. Every
dependency wait consumes a budget; choosing no budget still creates behavior.

| Teaching workload | Expected behavior |
|---|---|
| `POST /links` with a valid owned URL | Validate and durably record accepted work |
| Title server takes `30 s`; API budget is `500 ms` | Do not hold the API open for `30 s` |
| Same operation key repeated with same payload | Return the recorded operation result |
| Same key with different URL | Reject the conflict; do not silently reuse it |

These are exercise requirements, not AWS limits. **Ask first:** must the title be
ready before acceptance, or can it appear later?

```mermaid
flowchart TD
  Client[Client] --> API[API workers]
  API --> Remote[Unbounded title fetch]
  Remote --> Waiting[Workers occupied]
  Waiting --> Other[Other saves cannot start]
```

## Reason through the boundary

1. Decide whether acceptance means “stored” or “fully enriched.” Return a job
   identifier only after the promised durable state exists.
2. Validate URL and ownership before work. Restrict outbound destinations so a
   public URL field cannot fetch internal services.
3. Move optional enrichment behind a bounded queue and explicit worker deadline.
   A queue absorbs a burst; it does not fix a permanent arrival-rate overload.
4. Test a hanging destination, duplicate delivery, and a crash after saving the
   result. Define what can repeat and what remains atomic.

**Follow-up:** “Traffic doubles while title workers are stalled. Does the queue
make us safe?” Draw admission and recovery; backlog growth still needs a bound.

```mermaid
flowchart TD
  Client[Client] --> Admission[Validate and admit within budget]
  Admission --> DB[(Operation record)]
  DB --> Queue[Durable work queue]
  Queue --> Workers[Bounded workers with deadlines]
  Workers --> Remote[Allowed external pages]
  Workers --> Result[(Versioned result)]
  Queue --> Reject[Age and backlog policy]
```

AWS's SQS and Lambda are possible implementations of these boxes; the invariant
and failure policy come first. Keep external fetching distinct from the narrower
atomic-result guarantee in the queue lab.

## The one-liner

The backend is where a click becomes a row in a database — the code that takes
requests from the outside world and decides what actually happens. Everything
that arrives is a message from a stranger, and everything you promise must
stay true when two strangers arrive at once. A frontend bug is wrong on one
screen; a backend bug is wrong for everyone.

## The failure it prevents

You ship the reading list. Someone pastes a link to a server that accepts the
connection and then never sends a byte — a half-crashed machine, a load
balancer with nothing behind it.

Your title-fetch code waits. How long? You never said, so you inherited your
HTTP client's default. In Node's built-in `fetch` that is five minutes
waiting for response headers (300 seconds; checked 2026-09-21). In Python's
`requests` there is no default at all — the docs warn that without a timeout
"your code may hang for minutes or more" (checked 2026-09-21).

Each pasted link ties up one of your handful of worker processes. Nothing
crashes and nothing logs, because nothing is wrong — everything is just
waiting. A few links later, the sign-in page stops loading for everyone.

One pasted URL, zero exceptions, whole site down. That is the cost of an
unchosen timeout — one entry on this section's list: every place
between the click and the row where a request can stop, and who finds out when
it does.

## The mental model

A request is a message on a journey. The browser turns a name into an address
(DNS), opens an encrypted connection (TLS), and sends a few hundred structured
bytes across machines you do not own. At your process a router picks the code,
the body is parsed and validated, auth decides who is asking, and your handler
does the work — reading and writing the database, sometimes calling someone
else's server. The response makes the same trip in reverse, to a browser
that may no longer be waiting. The order of the middle steps varies by
framework; the stops do not.

![One request travels from browser through router, auth and handler to the database and back; numbered markers show the seven places it can stop, from the network to the reply itself](../../../assets/diagrams/request-lifecycle.svg)

Three ideas survive framework churn.

**Every hop is a place it can stop, and each stop needs an owner.** HTTP is
the contract for saying so: 4xx reports client/request-side failure; 5xx reports
server-side failure. A safe GET does not request a state-changing operation;
incidental logging is allowed. PUT and DELETE are idempotent in their intended
effect, not necessarily their response or logs. POST has no default idempotency
guarantee and can also represent a complex query (RFC 9110;
checked 2026-09-21), which matters because networks deliver things twice and
users double-click. Failures come in three kinds: expected (a 4xx with a clear
message), unexpected (a 5xx, logged loudly with stack trace and request id),
and swallowed — caught, hidden, returned as success. The third costs the
most; the 2025 OWASP Top 10 added "Mishandling of Exceptional Conditions" as a
category of its own (checked 2026-09-21).

**Your process is disposable; nothing true lives in it.** Restarted,
duplicated, killed mid-request; truth lives in the database. Requests
interleave, so "read a value, change it, write it back" is a bug waiting for
company: both read 4, both write 5, one update vanishes without an error. A
transaction commits a group atomically, but its isolation and write predicates
must also protect the invariant. `BEGIN` alone does not stop both callers from
reading 4 and assigning 5. Use `UPDATE count = count + 1`, a version-guarded
update, a row lock around read/decide/write, or serializable isolation with
whole-transaction retry. Identity comes from the environment:
harmless defaults in committed config files; secrets handed to the process at
start, as environment variables set by whatever launches it, or read from a
secret store. Never the repo — a repo is designed to be copied
everywhere.

**Everything crossing the boundary is untrusted.** Body, headers, URL,
cookies: attacker-controlled bytes until checked. The reading list makes this
sharp because it fetches URLs users hand it. Your server sits somewhere
privileged — inside a network, possibly next to a cloud metadata service — so
a user who submits `http://localhost:5432/` is asking *your server* to make
that request from *its* position. That is server-side request forgery (SSRF).
OWASP gave it its own slot in 2021 and folded it into Broken Access Control in
the 2025 revision (checked 2026-09-21); the reclassification is the lesson —
you never decided what your fetcher was allowed to reach.



## What good looks like

- Status codes describe the HTTP operation: a rejected charge needs the documented
  failure status; a successful GET may return a job whose domain state is failed.
- Errors have one shape everywhere: machine-readable code, human message, a
  request id that also appears in the logs.
- Every outbound call has a timeout visible in the code, chosen on purpose.
- GET requests no destructive effect; repeated PUT/DELETE preserve the intended
  idempotent effect; duplicate POST behavior is defined explicitly.
- Input is validated at the edge; handler logic starts after the shape is
  proven.
- Config comes from the environment; the repo holds an example file with
  variable names and none of the values.
- Read-modify-write paths name their enforcing predicate, row lock, or isolation level—not only a transaction wrapper.

Done badly, you see:

- A rejected `POST /charges` reported as a successful charge; this is different from `GET /jobs/42` returning `200 {"state":"failed"}`.
- A catch block that logs nothing and returns something.
- The database password in a committed config file, "to rotate later."
- A fetcher that will happily request `http://169.254.169.254/`, where cloud
  providers serve a machine's own credentials.
- Code that works every time you click it and corrupts data under two
  simultaneous clicks, which sequential tests never produce.

## Ask Claude for this

**Request 1 — the contract before the code**

```
I am building <feature: e.g. "add a URL to a shared reading list">.

Before any code: list every endpoint as a table — method, path, what it
does, the success status, and every failure it can return, each with its
status code and a structured error code.

Then tell me which failures on that list my frontend would never find out
about if the endpoint returned 200 with an error message inside the body.
```

*Why it is asked that way:* the failure column is what juniors and models both
skip, so it is demanded before a happy path exists to crowd it out. The second
paragraph distinguishes a failed HTTP operation from a successful representation of failed background work.

*What you should get back:* a boring table — nouns in the paths, methods as
verbs, mostly 200, 201, 400, 401, 403, 404, 409. Boring is the win:
everything already understands it.

*Push back on:* failed operations disguised as success, destructive GET requests,
or undocumented retry semantics. A logged GET is still safe; a documented POST
query is valid when its semantics and caching trade-offs justify it.

**Request 2 — hostile-input review of the fetcher**

```
Here is the code that fetches a user-submitted URL and reads the page
title. Assume the URL was chosen by someone who wants to hurt this server.

First list every way it can: where the request can hang, which internal
addresses it could be pointed at, how large a response it might swallow,
and what a redirect can do to any check you add.

Then fix each item: a total timeout I name, a response size cap, an
allowlist of URL schemes, and a block on private and internal addresses
that still holds after redirects. For each fix, say what the user sees
when it fires.
```

*Why:* "assume hostile" flips the model from helping the URL succeed to
attacking it, and list-first means every fix maps to a named threat. The
redirect clause names the classic bypass: validate, then obediently follow a
redirect to the address you just blocked.

*What you should get back:* timeout, size cap, scheme allowlist,
private-address block — each tied to a user-visible outcome, not a silent one.

*Push back on:* checking the hostname string but fetching whatever it resolves
to; a timeout on connect but none on the body; "sanitising" a bad URL instead
of refusing it.

**Request 3 — prove the race, then fix it**

```
Find every place in this code that reads a value, changes it, and writes
it back. For the most important one, write a test that runs two of those
operations concurrently and demonstrates the lost update — I want to see
it fail before any fix exists.

Then choose the enforcing mechanism: an atomic relative update, a guarded update
with an affected-row check, a row lock held through the write, or serializable
isolation with bounded whole-transaction retry. State the isolation level and
show the same controlled schedule preserving the invariant.
```

*Why:* the same discipline as [Testing](../04-testing/testing-strategy.md) — evidence the
bug exists before you trust the fix. A failing reproduction strengthens the
evidence; a separately justified invariant and real concurrent test also matter.

*What you should get back:* one red run showing the lost update, then the same
test green after the fix, in that order.

*Push back on:* sleep-only ordering or a process-local lock presented as a
multi-process guarantee. Use two independent database sessions; the
[PostgreSQL lab](../02-databases/labs/postgresql/README.md) includes the naive
transactional schedule, guarded stock decrement and serializable retry.

| Two callers start at 4 | Final value / decision |
|---|---|
| Both `BEGIN`; both read 4; both assign 5 | 5: atomic transactions still lost an update |
| Both `UPDATE counters SET value = value + 1` | 6: each update uses the protected current value |
| Both guard `WHERE version = 7` | One row changes; the loser handles a conflict |

For stock: `UPDATE inventory SET available=available-1 WHERE id=:id AND available>0 RETURNING available`.
Insert the reservation in that same transaction **only if a row returned**.
The conditional decrement prevents negative stock; the transaction couples it
to the reservation. SQL execution evidence belongs to the database lab, not this table.

## How you would know it is wrong

The checks for this topic, each one capable of going red:

1. **Kill the database mid-request.** Stop the database while a write is in
   flight. You want a clean 5xx within seconds, no half-written rows, and
   recovery without a restart when it returns. A 200, a hang, or a half-saved
   item is red.
2. **Point the fetcher at a URL that hangs.** Time it with a clock: the
   request must give up within the seconds *you* chose. "It errored
   eventually" is a fail — eventually was the default.
3. **Send a malformed body.** Truncated JSON, wrong types, a ten-megabyte
   string. You want a 400 in your structured shape. A 500 means untrusted
   bytes reached code that assumed their shape; a stack trace in the response
   publishes your internals.
4. **Call the same endpoint twice.** Submit the same URL twice, fast. Whatever
   you documented should happen. Two identical rows means you did not decide,
   you discovered.
5. **Ask the fetcher for something internal.** `http://localhost:5432/`, a
   private-range address, `http://169.254.169.254/`. The refusal must come
   before any connection opens — and survive a public URL that redirects
   there.
6. **Grep the repo for a secret you know, history included** (`git log -p`
   piped through grep). One hit means it belongs to everyone who ever clones;
   the fix is rotation, not deletion — history is the repo.

> Underneath all six: **before believing a green result, say what it would
> have looked like if the thing were broken.** A fetcher never pointed at a
> hostile URL is not safe; it is untested.

## Your slice of the project

On **P1**, this section is the add-a-URL flow done properly:

- The endpoint table from Request 1, committed *before* the handlers exist,
  failure column included.
- The title fetcher with a total timeout you chose (write the number and the
  reason next to it), a size cap, a scheme allowlist, and a private-address
  block. A failed fetch still saves the item, failure visible on it.
- One structured error shape — code, message, request id — used by every
  handler; distinguish failed requests from successfully retrieved domain states.
- Your one genuinely concurrent write (two people marking the same item read,
  say) protected by a named atomic predicate, lock or isolation/retry protocol,
  with Request 3's controlled two-session test as evidence.
- Secrets via the environment: an example env file in the repo, the real one
  ignored.

**Acceptance criteria you can check yourself:**

- Checks 1 through 5 each run once, with what you saw written down.
- The hanging-URL check completes within your chosen timeout plus one second,
  measured, not felt.
- Grepping the full git history for your database password and session secret
  returns nothing.
- A fresh clone with only the example env file refuses to start, naming the
  missing variable — not a stack trace.

## Words you now own

- **endpoint** — one method plus one path your server answers; the unit of API contract.
- **status code** — the machine-readable verdict: 2xx worked, 4xx the sender's problem, 5xx yours.
- **idempotent** — safe to repeat; the second identical call changes nothing more.
- **structured error** — a failure with a machine-readable code and a request id, not just prose.
- **timeout** — the longest you are willing to wait, chosen on purpose.
- **transaction** — a group of database changes that happens entirely or not at all, never seen half-done.
- **race condition** — two interleaved operations producing a result neither would alone; the lost update is the starter kind.
- **environment variable** — configuration the process reads at start; how secrets reach code without living in it.
- **SSRF** — server-side request forgery: tricking a server into making requests from its own privileged position.

---

**Not covered here:** the database itself — modelling, indexes, migrations —
has its own section; here it is where truth lives, nothing more.
Authentication internals (passwords, sessions, tokens) likewise. Retries,
queues, caching and rate limits are P3; deploying and observing this backend
is P2. Nothing here is about speed — a backend first has to be right when
things go wrong, which is most of what a backend is.

[Learning sequence](../../README.md) · [Independent practice](../../../practice/interview-guide.md)

## Draw it from memory · Put authority on the server side

```mermaid
flowchart TD
  Browser["Untrusted request"] --> Router["Router + input validation"]
  Router --> Auth["Identity and object authorization"]
  Auth --> Handler["Business invariant"]
  Handler --> DB[("Database constraint / transaction")]
  Handler --> Fetch["Outbound fetch: timeout + URL policy"]
  Fetch --> External["Untrusted external server"]
  DB --> Reply["Response after commit"]
  Reply --> Browser
```

**Redraw challenge:** Mark the point where a committed write can lose its response. Explain the safe retry.

![Put authority on the server side: mechanism in motion](../../../assets/learning/conditional-result.svg)

[Static view](../../../assets/learning/conditional-result-still.svg)
