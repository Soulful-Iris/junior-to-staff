# Process, search and store data at scale

Reason about caches, replication, partitioning, streams, and coordination scope.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Set reliability objectives and recover from failures](../../03-production/05-reliability/README.md)

Caching, replication and partitioning are answers to "this does not fit or does not keep up", which is an arithmetic finding first: see [The constants you estimate with](../../01-code/01-problem-solving/estimation-constants.md).

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

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
| 10 | [Synchronize files with resumable uploads and conflicts](problems/file-synchronization.md) |
| 11 | [Search documents without leaking revoked content](problems/document-search.md) |
| 12 | [Compute trending topics from duplicate and late events](problems/trending-counts.md) |
| 13 | [Ingest events with durable acceptance and replay](problems/event-ingestion.md) |
| 14 | [Build a durable crawler with per-host limits](problems/web-crawler.md) |
| 15 | [Build typeahead with stale-response protection](problems/typeahead-search.md) |
| 16 | [Protect a database with versioned cache fills](problems/distributed-cache.md) |
| 17 | [Implement replicated writes and fenced leadership](problems/distributed-key-value-store.md) |
| 18 | [Aggregate click events with late arrivals and reconciliation](problems/ad-click-aggregator.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Build HTTP APIs and reliable background work](../../02-applications/01-backend/README.md) · [Model data and enforce transactional rules](../../02-applications/02-databases/README.md) · [Set reliability objectives and recover from failures](../../03-production/05-reliability/README.md) · [Migrate live systems and verify recovery](../04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Build ingestion with bounded backlog and explicit rejection](projects/the-flood.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Measure capacity and control performance costs](../02-performance-cost/README.md).
