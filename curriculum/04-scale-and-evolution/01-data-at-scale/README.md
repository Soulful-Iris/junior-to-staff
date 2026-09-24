# Process, search and store data at scale

Reason about caches, replication, partitioning, streams, and coordination scope.

<section class="chapter-context" markdown="1">

## Add capacity without losing the meaning of the data

Two hundred readers miss the same cache entry. A replica has yesterday’s version. A single tenant overwhelms one partition while the fleet average remains low. Each case requires a different boundary and a different measurement.

Start with the cache and consistency models, then study projections, partition skew, and the larger design briefs. State coordination scope, freshness, and write authority. Local examples demonstrate protocols, while AWS adapters and real capacity measurements remain explicit deployment work.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Set reliability objectives and recover from failures](../../03-production/05-reliability/README.md)

Caching, replication and partitioning are answers to "this does not fit or does not keep up", which is an arithmetic finding first: see [Estimate request rates, storage, latency and availability](../../01-code/01-problem-solving/estimation-constants.md).

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Protect shared storage with bounded cache loads and consistent reads](scaling-data.md) |
| 2 | [Trace LRU eviction before implementing its linked order](cache-order.md) |
| 3 | [Implement LRU without an ordered-map helper](problems/28-manual-lru-cache/README.md) |
| 4 | [Expiring key-value store](problems/29-expiring-key-value-store/README.md) |
| 5 | [Bound cache misses across instances and preserve fresh reads](labs/cache-consistency/README.md) |
| 6 | [Enforce revocation even when a CDN already has the content](labs/cache-consistency/revocation.md) |
| 7 | [Count event-time windows with late arrivals](problems/40-event-time-windows/README.md) |
| 8 | [Keep job status current without repeating completed work](cases/status-projections.md) |
| 9 | [Distribute a hot tenant while preserving event identity and ordering](cases/hot-partitions.md) |
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
