# Reliability and incident recovery

Budget failures, bound overload, and recover from evidence.

<section class="chapter-context" markdown="1">

## Choose failure behavior before the dependency slows down

A dependency that normally takes 200 ms begins taking two seconds. Slots stay occupied, queues grow, and retries add more attempts. Even after the dependency recovers, the service needs spare capacity to catch up.

Separate successful user work from attempts, calculate the error allowance, and bound admission and waiting. The local arithmetic and incident exercises supply reproducible inputs. Follow recovery until useful work is current again, not merely until one alert clears.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Production observability](../04-observability/README.md)

An availability target is only concrete once it is a downtime budget: the nines table in [Estimate request rates, storage, latency and availability](../../01-code/01-problem-solving/estimation-constants.md) is what turns 99.99% into fifty-three minutes a year.

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Set an error budget and bound retries during overload](failure-budgets.md) |
| 2 | [Calculate error budgets, retry amplification and recovery capacity](labs/reliability/README.md) |
| 3 | [Bound retry load and reconcile a lost payment response](cases/retry-amplification.md) |
| 4 | [Mitigate an incident, verify recovery and complete the follow-up](risk-and-incidents.md) |
| 5 | [Diagnose stale work after the request-error alert clears](labs/reliability/incident.md) |
| 6 | [Build restartable CSV export jobs](problems/durable-jobs.md) |
| 7 | [Schedule reports without duplicate logical runs](problems/job-scheduler.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Production observability](../04-observability/README.md) · [Data systems at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Live migrations](../../04-scale-and-evolution/04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Define and calculate a user-facing save SLO](projects/01-the-slo-you-would-actually-honour.md)
- [Implement burn-rate alert and incident state rules](projects/02-the-alert-that-fires-when-it-matters-and-not-before.md)
- [Bound retries across browser, API and SDK layers](projects/03-the-retry-storm-you-build-on-purpose.md)
- [Prioritize API work within a fixed capacity budget](projects/04-shedding-the-right-thing.md)
- [Recover a service trapped in expired work and retries](projects/05-the-failure-that-will-not-recover.md)
- [Keep bookmark saves usable when title lookup fails](projects/degrade-do-not-stop.md)
- [Rehearse detection, rollback and service recovery](projects/the-incident-you-caused-on-purpose.md)

## Reference guides

- [Reliability — five projects](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Live migrations](../../04-scale-and-evolution/04-migrations/README.md).
