# 09 · Reliability

> Senior tier · feeds **P3 (it holds under load)**

## The one-liner

Reliability is not uptime you hope for. It is behaviour you designed for the
moments when part of the system is failing — and part of it is always failing.
The senior version has numbers attached: how much failure you are allowed, what
happens when that allowance runs out, how long each call waits before giving
up, and which requests get dropped first when there is not enough system to go
around.

## The failure it prevents

At 02:10 the database slows down — a backup job, a bad query plan, it barely
matters. Calls that took 20ms now take two seconds. The data layer times out
and retries, three attempts. The service above it times out and retries, three
attempts. So does the edge. One click has become twenty-seven queries, aimed at
a database that was struggling to serve one.

At 02:40 someone finds the backup job and kills it. The database is healthy
again. The outage continues. The load is no longer coming from users — the
system is generating it itself: timeouts breed retries, retries breed load,
load breeds timeouts. The graphs sit flat at 100% with the original cause long
gone. At 04:55 someone disables retries at the edge, and everything recovers in
ninety seconds.

The review will call the database the cause. It was only the trigger. The
outage was designed in months earlier, one locally reasonable retry policy at a
time. This section is about noticing that design before it runs.

## The mental model

Five ideas, and they compose into one: **decide the failure behaviour on a calm
afternoon, because otherwise the system decides it during the incident.**

### A budget you spend, and a policy someone signed

100% is not a target; nobody's network can deliver it and users cannot tell the
last nine from the one before it. So you set an SLO — say, 99.9% of requests
succeed within 500ms, over 30 days. The 0.1% left over is the **error budget**:
about 43 minutes of total downtime a month, yours to spend on deploys,
experiments and bad luck.

The arithmetic is the easy half. What makes a budget real is the **written
error-budget policy**: what changes, and on whose authority, as it burns.
Google publishes its example policy and the shape is worth copying: budget
exhausted over the trailing four weeks means releases freeze — only P0 fixes
and security patches ship — until the service is back inside SLO; a single
incident that burns more than 20% of the budget forces a postmortem with a P0
action; disputes escalate to a named executive. Notice what this is: an
agreement between product and engineering, negotiated before anyone is angry. A
budget with no freeze rule attached is a dashboard.

Alert on the budget's **burn rate**, not on static thresholds. Burn rate 1
spends the budget exactly by the window's end; 14.4 empties it in about two
days. The SRE Workbook's starting point: page when the last hour burned at
14.4× (2% of the budget in an hour), page at 6× over six hours, ticket at 1×
over three days — each paired with a short confirmation window about one
twelfth as long, so the alert also *stops* soon after the bleeding does. Static
thresholds fail both ways: they page on blips that never threatened the SLO,
and in the Workbook's own worked example a static rule misses a 35× burn that
empties the month's budget in under a day.

### Every call has a timeout, and you chose it or you inherited it

Every network call has a timeout. If you never set one, you are running on the
library's default, and defaults range from thirty seconds to forever. Either
way it is a decision; the question is whose. The Builders' Library method:
take the dependency's real latency distribution, pick the false-timeout rate
you can accept, and set the timeout near that percentile — if cutting off one
good call in a thousand is acceptable, sit near the p99.9. Too long, and a slow
dependency holds your threads and connections hostage while work queues behind
them. Too short, and you kill work that would have succeeded — and then, worse,
retry it.

### Retries are multiplication

A retry is extra load, added at the exact moment the system just said it has
too much. One layer retrying is a tool. Several layers retrying is a weapon
pointed inward:

![One user click becomes 27 database calls when each of three layers retries three times: one call fans out to three, then nine, then twenty-seven at the already-slow database](../../../assets/diagrams/retry-amplification.svg)

Nobody writes 27 into a config. Three teams each write 3. So the first rule is
structural: **retry at one layer only**, and know which. The Builders' Library
runs the same arithmetic on a deeper stack: three retries per layer, five
layers, load on the bottom multiplied by up to 243.

