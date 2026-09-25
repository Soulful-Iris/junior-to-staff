# Coding problems in their shapes

Solve the reported problem shapes in Python, then extend each to a stream or to concurrent workers.

<section class="chapter-context" markdown="1">

## Medium problems that turn into streams

CrowdStrike's coding rounds are reported as medium, framed as logs, hosts, events, and files, and extended with the same three follow-ups: what if the input never ends, what if it does not fit in memory, what if several workers process it. The one senior-cloud rejection on record fell on the worker-pool follow-up, not the code. Every bundle here has a baseline contract, six scenarios to settle first, a worked lesson, a reference implementation, tests, and the streaming or concurrent extension as its senior follow-up.

</section>

[Curriculum](../../README.md) · [About this track](../README.md) · [All coding problems](../../../indexes/coding.md)

## Prerequisites

[Data structures and algorithms](../../01-code/02-data-structures-algorithms/README.md), especially windows, heaps, graphs, and the [bounded blocking queue](../../02-applications/01-backend/problems/42-bounded-blocking-queue/README.md).

![The fourteen bundles grouped by pattern: hashing and windows, ordered structures, graphs, framing, and concurrency](../../../assets/crowdstrike/pattern-map.svg)

## Concepts and worked examples

| Step | Bundle | Reported basis |
|---|---|---|
| 1 | [Patterns to their stack](lessons/01-patterns-map.md) | Where each pattern runs at CrowdStrike |
| 2 | [String templating, then a worker pool](problems/43-string-templating/README.md) | `[Reported]` Oct 2025, Cloud senior |
| 3 | [Busiest host, then an endless stream](problems/44-busiest-host/README.md) | `[Aggregator]` log-stream shape |
| 4 | [Telemetry dedupe in a time window](problems/45-telemetry-dedupe/README.md) | `[Generated]` from their at-least-once pipeline |
| 5 | [Time-based key-value store](problems/46-time-based-kv/README.md) | `[Reported]` 2023 |
| 6 | [LRU cache with TTL, like Redis](problems/47-lru-cache-ttl/README.md) | `[Reported]` Jan 2026, Aug 2025 |
| 7 | [Number of islands on a large grid](problems/48-number-of-islands/README.md) | `[Reported]` Nov 2025 ×2 |
| 8 | [Per-tenant token-bucket rate limiter](problems/49-token-bucket/README.md) | `[Aggregator]`; posting names rate limiting |
| 9 | [Log parser: errors per service per minute](problems/50-log-parser/README.md) | `[Aggregator]` log parsing |
| 10 | [Merge k sorted event streams](problems/51-merge-k-streams/README.md) | `[Generated]` from compaction |
| 11 | [Length-prefix codec for framed records](problems/52-length-prefix-codec/README.md) | `[Aggregator]` encode/decode, packet framing |
| 12 | [Dependency order with cycle rejection](problems/53-dependency-order/README.md) | `[Generated]` |
| 13 | [Network delay: shortest time to reach every node](problems/54-network-delay/README.md) | `[Aggregator]` ×2 |
| 14 | [Merge outage intervals](problems/55-interval-merge/README.md) | `[Generated]` |
| 15 | [Bounded worker pool with clean shutdown](problems/56-worker-pool/README.md) | `[Reported]` follow-up; `[Aggregator]` thread-safe queue |

Attempt each before opening its worked lesson. Finish the baseline, run the tests, then do the senior follow-up with the reference closed. In the room, say the memory bound the moment the input becomes a stream.

## Reference guides

| Guide | Use |
|---|---|
| [Python toolkit for these rounds](lessons/02-python-toolkit.md) | The standard-library calls you should not have to look up |
