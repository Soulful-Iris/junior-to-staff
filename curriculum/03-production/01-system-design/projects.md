# Practice workload estimates, architecture choices and recovery plans

[Chapter](README.md)

Use a bookmark service as the common application: members save URLs and list recent bookmarks. You are preparing a design record another engineer could implement. The exercises build that record in stages, from known behavior to capacity and regional recovery. Teaching inputs and actual measurements must remain distinct.

## Choose your starting code

Start with [the service design lesson](design-method.md) and [the local API](../../../examples/reading-list-starter/README.md). The [bookmark service brief](problems/bookmark-service.md) supplies a complete scenario and proposed AWS view.

![Two candidate designs expose different state and failure boundaries](../../../assets/diagrams/two-designs.svg)

<a id="1-the-constraints-you-measured-instead-of-imagined"></a>

## 1. Build a constraint sheet from evidence and explicit assumptions

A request to “make the list fast” leaves several decisions unstated: whose list, how many rows, how fresh, and under what arrival rate.

**Your task.** Write the read and write contract. Measure local payload size and query behavior where possible. Label hypothetical peak rate, retention, and freshness targets as assumptions. Attach a consequence to each limit.

**What to observe.** At 20 writes/s for one hour, expect 72,000 writes. Do not present a one-hour peak as a continuous annual rate.

**Changed requirement.** One tenant supplies most of the load. Replace a fleet average with per-tenant distribution and the hottest operation.

[Worked mechanism and implementation context](../../01-code/01-problem-solving/estimation-constants.md)

<a id="2-two-shapes-and-the-bill-for-each"></a>

## 2. Compare two architectures that meet the same contract

A title lookup can occur inside the save request or after a durable job is accepted. Both can preserve the bookmark, but their waiting and recovery behavior differ.

**Your task.** Draw both paths using the same inputs. Name what is acknowledged, what persists, and what remains incomplete at response time. Compare latency, worker recovery, storage, and operating effort. Choose with a stated reason.

**What to observe.** The chosen diagram can explain both a successful save and a title dependency timeout. A queue is not credited with finishing work merely because it accepted it.

**Changed requirement.** The product now requires titles within ten seconds. Add completion latency and backlog age to the decision instead of measuring HTTP success alone.

[Worked mechanism and implementation context](../../02-applications/01-backend/projects/05-the-job-that-survives-a-restart.md)

<a id="3-the-failure-interrogation"></a>

## 3. Walk each dependency failure to the user-visible outcome

A database failure, cache outage, and slow title provider affect different portions of the user action.

**Your task.** For each component, record the user response, persisted state, retry owner, and recovery work. Use a local fixture to exercise two important cases. Record whether the observed behavior matches the design.

**What to observe.** A title failure preserves the accepted URL. A database failure must not return a successful save if nothing durable accepted it.

**Changed requirement.** The response is lost after a successful write. Add operation identity and a replay policy rather than interpreting timeout as a failed write.

[Worked mechanism and implementation context](problems/bookmark-service.md)

<a id="4-the-ten-times-question"></a>

## 4. Calculate the first limit under a larger workload

A tenfold increase in reads need not imply ten times as many writes. The bottleneck depends on query shape, cache hits, connections, and skew.

**Your task.** Write an ordered resource budget, then run a bounded local workload and identify the observed limit. Include offered rate, useful completions, waiting, and error counts. Keep the load generator’s own limits visible.

**What to observe.** A queue growing 200 jobs/s adds 12,000 jobs in a minute. Adding a buffer changes the waiting location, not the service rate.

**Changed requirement.** The cache fails at peak. Bound origin admission and explain what excess callers see.

[Worked mechanism and implementation context](../../04-scale-and-evolution/01-data-at-scale/labs/cache-consistency/README.md)

<a id="5-the-region-question"></a>

## 5. Choose a recovery promise and demonstrate its prerequisites

The primary region is unavailable. A backup exists elsewhere, but the application also needs configuration, identity, routing, and restored data to serve.

**Your task.** State tolerable data loss and recovery time, then inventory the needed artifacts. First rehearse restoration in an isolated environment. If extending to AWS, measure the actual cross-region procedure instead of assigning a standard time to a named recovery posture.

**What to observe.** The recovered service returns a known row, and the report names acknowledged writes not present in the recovery copy.

**Changed requirement.** The secondary has version 8 while version 9 was acknowledged in the failed region. Explain the loss honestly and compare an acknowledgment policy that waits for remote durability.

[Worked mechanism and implementation context](../../04-scale-and-evolution/04-migrations/labs/recovery-migration/regions.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
