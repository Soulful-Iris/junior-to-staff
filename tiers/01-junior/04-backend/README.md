# 04 · Backend

> Junior tier · feeds **P1 (it works)**

## The one-liner

The backend is where a click becomes a row in a database — the code that takes
requests from the outside world and decides what actually happens. Two facts
define the job: everything that arrives is a message from a stranger, and
everything you promise has to stay true when two strangers arrive at once. A
frontend bug is wrong on one screen; a backend bug is wrong for everyone at the
same time.

## The failure it prevents

You ship the reading list. Someone pastes a link to a server that accepts the
connection and then never sends a byte — a half-crashed machine, a hotel
captive portal, a load balancer with nothing behind it. The internet is full of
these.

Your title-fetch code waits. How long? You never said, so you inherited the
default of whatever HTTP client you happen to be using. In Node's built-in
`fetch` that is five minutes before it gives up waiting for response headers
(300 seconds; checked 2026-09-21). In Python's `requests` there is no default
at all — the official docs warn that without a timeout "your code may hang for
minutes or more," which in practice means until the socket dies (checked
2026-09-21).

Your app has a handful of worker processes, and each pasted link ties one up.
Nothing crashes. Nothing logs an error, because nothing is wrong — everything
is just waiting. A few links later the sign-in page stops loading for everyone,
and the restarted process looks perfectly healthy right up until it does not.

One pasted URL, zero exceptions, whole site down. That is what an unchosen
timeout costs, and it is one entry on a longer list this section is about:
every place between the click and the row where a request can stop, and who
finds out when it does.

## The mental model

A request is a message on a journey, and the journey is longer than it looks.
The browser turns a name into an address (DNS), opens an encrypted connection
(TLS), and sends a few hundred bytes of structured text. Those bytes cross
machines you do not own. They arrive at your process, where a router decides
which code runs, the body is parsed and validated, an auth check decides who is
asking, and your handler finally does the work — reading and writing the
database, sometimes calling someone else's server. Then a response makes the
same trip in reverse, to a browser that may or may not still be waiting. The
order of the middle steps varies by framework; the stops do not.

![One request travels from the browser through the router, auth and handler to the database and back as the reply; seven numbered markers show where it can stop: the network, the router, auth, the handler, the outbound fetch, the database, and the reply itself](../../../assets/diagrams/request-lifecycle.svg)

Three ideas survive any change of framework.

**Every hop is a place it can stop, and each stop needs an owner.** HTTP gives
you the vocabulary for this, and it is a contract, not decoration: 4xx means
the sender got it wrong, 5xx means you did. GET must never change anything.
PUT and DELETE are idempotent — doing them twice leaves the world as doing them
once — while POST is not guaranteed to be (RFC 9110; checked 2026-09-21).
Idempotency matters because networks deliver things twice, and users
double-click. Failures come in three kinds: the ones you expected (a 4xx with a
clear message), the ones you did not (a 5xx, logged loudly with a stack trace
and a request id), and the ones you swallowed — caught, hidden, returned as
success. The third kind costs the most, and it is no longer just a code smell:
the 2025 revision of the OWASP Top 10 added "Mishandling of Exceptional
Conditions" as a category in its own right (checked 2026-09-21).

**Your process is disposable; nothing true lives in it.** It will be restarted,
duplicated, killed mid-request. That has two consequences. Truth lives in the
database — and since two requests can interleave anywhere, "read a value,
change it, write it back" is a bug waiting for company: both read 4, both write
5, one update vanishes without an error. A transaction is the database's
promise that a group of changes happens entirely or not at all, and is not seen
half-done by anyone else. Identity comes from the environment — a disposable
process cannot carry its own secrets, so configuration arrives at start time:
harmless defaults in committed files, everything machine-specific and
everything secret through environment variables or a secret store. A repo is
designed to be copied everywhere, which is exactly why a password must never
enter one.

