# Find the bottleneck and measure cost per useful operation

[Curriculum](../../README.md) · [Capacity, performance and cost](README.md)

> Project connection · feeds [Reading-list stage 3: measure the application under load](../../../projects/reading-list/stages/03-under-load/README.md)

## The page that remains slow after an optimization

A user opens a reading-list page containing 40 bookmarks. The API first loads the list, then issues another database lookup for each bookmark’s author. The page waits for the combined result. This repeated lookup pattern is often called **N+1**: one list query plus N related queries.

An engineer speeds up a formatting helper, but users barely notice. Your task is to account for elapsed time before choosing the next change, then compare that change under the same data size and offered load. A faster helper and a faster page are different results.

### Recognize the work in code

The following pseudocode illustrates the problem. It is not a claim that the supplied editor performs these queries.

```python
bookmarks = load_page(group_id, limit=40)
for bookmark in bookmarks:
    bookmark.author = load_author(bookmark.author_id)
return bookmarks
```

A bounded batch can fetch the distinct authors needed by this page. It must still restrict access, handle missing authors, and preserve the page’s order. Replacing 40 calls with one call over the entire database would introduce a different resource problem.

Use the [deployment headroom case](cases/deployment-headroom.md) for a worked capacity example, or measure a request in the [local bookmark editor](../../02-applications/03-frontend/labs/bookmark-editor/README.md). Local timing is local evidence. A cloud cost claim additionally needs the billed units and allocated idle capacity.

## Attribute the time before choosing a change


> “A list endpoint takes 900 ms. An engineer made one helper four times faster,
> but the endpoint barely improved. Show me the measurements you want before
> proposing the next optimization.”

Performance work starts with attribution: which operation accounts for elapsed
time, resource consumption, and user-visible delay under the actual workload?

| Sequential teaching request | Before | After helper optimization |
|---|---:|---:|
| Helper | 40 ms | 10 ms |
| Repeated database lookups | 800 ms | 800 ms |
| Remaining work | 60 ms | 60 ms |
| Total | 900 ms | 870 ms |

The endpoint improves by about 3.3%, not fourfold. **Ask first:** are these
operations sequential, and which percentile and workload produced the numbers?

```mermaid
flowchart TD
  Page[Page of 40 items] --> Loop[Per-item lookup loop]
  Loop --> Q1[Lookup item 1]
  Loop --> Q2[Lookup item 2]
  Loop --> Q40[Lookup item 40]
  Q1 --> DB[(Same database)]
  Q2 --> DB
  Q40 --> DB
```

## Choose an optimization you can evaluate

1. Capture a trace or profile and query count under representative data sizes.
2. Identify repeated work: fetch related records in a bounded batch rather than
   issuing one query per item, while preserving ownership and output order.
3. Compare before and after on the same workload. Report latency distribution,
   CPU, queries, transferred bytes, and errors, not only a microbenchmark.
4. Attribute cost per useful operation. Fewer CPU seconds may not reduce a bill
   dominated by idle capacity, storage, or data transfer.

**Follow-up:** “The page can now contain 100,000 items.” A single unbounded batch
is not the fix; add pagination and bounded batch size, then remeasure.

```mermaid
flowchart TD
  Request[Stable page cursor] --> API[Page size cap]
  API --> Batch[Bounded related-record query]
  Batch --> DB[(Owner and cursor index)]
  DB --> Assemble[Preserve requested order]
  Assemble --> Page[Bounded response plus next cursor]
```

Senior depth explains the bottleneck and verifies the result. Lead depth includes
capacity forecasts, workload isolation, budgets, and the ongoing cost of the
optimization itself.

## The principle behind the design

Performance and cost are the same skill pointed at different units. Both are
found by measuring where the time or the money actually goes, and both are lost
by optimising what you assumed. The hard part is not making things faster. It is
finding out what is slow, which is almost never what you think.

## Follow the failure through the system

An engineer spends three days making a function four times faster. It was
already 0.4% of the request. Nothing measurable changes, and the change ships
with a paragraph about the improvement.

Meanwhile the actual cost is a query in a loop — the same lookup, once per item,
ninety times per page — and nobody found it because nobody profiled, because
everybody already knew where the slow part was.

The cost version is quieter and more expensive. A bill goes from four hundred
dollars a month to two thousand over a quarter and nobody can say which change
did it, because cost was never attributed to anything. By the time somebody
cares it is archaeology, and the usual response is to turn off the thing that
*looks* expensive rather than the thing that *is*.

## Mechanisms and their limits

Three things, and the first is the whole section.

**Averages lie, and they lie in the direction of comfort.**

