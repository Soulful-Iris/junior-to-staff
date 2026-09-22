# Data at scale

Reason about caches, replication, partitioning, streams, and coordination scope.

[Curriculum](../../README.md) · [About this part](../README.md)

## Before this chapter

[Reliability and incident response](../../03-production/05-reliability/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Learn in this order

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Data at scale](scaling-data.md) |
| 2 | [Stateful coding: design an LRU cache](cache-order.md) |
| 3 | [Implement LRU without an ordered-map helper](problems/28-manual-lru-cache/README.md) |
| 4 | [Expiring key-value store](problems/29-expiring-key-value-store/README.md) |
| 5 | [An expired key, ten instances, and a finite database](labs/cache-consistency/README.md) |
| 6 | [Revoke a link that is already warm](labs/cache-consistency/revocation.md) |
| 7 | [Count event-time windows with late arrivals](problems/40-event-time-windows/README.md) |
| 8 | [Completed work can have a stale status view](cases/status-projections.md) |
| 9 | [A healthy average can hide an overloaded partition](cases/hot-partitions.md) |
| 10 | [File synchronization](problems/file-synchronization.md) |

## Go deeper on the same problem

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Backend and APIs](../../02-applications/01-backend/README.md) · [Databases and transactions](../../02-applications/02-databases/README.md) · [Reliability and incident response](../../03-production/05-reliability/README.md) · [Migrations and recovery](../04-migrations/README.md).

## Apply the concept

Each link opens one existing project brief with its own context, diagrams, AI prompts, AWS choices and follow-ups.

- [The flood](projects/the-flood.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Performance and cost](../02-performance-cost/README.md).
