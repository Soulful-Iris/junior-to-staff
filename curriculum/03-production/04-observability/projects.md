# Practice request tracing, diagnosis, metric budgets and sampling

[Chapter](README.md)

A reading-list save accepts a URL and may schedule title lookup. Support needs to understand one affected request, while operations needs to detect a growing backlog across all users. These exercises connect detailed event evidence with population measurements without treating either as complete by default.

## Choose your starting code

Use [the tracing project](../../02-applications/01-backend/projects/01-the-request-you-can-trace-end-to-end.md) for the concrete application and supplied starting code. Read [logs, metrics and traces](logs-metrics-traces.md) before adding collection infrastructure.

![Adding unbounded label values can multiply metric series](../../../assets/diagrams/cardinality-explosion.svg)

<a id="1-one-requests-story-across-the-queue"></a>

## 1. Follow a saved bookmark into a queued title lookup

The HTTP response finishes before the worker starts. Request-local memory is no longer available to establish why the job exists.

**Your task.** Persist job identity and originating request identity with durable acceptance. Carry permitted trace context through publication and consumption. Give each retry its own attempt identity linked to the same logical job.

**What to observe.** From the save response ID, find the accepted job, its attempts, and final result. A batch containing unrelated producers does not invent one common request parent.

**Changed requirement.** The outbox relay republishes after losing its acknowledgment. Preserve event identity so a duplicate delivery does not create a second logical job.

[Worked mechanism and implementation context](../../02-applications/01-backend/projects/01-the-request-you-can-trace-end-to-end.md)

<a id="2-the-fire-drill"></a>

## 2. Diagnose an unknown failure from existing evidence

A save slows down, but the symptom could be a pool wait, a slow query, or an unavailable title provider.

**Your task.** Choose one controlled fault in a local environment. Use recorded spans, counters, and structured events to distinguish it from the other explanations. Keep observations and hypotheses separate, then repeat after improving one missing signal.

**What to observe.** The explanation identifies the affected user operation and measured delay. A guessed diagnosis or process health badge is insufficient.

**Changed requirement.** The log destination fails during the incident. Bound diagnostic buffering, count loss through an independent path, and preserve the application’s stated failure policy.

[Worked mechanism and implementation context](problems/slow-request.md)

<a id="3-the-cardinality-budget"></a>

## 3. Budget metric dimensions using observed combinations

The service emits request metrics by method, route template, and status class. Adding raw user IDs can create many more series without adding useful aggregate comparisons.

**Your task.** Inventory dimensions, potential combinations, and actually active combinations over a named window. Compare that inventory with the backend’s retention and billing model. Put permitted diagnostic IDs in the appropriate event or trace record instead.

**What to observe.** Four methods × twenty routes × five status classes has a 400-combination upper bound. It does not prove that all 400 are active.

**Changed requirement.** A tenant-specific requirement needs diagnosis of a rare failure. Compare targeted traces, bounded top groups, and queryable events instead of adding every tenant to every metric.

[Worked mechanism and implementation context](problems/metrics-platform.md)

<a id="4-tail-sampling-that-survives-a-second-collector"></a>

## 4. Preserve trace affinity when adding tail samplers

One collector can buffer a trace’s spans locally. Randomly sending those spans to three collectors can fragment the evidence each sampler sees.

**Your task.** Draw a routing layer keyed by trace identity and a bounded sampling layer. State the wait window, capacity policy, late-span behavior, and restart loss. Compute request rates independently of biased sampled survivors.

**What to observe.** A chosen trace’s spans reach the same sampling owner within the stated routing conditions. Observed loss and incomplete traces remain visible.

**Changed requirement.** A sampler is removed while traces are buffered. Explain ownership change and accepted loss or draining behavior rather than treating a new instance as shared memory.

[Worked mechanism and implementation context](logs-metrics-traces.md)

<a id="5-the-one-user-whose-week-was-broken"></a>

## 5. Investigate one affected member without exposing private URLs

A member reports a week of failed saves, while the aggregate error ratio is small. The useful question is which operation class failed for that permitted diagnostic identity.

**Your task.** Use synthetic or appropriately permitted events to search the request path, compare versions and outcomes, and estimate the affected population. State retention and sampling gaps. Avoid placing full private URLs in logs to make correlation easier.

**What to observe.** The result names supported observations and remaining unknowns. Missing sampled events do not establish that no failure happened.

**Changed requirement.** The requested week falls outside retention. Explain the evidence limit and a future collection change without inventing a historical root cause.

[Worked mechanism and implementation context](projects/debuggable-at-three-in-the-morning.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
