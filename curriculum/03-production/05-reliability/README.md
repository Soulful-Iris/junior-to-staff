# Reliability and incident response

Budget failures, bound overload, and recover from evidence.

[Curriculum](../../README.md) · [About this part](../README.md)

## Before this chapter

[Observability](../04-observability/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Learn in this order

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Reliability](failure-budgets.md) |
| 2 | [Reliability: count users, attempts, and work separately](labs/reliability/README.md) |
| 3 | [Retries spend the capacity needed for recovery](cases/retry-amplification.md) |
| 4 | [Risk and incidents](risk-and-incidents.md) |
| 5 | [Incident desk: the page cleared, the queue did not](labs/reliability/incident.md) |

## Go deeper on the same problem

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Observability](../04-observability/README.md) · [Data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Migrations and recovery](../../04-scale-and-evolution/04-migrations/README.md).

## Apply the concept

Each link opens one existing project brief with its own context, diagrams, AI prompts, AWS choices and follow-ups.

- [The SLO you would actually honour](projects/01-the-slo-you-would-actually-honour.md)
- [The alert that fires when it matters and not before](projects/02-the-alert-that-fires-when-it-matters-and-not-before.md)
- [The retry storm you build on purpose](projects/03-the-retry-storm-you-build-on-purpose.md)
- [Shedding the right thing](projects/04-shedding-the-right-thing.md)
- [The failure that will not recover](projects/05-the-failure-that-will-not-recover.md)
- [Degrade, do not stop](projects/degrade-do-not-stop.md)
- [The incident you caused on purpose](projects/the-incident-you-caused-on-purpose.md)

## Supporting material

- [Reliability — five projects](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md).
