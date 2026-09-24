# Migrate live systems and verify recovery

Move live data and clients through compatibility, reconciliation, rollback, and retirement.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Build AI features with evidence and controlled actions](../03-ai-systems/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Migrations](migration-method.md) |
| 2 | [A worker resumes after somebody else finished](labs/recovery-migration/README.md) |
| 3 | [Move live rows without losing the writes between copies](labs/recovery-migration/migration.md) |
| 4 | [Move a hot tenant, then lose a region](labs/recovery-migration/regions.md) |
| 5 | [Migrate tenant data with a resumable backfill](problems/multi-tenant-migration.md) |
| 6 | [Design and rehearse regional write failover](problems/regional-failover.md) |
| 7 | [Erase account data across stores and in-flight work](problems/erasure-workflow.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Model data and enforce transactional rules](../../02-applications/02-databases/README.md) · [Process, search and store data at scale](../01-data-at-scale/README.md) · [Deploy changes and control feature exposure](../../03-production/02-delivery/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Migrate tags across data, clients and workers](projects/the-migration-you-actually-finish.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Make technical decisions and improve team workflows](../05-technical-decisions/README.md).