Cap even that one layer. The classic guard is the circuit breaker — trip open
after repeated failures, fail fast, probe for recovery. AWS's stated preference
is **token-bucket retry limiting** instead: successes drip tokens into a
bucket, each retry spends one, and an empty bucket means fail fast until real
successes refill it (their SDKs have shipped this since 2016). Their case
against breakers: a breaker adds *modal* behaviour — a second mode the system
can be in, hard to test and therefore usually untested — and an open breaker
keeps rejecting after the dependency has already recovered, stretching the
outage. A token bucket degrades continuously instead of flipping state.
Breakers are not wrong everywhere — they are standard in plenty of stacks — but
if you deploy one, you own testing its open, closed and half-open modes, and
most teams never do.

Two smaller rules with large blast radii. **Never blind-retry a 4xx**: the
request was rejected, not lost, and identical bytes will be rejected
identically (429 is the exception, and it arrives with its own instruction:
wait). And **jitter every timer** — backoff, cron schedules, cache TTLs, health
checks — because anything synchronised arrives as a spike; the AWS guidance is
jitter on all timers, periodic jobs and deferred work, not just retries.

And the precondition for all of it: **only retry a side effect if doing it
twice equals doing it once.** The mechanism is the **idempotency key**: the
client mints a unique key per logical operation and sends it with every
attempt; the server remembers key → result and replays the stored result on a
duplicate. Without it, a retry is not "try again" — it is "maybe charge them
twice".

### Degradation is a mode you design

When there genuinely is not enough system, the remaining question is who gets
served. Netflix's engineering write-ups describe classifying requests by how
much a user would notice — pressing play is CRITICAL, speculative prefetch is
BULK — and shedding the lowest class first as CPU crosses per-class thresholds
(in their example configuration, non-critical shedding starts at 60% CPU,
critical only at 80%). The result they report from a real event: prefetch
traffic returned from an outage at twelve times the normal rate; prefetch
availability was allowed to fall to 20% while user-initiated requests stayed
above 99.4%, with more than half of all requests being throttled. Users did
not notice, and that is the point: **the system chose what to drop before the
incident could choose for it.** They validate the thresholds with continuous
chaos load tests rather than trusting the config. Your version needs two
classes and one threshold, not their machinery. "Whatever times out first" is
not a degradation mode; it is a lottery.

### The failure that outlives its cause

The opening story has a name: **metastable failure**, defined in a 2021 paper
by Bronson, Aghayev, Charapko and Zhu. A system is *stable* while it absorbs
shocks, *vulnerable* when it runs fine but has lost that headroom, and
*metastable* when a **trigger** — a load spike, a slow disk — tips it into a
failure that a **sustaining loop** keeps alive after the trigger is gone.
Retries are the canonical loop. Cold caches are the sneaky one: a restart or
flush turns every cheap hit into an expensive miss, so capacity is lowest at
the moment load is highest. The defining property is that waiting does not
help — the failed state is self-sustaining, which is what "metastable" means.
Recovery takes deliberate loop-breaking: shed load, switch retries off, restart
with intake throttled.

Read everything above as loop prevention. Single-layer token-bucket retries cap
the multiplication. Timeouts release held resources. Shedding cuts the loop's
fuel. The budget is how you notice you have drifted from stable to vulnerable
before a trigger finds you.

*(Positions and numbers checked against the Google SRE Workbook, the AWS
Builders' Library, the metastability paper and Netflix's engineering material
on 2026-09-21.)*

## What good looks like

- Every outbound call has an explicit timeout, and a sentence somewhere says why that value.
- An SLO someone outside engineering agreed to, and a one-page error-budget policy with named actions and named authority.
- Alerts are burn rates over paired long and short windows, and the last page corresponded to real user harm.
- Retries exist at exactly one layer, budgeted and jittered; every other layer fails fast upward.
- Every retried side effect carries an idempotency key, and a test submits a duplicate.
- A written shed order: which request classes drop first, at what signal, and what the caller sees instead.
- The team has watched the system recover from a killed dependency with nobody touching it.

Done badly, you see:

