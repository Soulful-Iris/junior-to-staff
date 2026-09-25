# Architecture: their systems and their design cases

Design the systems they ask about at the scale they publish, and defend every box for ninety minutes.

<section class="chapter-context" markdown="1">

## Learn how they built it, then design what they ask

CrowdStrike publishes more about its own architecture than most companies: Kafka sharded into fungible clusters at 15 million events a second, Go consumers with three retry tiers, an append-only graph on LSM stores, ring-based rollout after the 2024 outage. Their design reviews use that vocabulary and that scale. The first three lessons give you the systems, the building blocks with the sentence to say for each, and the method for a ninety-minute defense. The nine cases that follow are the reported and inferred design prompts, each worked to a main path, a table of expected behaviors, failure modes, and senior and staff follow-ups.

</section>

[Curriculum](../../README.md) · [About this track](../README.md) · [All system designs](../../../indexes/system-designs.md)

## Prerequisites

[System design under constraints](../../03-production/01-system-design/README.md) and [Data systems at scale](../../04-scale-and-evolution/01-data-at-scale/README.md).

![Sensor to cloud at CrowdStrike: sensors, gateway, sharded Kafka, Go consumers, Threat Graph on LSM stores, detections back to the customer](../../../assets/crowdstrike/sensor-to-cloud.svg)

## Concepts and worked examples

| Step | Lesson or case | Basis |
|---|---|---|
| 1 | [How CrowdStrike builds it](lessons/01-how-crowdstrike-builds-it.md) | `[Official]` engineering blog and incident reports |
| 2 | [Building blocks, and the sentence for each](lessons/02-building-blocks.md) | Posting requirements mapped to their stack |
| 3 | [The ninety-minute review](lessons/03-the-ninety-minute-review.md) | `[Reported]` review formats, 2020–2026 |
| 4 | [File-scanning platform](problems/file-scanning-platform.md) | `[Reported]` seven times, 2019–2026 |
| 5 | [Real-time event message system](problems/event-message-system.md) | `[Reported]` Jan 2026 take-home |
| 6 | [Telemetry ingestion from millions of endpoints](problems/telemetry-ingestion.md) | `[Aggregator]` ×3; the posting's team |
| 7 | [Content rollout with rings and rollback](problems/content-rollout-rings.md) | `[Official]` post-2024 model |
| 8 | [Endpoint management control plane](problems/endpoint-control-plane.md) | `[Official]` the R30109 team's words |
| 9 | [Searchable event store with hot and cold tiers](problems/searchable-event-store.md) | `[Aggregator]` logging service with search |
| 10 | [Rate limiter and distributed queue](problems/rate-limiter-and-queue.md) | `[Aggregator]`; idempotent endpoints |
| 11 | [Design Redis, briefly](problems/design-redis.md) | `[Reported]` Jan 2026 |
| 12 | [Worker pool for template jobs](problems/worker-pool-template-jobs.md) | `[Aggregator]` Oct 2025; `[Reported]` live follow-up |

Work case 4 first and defend it aloud twice; it is the one design prompt that is genuinely repeated. Then case 5, which is the shape of the most recent senior offer. The rest in order.