![A latency distribution where the average sits comfortably inside the target while the tail does not, with the p99 marked far to the right and a note that one in a hundred requests is a real person](../../../assets/diagrams/average-hides-it.svg)

An average latency of 180 ms can hide a long tail. Suppose a defined slow event
occurs on 1% of calls. For **20 independent calls**, the probability of at least
one slow call is `1 - 0.99**20 ≈ 18.2%`. If every call shares exactly the same
slow event, perfect correlation makes that probability **1%**, not 18.2%.
A p99 is a distribution boundary, not a claim that exactly 1% take four seconds.
Measure page-level elapsed time and dependency correlation rather than inferring
them from marginal percentiles.

Report distributions alongside counts and error rates. p50 describes a median and p99 a tail boundary. Small sample sizes make extreme percentiles unstable. Averages remain useful for capacity arithmetic, but do not explain the tail on their own.

**Identify what the profiler sampled.** A CPU flame graph attributes sampled
CPU activity; an allocation profile attributes allocations. Neither is
automatically elapsed request time. Use a trace/waterfall for the critical path,
including queue, lock and network waits. Concurrent span durations cannot simply
be added to obtain end-to-end latency.

| Change, same useful workload | Measured result | What follows |
|---|---|---|
| 10 ms helper becomes 5 ms in a 1,000 ms serial endpoint | Endpoint becomes 995 ms | Helper is 2× faster; endpoint improves only 0.5% |
| CPU usage halves on an unchanged fixed-size reserved instance | Same instance-hours billed | More headroom, not an automatic 50% bill reduction |
| Retries double while successful jobs stay constant | More requests/CPU/network per useful job | Report cost including failed attempts, not cost per attempt alone |

**Cost needs billing data.** Attribute compute time/capacity, requests, storage,
I/O, network and allocated idle cost to useful requests or completed jobs. Name
the actual billed unit and what was measured versus estimated. Compare matched
workloads, percentiles and error rates before claiming a cheaper release.

### Continuous profiling and repeatable comparisons

Differential flame graphs compare two profiles; they do not depend on eBPF and
were not invented by modern production profiling. Choose a collection method
for workload coverage, overhead, deployment constraints and symbolization.
Record profiler/configuration and workload identity, then compare equivalent
profiles across versions. Measure CPU, latency, dropped samples and storage
before accepting an always-on budget.

### Attribution is the whole cost discipline

You cannot manage a number you cannot break apart. The engineering work is
tagging — by service, by environment, by team, by feature — so that "the bill
went up" becomes "the bill went up because of this". The FinOps community has a
standard data format for this (FOCUS) so that the same analysis works across
providers.

The question to be able to answer is the **unit cost**: what does one request,
one user, one job cost? Almost nobody can answer it, and the teams that can make
different decisions.



## What good looks like

- You quote percentiles, not averages, and you know your p50/p99 gap.
- You profiled before you optimised, and you can show the profile.
- After the change you measured the *same percentile* again and the number moved.
- Cost is attributed: you can say which service or feature owns a line on the bill.
- You know the unit cost of the main thing your system does.
- Some optimisation was rejected because the measurement said it did not matter.

Done badly:

- "It feels slow" as a diagnosis, followed by a rewrite.
- Optimising the thing that was easy to measure rather than the thing that hurt.
- A benchmark on your laptop, standing in for production.
- An average on the dashboard and no percentiles anywhere.
- Cost discovered monthly, by whoever opens the invoice.
- A performance fix with no before-and-after at the same percentile, which is indistinguishable from no fix at all.

## Use an assistant to investigate specific questions

**Request 1 — read the profile, do not theorise about the code**

```
Here is a profile (or a flame graph export). Tell me where the time
actually goes, ranked, as percentages of total.

Do not suggest optimisations yet, and do not reason from what the code
looks like — only from what the profile says. If the profile is
dominated by waiting rather than computing, say so and say what it is
waiting on.
```

*Why it is asked that way:* a model handed code will generate plausible
optimisations all day, and they will be about algorithms because that is what
code looks like. Forbidding it from reasoning about the source forces the answer
to come from the measurement, which is the only place it can honestly come from.

*What you should get back:* a ranked list, usually topped by something dull — a
database call, serialisation, a lock. If the top item is under 5% of total, you
do not have a hot spot, you have a distributed cost, and that is a different and
harder problem worth knowing about.

**Request 2 — make the before-and-after honest**

```
I am about to change <X> for performance.

Write the measurement I should take before: which percentile, over what
window, under what load, and what number I should record.

Then tell me what result would mean the change did nothing, and what
result would mean it made things worse in a way this measurement would
hide.
```