- "We target 99.99%" and nobody can say what happens when it is missed. (What happens is a meeting.)
- Timeouts are whatever the libraries shipped, and someone discovers mid-incident that one default is infinite.
- Retries configured in the HTTP client, the mesh and the application, by three people who have never met.
- A circuit breaker in production whose open state has never once been exercised.
- "Degradation" meaning pods restart and requests fail at random.
- Postmortems that stop at the trigger ("the database was slow") and never name the loop that kept the system down for three more hours.

## Ask Claude for this

**Request 1 — the policy, not the maths**

```
Our SLO: 99.9% of requests succeed in under 500ms, over a rolling 30 days.

Write the one-page error-budget policy that goes with it. It must name:
tiered actions as the budget burns (at 50% consumed, at 100%, and for any
single incident that burns 20% on its own), who has the authority to
declare a release freeze and who can lift it, what may still ship during
a freeze, and where a disagreement escalates.

Then define the alerting as burn rates: one paging alert on a fast burn,
one ticket on a slow burn, each with a paired long and short window.
Show the arithmetic from the SLO to every threshold.

Do not propose loosening the SLO.
```

*Why it is asked that way:* everyone asks for the SLO maths; behaviour is
changed by the policy — the freeze, the names, the exceptions — which is
exactly the part teams skip. The last line matters because loosening the target
is the easiest way to make the policy painless, and a painless policy is not
one.

*What you should get back:* thresholds paired with actions a person could
refuse to perform — that is the test of an action — and burn-rate arithmetic
you can recompute: for this SLO, 2% of budget in an hour is a burn rate of
14.4. If the numbers do not recompute, they were pattern-matched.

*Push back on:* actions that are sentiments. "The team should prioritise
reliability" freezes nothing. Every tier needs a change someone can point at:
this ships, this does not.

**Request 2 — the outbound-call audit**

```
Here is the codebase. Find every place it makes a network call — HTTP,
database, cache, queue.

For each call site, one row: where it is, what it calls, the timeout and
WHERE that timeout comes from (our code, or a library default — name the
default's actual value), everything that retries it (our code, the client
library, a mesh or proxy — count the layers), and whether the operation
is idempotent by nature, idempotent via a key, or not idempotent.

Do not fix anything. Give me the table, worst rows first.
```

*Why:* "name the default's actual value" is the constraint doing the work. It
forces a look at what the library really does rather than assuming the visible
code is the whole story — and stacked retry layers are precisely what reading
one file never shows.

*What you should get back:* at least one call with no explicit timeout, and at
least one operation retried at two layers. Unaudited systems have both; an
audit that comes back clean should raise your suspicion of the audit, not your
confidence in the system.

*Push back on:* "safe to retry" on any write that does not point at its dedupe
mechanism, and any timeout column that says "default" without a number — that
means it did not check.

**Request 3 — design the shed, then hunt the loop**

```
Same system. Design its degradation mode:

1. Sort every endpoint into classes — CRITICAL (a user loses the core
   function), DEGRADED (worse but working), BEST_EFFORT, BULK
   (machine-initiated, deferrable). Justify any surprising placement.
2. Choose the utilisation signal and a shed threshold per class. State
   exactly what a shed request returns and what its caller does with it.
3. Now run the film backwards: the database is pinned at 100% for five
   minutes, then fully recovers. Trace what every retry policy, cache
   and queue does during and after those five minutes, and tell me
   whether load returns to baseline on its own. If not, name the loop.
```

*Why:* part 3 is the senior question. It demands the sustaining loop by
mechanism — this retry config, this cold cache — which can only be answered
from the actual configuration part 2 has to live with, not from general
optimism about resilience.

*What you should get back:* an uneven classification — most traffic is not
critical, and if everything lands in CRITICAL, nothing is — then either a
concrete loop or a concrete argument that none exists, with the caches and
client-side retry queues accounted for.

*Push back on:* shedding by rejecting at random rather than by class, and any
"it recovers cleanly" that never mentions what the queued retries and cold
caches do in minute six.

## How you would know it is wrong

1. **The kill test.** Stop a dependency for sixty seconds, then restore it.
   Watch load at that dependency. If it does not return to baseline within a
   few minutes with no human action, you have a sustaining loop — a metastable
   system, found on a weekday afternoon instead of at 2am.
