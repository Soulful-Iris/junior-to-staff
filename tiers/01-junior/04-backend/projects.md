# 04 · Backend — five projects

> Junior tier · each one an afternoon · read [the section](README.md) first

Five projects, rising. Each one isolates a different thing the backend owes
the world outside it: an account of what it did, an answer on time, a refusal
it can prove, a promise kept to old callers, and work that survives its own
death. All five build on P1's reading list, and in all five the order of the
asks matters more than the code that comes back.

![A caller's three-second budget spent down a call chain: the handler spends half a second and hands 2.5 seconds to the title fetcher, which keeps its own ten-second timeout — so from three seconds on the caller is gone and the fetch runs seven and a half more seconds, holding a worker, for nobody](../../../assets/diagrams/timeout-budget.svg)

---

### 1. The request you can trace end to end

*You end up able to take one id from an error message and reconstruct
everything that request did, in order, with timings.*

**Build**

P1 emits one structured JSON event for each step of every request — an id
minted at the entry point, carried through auth, the database and the title
fetch, echoed in the response headers and in every error body. Plus a script
that takes an id and prints that request's story.

**The thought process**

The first decision is what the evidence belongs to. Processes produce logs,
but requests are what break, and until every line carries the id of the
request that caused it, the logs are a pile sorted by time — and under
concurrency, time lies.

Second, where the id is born: mint it at your own front door. An id accepted
from any browser header is a field strangers get to write; believe an inbound
one only from infrastructure you own.

Third, the event shape is an API whose consumer is you at 3am — id, timestamp,
event name, duration, outcome. Decide the fields once, or every handler
invents a dialect and grep becomes archaeology. And decide what never appears:
secrets, whole bodies, URLs with tokens in them. Logs are copied to more
places than your database will ever be.

**How to organise the prompts**

**1. The inventory.**

```
Read this repository. List every place a request leaves evidence today —
log lines, prints, uncaught errors. For each one: could I tell WHICH
request produced it? Do not write any code.
```

The honest answer is mostly no, and that list is the case for the work.

**2. The shape, then the thread.**

```
Design one JSON log event: request id, timestamp, event name, duration,
outcome. Mint the id at the entry point, return it in a response header
and in the error body, and wrap the database calls and the title fetch so
each logs start and finish with the id.

Show me the event shape and where the id is born before writing the rest.
```

Check with one curl: grep the id, count the events — every step you know
about, present exactly once.

**3. The stitcher.**

```
Write a script: given a request id, print that request's events in order
with elapsed milliseconds between them. If the story has a hole — a fetch
that started and never finished — say so instead of hiding it.
```

Point it at a request whose fetch hangs. The visible hole is the deliverable.

**On AWS**

**CloudWatch Logs**, for what you do not build: log JSON to stdout and Lambda
or Fargate ship it automatically, where EC2 has you installing and patching an
agent. **Logs Insights** queries the JSON fields directly, which at one
application's scale removes the case for **OpenSearch** — a cluster that runs,
and bills, while you sleep. **X-Ray** is this project done by infrastructure;
meet it after threading the id by hand once. Set retention when you create the
log group — left alone it keeps everything forever, which is the quiet cost
here.

**What productionising it means**

A metric filter on error events feeding an alarm, so the logs page you before
a user does. The id shown in the UI's error state, so a support message
arrives holding the exact thread to pull. And a second person able to answer
"what happened to this request" with one query — the test of whether your
event shape was an API or a habit.

**The learning**

Evidence belongs to requests, not processes. Once one id threads the whole
journey, everything later — metrics, tracing, support — hangs off it. A
backend that cannot narrate one request is operated by guessing.

**How you would know it is wrong**

- Point the fetch at a URL that hangs. The story must show a started-and-never-finished step, not a clean-looking gap.
- Force a 500 and take the id from the error body. One grep must land on the stack trace.
- Fire two requests concurrently: two clean stories, no line belonging to both.
- Send a password-shaped value in a request body, then grep the logs for it. One hit means the pipeline leaks.

---

### 2. The three-second budget

*You end up with every outbound call bounded by a number you chose, retries in
exactly one place, and a POST that is safe to send twice.*

**Build**

A time budget for P1's add-a-URL request: a deadline minted at the door and
spent down the chain — the diagram above — every outbound timeout derived from
what remains, retries living only in the fetch client, and an idempotency key
so a retried POST cannot create two rows.

**The thought process**

The top number comes first: how long will a person wait before the answer is
worthless? Three seconds is defensible; pick yours and write it down. Until it
exists, every timeout below it is a guess about a whole nobody named.

Then the arithmetic: budgets subtract. A hop may spend what is left, not what
feels generous, and the diagram's failure is a hop whose own timeout exceeds
what it was handed — the caller gone at three seconds, the fetch doing seven
more seconds of work for nobody, holding a worker throughout.

Third, retries live in one layer, chosen. They multiply through a stack —
three layers each retrying three times is twenty-seven calls at the bottom —
so they belong where the failure is understood, here the fetch client. A retry
spends budget too: both attempts plus the backoff must fit the same deadline.

Last, what makes a retry safe: nothing, by default — the network can lose a
response after the insert happened. Safety is built: the client mints a key,
the server remembers the first outcome and returns it to replays. The section
said a duplicate POST does something you decided in advance; here you decide.

**How to organise the prompts**

**1. The timeout census.**

```
List every outbound call this system makes — HTTP, database, anything
that leaves the process. For each: the timeout it has today, and whether
that number was chosen or inherited from a library default. No fixes yet.
```

Every row that says "inherited" is the section's opening failure, waiting. The
table becomes the budget.

**2. The deadline, passed down.**

```
The whole request gets 3.0 seconds. Create a deadline at the entry point
and pass it down: every outbound call's timeout becomes the smaller of
its own cap and the time remaining, and a call asked to start with
nothing left fails at once instead of trying.

Show me the budget as a table before changing any code.
```

The worst case must sum to 3.0 or less. If it cannot, something on the list
does not belong in the request at all — that is project 5.

**3. Retries, then the key.**

```
Add retries for the title fetch only: at most two, exponential backoff
with jitter, only on timeouts, connection failures and 5xx — never 4xx —
and both attempts must fit inside the same 3.0s deadline.

Then make the POST safe to retry: the client sends an Idempotency-Key,
and a replay returns the first attempt's result instead of inserting
again. Prove it by cutting the connection after the insert but before
the response, then retrying.
```

The proof is the checkpoint: one row in the database, two identical responses.

**On AWS**

The edge enforces a budget whether you chose one or not: **API Gateway** REST
APIs wait at most 29 seconds for an integration by default, raisable for
regional and private REST APIs at the possible cost of a reduced throttle
quota (checked 2026-09-22). An **ALB** mostly hands the socket through —
gateway as opinionated budget-keeper at the door, ALB as plumbing you
instrument yourself. Pair the numbers deliberately: **Lambda** runs up to
900 seconds (checked 2026-09-22), so a function timeout above your edge's is
the diagram at cloud scale — the 504 long since sent, the function still
running and still billed. Set the inner number below the outer one, on
purpose.

**What productionising it means**

The budget is a file in the repository that changes by review, not numbers
smeared across call sites. Timeout rate and retry rate become their own
metrics — a retry storm can look healthy in error rate alone. And retries get
an environment-variable kill switch, because during an incident retries
convert failure into load, and you want a lever, not a deploy.

**The learning**

A timeout is a claim about the whole chain, not one call, and a default is
someone else's claim about a system that is not yours. Retries are extra load,
safe only where a repeat is provably harmless — a proof you construct, never
assume.

**How you would know it is wrong**

- Point the fetch at a URL that hangs and wall-clock the request: 3.0 seconds plus a little, measured, not felt.
- Read the logs from that run: fetch activity stamped after the deadline means the budget is decoration.
- Send the same Idempotency-Key twice: one row, byte-identical responses.
- Make the upstream return 400: exactly one attempt in the logs.

---

### 3. The fetch that cannot be aimed inward

*You end up with a title fetcher that can be handed any URL and can only ever
reach the public internet — with a test that proves each refusal.*

**Build**

One guarded HTTP client that everything in P1 fetches through: scheme
allowlist, resolve-then-connect to the exact address that was vetted, refusals
for private, loopback, link-local and metadata addresses, every redirect
re-vetted, plus project 2's deadline and a size cap. Refusals are coded 4xxs,
and the item still saves with the failure visible.

**The thought process**

Start from the job description, not the threat list. The fetcher exists to
read public web pages, so the posture is deny by default: http and https, to
public addresses, everything else refused because it was never the job. The
section explained the stakes — your server stands somewhere privileged, and a
user-supplied URL is a request made from *its* position.

The decision that makes the project: a check must bind to the connection it
protects. A URL is indirection — the name you inspect is not the place you
connect — so the guard resolves the name, vets the resolved address, and
connects to exactly that. Inspecting the string and then connecting to
whatever it resolves to a moment later is inspecting a costume.

A redirect is a new fetch; approval does not survive it. Each hop gets the
whole check again, capped, because the classic hole is a public URL
redirecting somewhere internal, followed obediently by code that finished its
checking a hop ago. And the guard lives in one place — the client — so
project 5's worker inherits safety without anyone remembering to add it.

**How to organise the prompts**

**1. The map of what could reach you.**

```
Here is the code that fetches user-submitted URLs. Assume any URL. List
every way this fetch could be made to reach something inside my network
or my cloud account, hang forever, swallow something enormous, or be
re-aimed after a check has passed. Rank the list by how likely I am to
have missed each one. No code.
```

If redirects and re-resolution are missing, the list is not finished — push
back. What survives is the client's specification.

**2. The one guarded client.**

```
Build a single guarded fetch client and route every fetch in this
codebase through it: allow only http and https, resolve the hostname,
refuse private, loopback, link-local and metadata ranges, connect to the
exact address that passed, re-run the whole check on every redirect
(maximum three), enforce the deadline and a 1 MB response cap. Every
refusal is a distinct 4xx with a code.
```

Before moving on, grep for any fetch that bypasses the client. One bypass and
the guard is a suggestion.

**3. The refusals, proven.**

```
Write the refusal tests: one per promise, each able to fail. Include a
test that starts a listener on a local port and proves the fetcher never
opened a connection to it, and one where a public URL redirects to an
internal address. Then remove the guard on a branch and show me every
one of these tests going red.
```

The remove-the-guard run is the instrument check: a safety suite that stays
green without the safety has measured nothing.

**On AWS**

Why the position is privileged, concretely: on **EC2** the machine's own
credentials are served over plain HTTP from the metadata service the section
named — require the session-based **IMDSv2** so a bare forged GET gets
nothing. A **Fargate** task holds its role credentials at a link-local
endpoint too. **Lambda** is the odd one out — no metadata endpoint reachable
from code — so moving just the fetcher into its own Lambda with a role that
can do almost nothing is real defence in depth: whatever is tricked arrives in
a room with nothing in it. Whichever you run, add the network layer: the
fetcher gets a route to the internet and to nothing internal. At P1 volume the
Lambda costs effectively nothing.

**What productionising it means**

Refusals are logged with the request id from project 1 and rate-limited per
account — a burst of them from one user is information about intent, better
seen than inferred later. The blocked ranges live as data with a source
comment, not folklore in a regex. And every future URL-shaped feature —
webhooks, imports, avatars — goes through the same client or does not ship.

**The learning**

"Validated" is a statement about a moment, and the connection happens after
it: safety binds to what the code does, not what it once checked. The other
half is that position is privilege — the same GET is harmless from your laptop
and a live wire from inside your network, and your server lives inside.

**How you would know it is wrong**

- The canary listener records a connection for an address the fetcher claims it refused.
- A public URL redirecting to an internal address is followed instead of refused at the hop.
- A hostname that looks public but resolves to a private address — a hosts-file entry reproduces this locally — gets through.
- With the guard removed on a branch, any refusal test stays green.

---

### 4. The API that does not break its callers

*You end up able to change P1's API underneath a frontend you are not allowed
to touch — with a dated, tested path to removing what you replaced.*

**Build**

Yesterday's client, recorded and turned into a compatibility test. One real
change made additively — the new shape beside the old. The old shape marked
with `Deprecation` and `Sunset` headers and a real date, and a log query that
says who still uses it.

**The thought process**

Decide what breaking means before touching anything. Not "the schema changed"
— "a promise changed": a field removed or renamed, a type tightened, a meaning
shifted, required become optional. Then the honest third column, ambiguous:
field order, an enum value nobody has seen. Callers depend on everything
observable, promised or not, and the ambiguous column is where incidents are
born.

The additive rule and its price: you may add; you may not remove or repurpose.
So wrong turns accumulate forever unless retirement is a process — announce,
measure, remove — and only the measuring makes the date honest. Version only
when additive fails, when the shape itself was the mistake, and version in the
path: `/v2/` shows up in logs, curls and screenshots. Header versioning is
tidier and invisible, and invisible is the wrong property while you are
learning to debug.

There are standard words for retirement: `Deprecation` (RFC 9745, published
March 2025) announces it, `Sunset` (RFC 8594) names the date after which it
may stop answering, and the sunset must not be earlier than the deprecation
(checked 2026-09-22). Machine-readable retirement reaches callers a changelog
never will.

**How to organise the prompts**

**1. The promises, then the classification.**

```
Read the API and its callers. Write down every promise a caller could
currently rely on: fields, types, optionality, meanings, status codes,
orderings. Then sort possible changes into three lists — safe to make
silently, breaking, and ambiguous — with one line of why per entry.
```

Argue with the ambiguous list before moving on. It is the whole lesson wearing
a table.

**2. The additive change, guarded by yesterday.**

```
Tags need to become structured objects instead of bare strings. Do it
additively: new field beside the old, both written on every change, old
callers unaffected. Before changing anything, record today's real
responses and turn them into a test that yesterday's client still
passes.
```

The recorded-yesterday test must be green before and after. That pair of runs
is the deliverable.

**3. The retirement, dated and enforced.**

```
Mark the old field's endpoints with Deprecation and Sunset headers,
sunset ninety days out. Add a log query that counts callers still
reading the old field. Then make the compatibility test enforce the
calendar: before the sunset date, removing the old field is a failure;
after it, it is allowed.
```

Check with `curl -i` that both headers arrive with a real date, and that the
usage query returns a number rather than a shrug.

**On AWS**

This is where **API Gateway** earns its keep over an **ALB**: stages and
base-path mappings make `/v1` and `/v2` separately deployed, separately
measured things, per-stage **CloudWatch** metrics answer "is anyone still on
v1" without instrumenting a line, and canary settings shift a percentage of a
stage to new code first. An ALB can route paths to target groups, but the
bookkeeping — per-version metrics, the gradual shift, the mapping — is yours
to build. Pin `/v1` to a **Lambda** alias so the retired surface is served by
code that no longer changes. None of this costs meaningful money at P1
traffic.

**What productionising it means**

The sunset date gets an owner and a calendar entry, because a date nobody owns
is a wish. Removal day is a deploy with a decided behaviour — a 410 and a
pointer at the new shape, chosen in advance. The second deprecation should be
cheaper than the first; that is what writing the policy down buys. The date
opens the conversation; the caller count closes it, at zero.

**The learning**

An API is a promise with an audience. You can widen it silently; narrowing it
needs consent and a calendar. Compatibility is not refusing to change — it is
changing in a fixed order: add, migrate, measure, and only then remove.

**How you would know it is wrong**

- Replaying yesterday's recorded traffic fails against today's API.
- Deleting the old field on a branch leaves the compatibility test green — a guard that cannot fail.
- `curl -i` shows a Sunset earlier than the Deprecation, or no date at all.
- A brand-new optional field trips an alarm — a guard that blocks safe changes teaches people to route around it.

---

### 5. The job that survives a restart

*You end up with the title fetch off the request path, and a worker you can
kill mid-job without losing the work or doing it twice where it shows.*

**Build**

A jobs table in the database P1 already has — pending, claimed with an expiry,
done, failed with a reason — and a worker loop that claims atomically and runs
the guarded fetch inside the budget. The add-URL endpoint returns at once with
the title pending. At-least-once delivery, idempotent handling.

**The thought process**

Start with what the user gets now. The request has to end on time — project 2
— so the honest answer is the saved item with its title pending. P1's decision
list called this the honest version of a queue; note the response gains a
status field, an additive change under project 4's rules.

Then the guarantee arithmetic. The worker does three things — claim, work,
record. A crash between work and record repeats the work; a crash between
claim and work strands the claim unless claims expire. Exactly-once is off the
menu once `kill -9` is in the room; what remains is at-least-once with work
that converges — writing the same title twice leaves the same row, so the
repeat is invisible where it matters.

The claim itself is the section's lost update wearing overalls: two workers,
one job, and read-then-write hands it to both. It must be one atomic statement
— update where still pending, returning the row — never a select followed by
an update. And failure is a state, not an exception: attempts counted, capped,
ending in failed with the reason stored where a person can see it. A fetch
that can never succeed must end somewhere visible, not loop forever, and not
vanish.

**How to organise the prompts**

**1. The design, and the crash map.**

```
Move the title fetch out of the request. Design first, no code: the jobs
table with its states, the exact atomic statement by which one of two
competing workers claims a job, how a claim expires if its worker dies,
and a list of every moment where a crash loses work or repeats it.
```

If the crash list does not include "after the fetch, before recording it," the
design has not understood the problem. No code yet.

**2. The worker, counted honestly.**

```
Implement it: the endpoint saves the item and the job and returns the
title as pending. The worker claims with the atomic statement, claims
expire after 60 seconds, and three failed attempts end in a failed state
with the reason on the item. Run two workers against ten jobs and show,
from the tables alone, that each job was claimed exactly once.
```

From the tables, not the logs' general mood — a count of claims is a number
that can be wrong.

**3. The two deaths.**

```
Two demonstrations. One: kill -9 the worker mid-fetch, restart it, and
show the job re-claimed after the expiry and finished. Two: crash
between the fetch finishing and the outcome being recorded, and show the
fetch running twice while the item still ends correct. Save both stories
with their job ids.
```

The second demonstration is at-least-once seen with your own eyes: the
duplicate happens and does not matter. That is the design working, not
failing.

**On AWS**

**SQS** is this project as a managed service, and everything you built has a
name there: the claim expiry is the visibility timeout — 30 seconds by
default, extendable to 12 hours (checked 2026-09-22) — the attempts cap is a
dead-letter queue, and standard queues promise exactly the at-least-once you
designed for (checked 2026-09-22). **EventBridge** is the neighbour that looks
similar and is not: it routes events to many listeners — announcements, not a
work list. **Kinesis** is an ordered, replayable stream for many readers, the
wrong shape for "do this once". For the consumer, **Lambda** triggered from
SQS wires batching, retries and the DLQ with almost no code, under a
15-minute ceiling per invocation (checked 2026-09-22) — vast for a title
fetch; a **Fargate** worker is for jobs that outgrow it. Keeping the table
version instead: the claim is `SKIP LOCKED` on **RDS** Postgres, a conditional
write on **DynamoDB** — the same idea in two spellings. At P1 volume, all of
it is effectively free.

**What productionising it means**

The alarms are depth and age, not errors: a dead worker emits no errors at
all, and its silence photographs exactly like health, so alarm when the oldest
pending job passes an age you chose. The worker finishes its claim on SIGTERM
instead of dropping it. The attempts cap stands between one poison job and a
worker that dies in a loop, and the failed state needs an owner — a
dead-letter queue nobody reads is a landfill with an SLA.

**The learning**

Exactly-once is a slogan; at-least-once plus convergent work is what survives
`kill -9`, and you have now watched it survive. The queue was never the hard
part — the state machine and the atomic claim were, and both came from the
database you already had.

**How you would know it is wrong**

- `kill -9` mid-fetch: the job completes within claim expiry plus one poll, measured.
- Two workers, ten jobs: the table shows exactly ten claims.
- A poison job: three attempts, a failed state with the reason, a worker still alive.
- Stop the worker for an hour: the age check goes red. If nothing notices, silence means nothing.
- Kill the database mid-claim: the worker survives and resumes when it returns.
