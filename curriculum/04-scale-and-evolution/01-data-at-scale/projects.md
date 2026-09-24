# Practice cache protection, durable handoff and replica recovery

[Chapter](README.md)

The reading-list application now receives enough concurrent traffic to expose shared resource limits. Its cache, background queue, and replicas each change a different contract. These exercises make those consequences measurable before you add more infrastructure.

## Choose your starting code

Start with [the scaling lesson](scaling-data.md) and [the local cache models](labs/cache-consistency/README.md). The models expose exact schedules. A real database pool, queue adapter, or replica topology is additional implementation work unless a linked deployment lab supplies it.

![Concurrent requests share one in-flight load within the stated coordination boundary](../../../assets/learning/cache-coalescing.svg)

<a id="1-what-saturates-first"></a>

## 1. Find the first saturated resource

The group page slows, then unrelated sign-in requests begin waiting. A shared connection pool is one hypothesis, but CPU, locks, and I/O can produce related symptoms.

**Your task.** Measure arrivals, useful completions, acquisition waits, query time, and resource saturation on a bounded workload. Choose an intervention only after the evidence identifies a constraint. A pooler is useful for some connection problems, not every slow query.

**What to observe.** Your record links the observed limit to the change. It names what happens when a new operation cannot acquire capacity before its deadline.

**Changed requirement.** Add ten API replicas. Recalculate total downstream connections and query load rather than only counting new CPU capacity.

[Worked mechanism and implementation context](scaling-data.md)

<a id="2-the-stampede-you-cause-on-purpose"></a>

## 2. Count reloads when one hot key expires

Two hundred readers request the same missing cached list. Independent loaders issue two hundred queries even though they need the same result.

**Your task.** Run the supplied baseline and shared-flight model. Trace who creates the load, who waits, and who removes the in-flight entry on failure. Define whether canceling one waiter cancels shared work.

**What to observe.** One successful local shared load serves overlapping local waiters. Ten independent process maps can still produce ten loads.

**Changed requirement.** The cache is entirely unavailable. Add a fleet-scoped admission budget and explicit stale or unavailable response policy.

[Worked mechanism and implementation context](labs/cache-consistency/README.md)

<a id="3-at-least-once-at-both-ends"></a>

## 3. Commit business intent and tolerate duplicate delivery

Saving a bookmark and then separately publishing its title job leaves a crash gap between the two operations.

**Your task.** Place the saved row and outgoing intent in one transaction, relay it, and make the consumer’s protected effect idempotent. Trace crashes before and after each acknowledgment. The relay can still publish more than once.

**What to observe.** A committed save has durable job intent. Repeated delivery does not create a second protected result, while a changed payload under the same operation ID is rejected.

**Changed requirement.** The consumer now calls an external provider. Add provider-supported idempotency or uncertain-outcome reconciliation because the local database constraint does not cover that effect.

[Worked mechanism and implementation context](../../03-production/03-infrastructure/aws/labs/job-pipeline/README.md)

<a id="4-reading-from-a-replica-without-lying-to-the-user"></a>

## 4. Preserve a user’s new write while replicas lag

Ana saves version 8 and immediately reloads. A replica still has version 7, so a successful read can appear to undo her edit.

**Your task.** Use the local lag fixture to reproduce the regression. Compare an authoritative read with a session watermark and deadline fallback. State which other readers may accept stale data.

**What to observe.** A strict read returns version 8 or an explicit unavailable result. A fixed five-second primary pin is not sufficient if lag lasts ten seconds.

**Changed requirement.** The primary fails before version 8 reaches the survivor. State possible data loss separately from read routing.

[Worked mechanism and implementation context](labs/cache-consistency/README.md)

<a id="5-the-failover-rehearsed-and-what-it-cost"></a>

## 5. Measure failover from the application’s perspective

A standby becoming writable is only one recovery milestone. Clients need the new route, usable credentials, compatible schema, and enough capacity to serve again.

**Your task.** Record accepted write IDs before a controlled failure in a disposable setup. Recover, issue user operations, and compare durable rows with those acknowledgments. Measure the interval and any missing writes.

**What to observe.** The report distinguishes recovery time from data loss and identifies the replication/acknowledgment policy that allowed it.

**Changed requirement.** Fresh traffic continues during catch-up. Reserve capacity and calculate drain time using completion rate minus new arrival rate.

[Worked mechanism and implementation context](../04-migrations/labs/recovery-migration/regions.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