2. **Count the amplification.** Slow the database artificially and send exactly
   one request at the top. Count arrivals at the bottom, from the query log.
   The number must match what your single retry layer allows. Twenty-seven
   means hidden layers are retrying — usually a library default and a proxy
   nobody mentioned.
3. **The duplicate test.** Send the same side-effecting request twice with the
   same idempotency key: exactly one effect. Then twice with different keys:
   exactly two. The second half matters — a dedupe that swallows everything is
   broken in the other direction, quietly.
4. **Fire the pager on purpose.** Inject synthetic errors just above the
   fast-burn threshold; a page must arrive. Stop them; the alert must clear
   within the short window. An alert that has never fired is a hypothesis.
5. **Ask when the policy last changed a plan.** If the error budget has ever
   been exhausted and nothing froze, you have arithmetic and a dashboard, not a
   policy.
6. **Shed under load and diff the classes.** Push utilisation past the
   threshold in a load test: BULK availability should crater while CRITICAL
   barely moves. If the two curves droop together, your classes exist in a
   document and nowhere else.

## Your slice of the project

On **P3**, the reading list finally meets load. From this section:

- A one-page SLO and error-budget policy for the core action (add a URL, see
  the list): tiered actions, and your own name in the freeze rule. It binds
  only you; the practice is the point.
- Burn-rate alerts — fast-burn page, slow-burn ticket, each with paired
  windows — plus the drill log showing each has fired once.
- A committed timeout inventory: every outbound call, its value, chosen or
  inherited. No row that says "default" without the number.
- Retries at exactly one layer, token-bucket capped, jittered — and the other
  layers' retry counts explicitly set to zero in config, with a comment saying
  why.
- An idempotency key on adding a URL — your one side-effecting call that talks
  to the outside world — and the duplicate test in the suite.
- Two request classes: user actions are CRITICAL, title fetching is BULK. One
  utilisation threshold that sheds BULK first, and a recorded load test showing
  the two availability curves separating.
- A game day, written up: the fetch target killed for one minute, once with
  retries deliberately stacked at two layers, once with your real config.
  Record what load does *after* the trigger is removed, in both runs. The
  difference between those two graphs is this whole section.

**Acceptance criteria:**

- The kill test passes: trigger removed, baseline restored, no human in the
  loop.
- Disabling the dedupe makes the duplicate test go red.
- You can state the worst-case number of database calls for one user click
  under failure, and the measured amplification matches it.
- The fast-burn page fired in the drill and cleared inside the short window.

## Words you now own

- **SLI** — the measurement: what fraction of requests were good, by a definition you wrote down.
- **SLO** — the target on an SLI over a window. The number you defend, not the number you advertise.
- **error budget** — one minus the SLO: the failure you are allowed. Spent by incidents and by risk-taking alike.
- **error-budget policy** — the written, agreed rules for what happens as the budget burns. The freeze lives here.
- **burn rate** — how fast the budget is being spent relative to exactly-on-plan. Rate 1 spends it by the window's end.
- **retry storm** — retries stacking across layers until the system attacks its own dependency.
- **jitter** — deliberate randomness on timers, so synchronised things stop arriving together.
- **token-bucket retry limiter** — successes earn tokens, retries spend them, empty means fail fast. Degrades smoothly where a breaker flips.
- **circuit breaker** — fails fast after repeated failure, probes for recovery. Modal: test every mode or do not ship it.
- **idempotency key** — a client-minted id for one logical operation, so the server can make twice equal once.
- **load shedding** — refusing chosen work on purpose so the important work survives.
- **metastable failure** — an outage that persists after its cause is fixed, held up by a sustaining loop such as retries or cold caches.

---

**Not covered here:** observability — how you would see any of these numbers
happening — is its own senior section, as are queues and backpressure. Capacity
planning, autoscaling, multi-region failover and incident response as a
practice are deliberately out. Chaos engineering appears here only as a game
day; the discipline is larger. And everything above assumes one region and one
database, because most systems are that, for longer than their diagrams admit.
