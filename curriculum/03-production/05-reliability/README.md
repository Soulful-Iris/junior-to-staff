# Set reliability objectives and recover from failures

Budget failures, bound overload, and recover from evidence.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Trace requests and diagnose production symptoms](../04-observability/README.md)

An availability target is only concrete once it is a downtime budget: the nines table in [The constants you estimate with](../../01-code/01-problem-solving/estimation-constants.md) is what turns 99.99% into fifty-three minutes a year.

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Reliability](failure-budgets.md) |
| 2 | [Reliability: count users, attempts, and work separately](labs/reliability/README.md) |
| 3 | [Retries spend the capacity needed for recovery](cases/retry-amplification.md) |
| 4 | [Risk and incidents](risk-and-incidents.md) |
| 5 | [Incident desk: the page cleared, the queue did not](labs/reliability/incident.md) |
| 6 | [Build restartable CSV export jobs](problems/durable-jobs.md) |
| 7 | [Schedule reports without duplicate logical runs](problems/job-scheduler.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Trace requests and diagnose production symptoms](../04-observability/README.md) · [Process, search and store data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Migrate live systems and verify recovery](../../04-scale-and-evolution/04-migrations/README.md).

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

Next chapter: [Process, search and store data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md).