**Everything that crosses the boundary is untrusted.** Body, headers, URL,
cookies: attacker-controlled bytes until you have checked them. The reading
list makes this sharp, because it fetches URLs users hand it. Your server sits
somewhere privileged — inside a network, possibly next to a cloud metadata
service — and a user who submits `http://localhost:5432/` or an internal admin
URL is asking *your server* to make that request from *its* position. That is
server-side request forgery (SSRF). It held its own slot in the OWASP Top 10 in
2021; the 2025 revision folded it into Broken Access Control (checked
2026-09-21), and the reclassification is the lesson: the flaw is that you never
decided what your fetcher was allowed to reach.

## What good looks like

- Status codes tell the truth. Every failure is a 4xx or 5xx; a 200 with an
  error inside the body is a lie that the frontend, the caches, and the
  monitoring will all believe.
- Errors have one shape everywhere: a machine-readable code, a human message,
  a request id that also appears in the logs.
- Every outbound call has a timeout that is visible in the code, with the
  number chosen on purpose.
- GET changes nothing; repeating a PUT or DELETE changes nothing more; a
  duplicate POST does something you decided in advance.
- Input is validated at the edge, so handler logic starts only after the shape
  of the input has been proven.
- Config comes from the environment; the repo holds an example file with the
  names of the variables and none of the values.
- The read-modify-write paths are inside transactions or single atomic
  statements.

Done badly, you see:

- `200 {"success": false}`.
- A catch block that logs nothing and returns something.
- The database password in a committed config file, "to rotate later."
- An outbound fetch with no timeout anywhere in sight.
- A fetcher that will happily request `http://169.254.169.254/` — the address
  where cloud providers serve a machine's own credentials.
- Code that works every time you click it and corrupts data under two
  simultaneous clicks — which the tests never produce, because tests run one
  at a time.

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

*Why it is asked that way:* the failure column is the part both juniors and
models skip, so it is demanded first, before a happy path exists to crowd it
out. The second paragraph turns "don't return 200 on failure" from a rule into
a visible cost.

*What you should get back:* a boring table. Nouns in the paths, methods as the
verbs, and mostly 200, 201, 400, 401, 403, 404, 409. Boring is the good
outcome — every tool, cache, and engineer already understands it.

*Push back on:* any failure that comes back as 200; POST used for reads;
inventive shapes (verbs in paths, everything wrapped in a custom envelope)
that trade a decade of shared convention for nothing.

**Request 2 — hostile-input review of the fetcher**

```
Here is the code that fetches a user-submitted URL and reads the page
title. Assume the URL was chosen by someone who wants to hurt this server.

First list every way it can: where the request can hang, which internal
addresses it could be pointed at, how large a response it might swallow,
and what a redirect can do to any check you add.

Then fix each item: a total timeout I name, a response size cap, an
allowlist of URL schemes, and a block on private and internal addresses
that still holds after redirects. For each fix, say exactly what the user
sees when it fires.
```

*Why:* "assume hostile" flips the model from helping the URL succeed to
attacking it, and demanding the list before the fixes means every fix maps to
a named threat. The redirect clause is there because it is the classic bypass:
validate the URL, then obediently follow a redirect to the address you just
blocked.

*What you should get back:* the words timeout, size cap, scheme allowlist, and
private-address block, each tied to a user-visible outcome rather than a
silent one.

*Push back on:* validation that checks the hostname string but fetches
whatever it resolves to; a timeout on connecting but none on reading the body;
any attempt to "sanitise" a bad URL instead of refusing it.

**Request 3 — prove the race, then fix it**

```
Find every place in this code that reads a value, changes it, and writes
it back. For the most important one, write a test that runs two of those
operations concurrently and demonstrates the lost update — I want to see
it fail before any fix exists.

Then fix it with a transaction or a single atomic statement, and show the
same test passing.
```

*Why:* the same discipline as [06 · Testing](../06-testing/) — evidence that
the bug exists before you trust the fix. A concurrency fix without a red test
first is a guess that happened to compile.

*Push back on:* a test that fakes concurrency with sleeps and sequential
calls, and any fix that adds an in-process lock — it stops working the moment
you run a second process, which is the first thing that happens after P1.

