# Migrations and recovery

Move live data and clients through compatibility, reconciliation, rollback, and retirement.

[Curriculum](../../README.md) · [About this part](../README.md)

## Before this chapter

[AI systems](../03-ai-systems/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Learn in this order

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Migrations](migration-method.md) |
| 2 | [A worker resumes after somebody else finished](labs/recovery-migration/README.md) |
| 3 | [Move live rows without losing the writes between copies](labs/recovery-migration/migration.md) |
| 4 | [Move a hot tenant, then lose a region](labs/recovery-migration/regions.md) |
| 5 | [Multi-tenant migration](problems/multi-tenant-migration.md) |
| 6 | [Regional failover: which acknowledged write survives?](problems/regional-failover.md) |

## Go deeper on the same problem

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Databases and transactions](../../02-applications/02-databases/README.md) · [Data at scale](../01-data-at-scale/README.md) · [CI/CD and progressive delivery](../../03-production/02-delivery/README.md).

## Apply the concept

Each link opens one existing project brief with its own context, diagrams, AI prompts, AWS choices and follow-ups.

- [The migration you actually finish](projects/the-migration-you-actually-finish.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Technical decisions and engineering effectiveness](../05-technical-decisions/README.md).