*Why:* the last clause is the one that matters. Optimisations frequently improve
p50 and worsen p99 — a cache does this routinely, because a miss now costs the
lookup plus the cache round trip. A measurement that only watches the average
will call that a win.

**Request 3 — the unit cost**

```
Here is my architecture and my bill. Work out the cost of one <request /
user / job>, showing the arithmetic, and tell me which component
dominates it.

Then tell me which parts of that number you had to guess, and what I
would have to measure to replace the guesses.
```

*Why:* the second half is the whole value. A unit-cost estimate with the guesses
marked is useful. One without them is a number that will be quoted in a meeting
for a year.

**What to keep for yourself:** whether it is worth doing. A measurable
improvement to something nobody notices is still a waste, and the cheapest
performance work remains deleting a feature — with not building one a close
second.

## How you would know it is wrong

1. **Measure the same percentile before and after.** A p50 improvement quoted against a p99 baseline is not a comparison. This is the commonest way a performance claim turns out to be empty.
2. **Check the optimisation applied at all.** Assert the new code path actually ran — a flag not set, a cache not warmed, a config not deployed all produce "no change", and so does a change that did nothing.
3. **Look at the p99, specifically, after a caching change.** If it got worse, you moved cost from the typical case to the unlucky one.
4. **Use evidence from a representative environment.** Production profiles can reveal real workload behavior. Controlled local profiles are useful for hypotheses, but account for data volume, cache state, contention, and network differences.
5. **Compute the unit cost and ask somebody else on the team for theirs.** If nobody can produce one, cost is unattributed, whatever the tagging policy says.
6. **Turn the profiler on and measure its own overhead** on your workload. The published figure is somebody else's workload.
7. **Ask what you rejected.** If every optimisation you ever measured turned out to be worth doing, you are only measuring the ones you already believed in.

## Apply this lesson to the reading-list application

On **P3**, after the load test:

- Profile the system *under load*, not idle, and record where the time goes as percentages.
- Write down your p50 and p99 before touching anything.
- Make exactly one change, chosen from the profile rather than from intuition.
- Re-measure both percentiles under the same load, and record both numbers.
- Compute the unit cost of one link-fetch: compute, storage, and the outbound request. Mark every figure you had to guess.
- Find one thing the profile says is expensive that you decided **not** to fix, and write down why.

**Acceptance criteria:**

- You have four numbers: p50 and p99, before and after, measured the same way.
- The change you made is the one the profile pointed at, and you can show the profile.
- The unit cost has its guesses marked.
- The rejected optimisation is written down with its reason. If none was rejected, state the alternatives considered and the evidence available rather than inventing a rejection.

## Terms used in this lesson

- **percentile** — the value below which that share of requests fall. p99 is a boundary in a measured sample or distribution, not an identity assigned to one person.
- **tail latency** — the slow end of the distribution. Where the people who leave live.
- **flame graph** — a profile whose width represents its sampled quantity
  (for example CPU samples or allocated bytes); read the profiler and units first.
- **diff flame graph** — two profiles compared, so you see what a release changed rather than what is slow.
- **continuous profiling** — always-on sampling in production, cheap enough to leave running.
- **N+1** — one query to get a list, then one per item. A repeated-access pattern that can add avoidable calls.
- **attribution** — knowing which service, team or feature owns a line on the bill.
- **unit cost** — what one request, user or job costs. The number that makes cost decidable.
- **coordinated omission** — a load generator that waits for slow responses and so never sends the requests that would have been slowest, quietly under-reporting your tail.

---

**Not covered here:** the measurement plumbing — metrics, traces, cardinality
and what telemetry itself costs — is [Use logs, metrics and traces to explain one slow request](../../03-production/04-observability/logs-metrics-traces.md).
This section is what you do with the numbers once you can see them. Micro-
benchmarking individual functions is deliberately absent: it is a specialist
skill and, for this whole-system question, almost always the wrong instrument for the question.

[Learning sequence](../../README.md) · [Independent practice](../../../practice/interview-guide.md)

## Draw it from memory · Measure the whole critical path

```mermaid
flowchart TD
  Browser["Browser: network + render"] --> API["API: CPU + queue wait"]
  API --> A["Independent dependency A"]
  API --> B["Independent dependency B"]
  A --> Join["Wait for required results"]
  B --> Join
  Join --> Reply["Serialize + transfer"]
  Reply --> Browser
  API --> Profile["Profile time and resource use"]
  Profile --> Change["One measured change"]
  Change --> Compare["Same workload comparison"]
```

**Redraw challenge:** Identify which calls can overlap. Which resource grows when you increase fan-out?

![Measure the whole critical path: mechanism in motion](../../../assets/learning/io-waterfall.svg)

[Static view](../../../assets/learning/io-waterfall-still.svg)