## How you would know it is wrong

The checks for this topic, each one capable of going red:

1. **Kill the database mid-request.** Start a request that writes, stop the
   database while it is in flight. You want a clean 5xx within seconds, no
   half-written rows, and recovery without a restart when the database comes
   back. A 200, a hang, or a half-saved item is a red result.
2. **Point the fetcher at a URL that hangs.** A server that accepts and never
   responds is one shell command away. Time the request with a clock: it must
   give up within the seconds *you* chose. "It errored eventually" is a fail —
   eventually was the default, not a decision.
3. **Send a malformed body.** Truncated JSON, wrong types, a ten-megabyte
   string. You want a 400 with your structured error shape. A 500 means
   untrusted bytes reached code that assumed their shape; a stack trace in the
   response means you are publishing your internals.
4. **Call the same endpoint twice.** Submit the same URL twice, fast. Whatever
   you documented should happen. Two identical rows means you did not decide,
   you discovered.
5. **Ask the fetcher for something internal.** `http://localhost:5432/`, a
   private-range address, `http://169.254.169.254/`. The refusal must happen
   before any connection is opened — and it must survive a public URL that
   redirects to the same place.
6. **Grep the repo for a secret you know, history included** (`git log -p`
   piped through grep). One hit means the secret is public to everyone who
   ever clones, and the fix is rotation, not deletion — history is the repo.

> The rule under all six: **before believing a green result, say what it would
> have looked like if the thing were broken.** A fetcher you never pointed at
> a hostile URL is not safe; it is untested.

## Your slice of the project

On **P1**, this section is the add-a-URL flow done properly:

- The endpoint table from Request 1, committed to the repo *before* the
  handlers exist, failure column included.
- The title fetcher with a total timeout you chose (write the number and the
  reason next to it), a response size cap, a scheme allowlist, and a
  private-address block. A failed fetch still saves the item, with the failure
  visible on it rather than swallowed.
- One structured error shape — code, message, request id — used by every
  handler, and no 200-with-a-failure-inside anywhere.
- The one genuinely concurrent write you have (two people marking the same
  item read is a fine candidate) protected by a transaction or atomic update,
  with the red-then-green test from Request 3 as evidence.
- Secrets via the environment: an example env file in the repo, the real one
  ignored, and an app that refuses to start with a clear message naming any
  missing variable.

**Acceptance criteria you can check yourself:**

- Checks 1 through 5 above each run once, with what you saw written down.
- The hanging-URL check completes within your chosen timeout plus one second,
  measured, not felt.
- Grepping the full git history for your database password and session secret
  returns nothing.
- A fresh clone with only the example env file fails to start with a message
  that names the missing variable — not a stack trace.

## Words you now own

- **endpoint** — one method plus one path your server answers; the unit of API contract.
- **status code** — the machine-readable verdict: 2xx worked, 4xx the sender's problem, 5xx yours.
- **idempotent** — safe to repeat; the second identical call changes nothing more.
- **validation** — proving input has the shape you expected before acting on it.
- **structured error** — a failure with a machine-readable code and a request id, not just prose.
- **request id** — a random id minted per request and carried into logs and error responses, so one user's bad afternoon can be found later.
- **timeout** — the longest you are willing to wait, chosen on purpose.
- **transaction** — a group of database changes that happens entirely or not at all, and is never seen half-done.
- **race condition** — two interleaved operations producing a result neither would produce alone; the lost update is the starter kind.
- **environment variable** — configuration the process reads at start; how secrets reach code without living in it.
- **SSRF** — server-side request forgery: tricking a server into making requests from its own privileged position.

---

**Not covered here:** the database in its own right — modelling, indexes,
migrations — has its own section; here it is simply where truth lives. The
internals of authentication (passwords, sessions, tokens) likewise. Retries,
queues, caching and rate limits are P3 problems, and deploying and observing
this backend is P2. Nothing here is about making it fast, either — a backend
first has to be right when things go wrong, which is most of what a backend is.
