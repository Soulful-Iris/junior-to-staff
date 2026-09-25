# System design · worked examples and design briefs

These are original practice prompts chosen to exercise the concepts. They are not a ranked list of current company questions. Reported question families and their evidence limits are in [research](../docs/research/interview-evidence.md).

This catalog links **50 design and architecture practice pages**: five longer
worked examples, 36 focused briefs, and nine CrowdStrike track cases, grouped below by prerequisite chapter.
These are not 41 deployed applications. Some focus on diagnostic or operational
reasoning rather than building an entire service. Runnable references are labeled
separately and provide a source directory and test command.

## A 45-minute practice structure

| Minutes | Produce | Check before moving on |
|---|---|---|
| 0–5 | Users, top two use cases, non-goals | Are you solving the asked product? |
| 5–10 | Scale, latency, durability, consistency | Which numbers change a decision? |
| 10–18 | API, data ownership, minimal end-to-end flow | Can one real request succeed? |
| 18–32 | One or two deep dives | Which bottleneck or failure matters most? |
| 32–40 | Recovery, operations, security, cost | What happens when a dependency is slow? |
| 40–45 | Tradeoffs and next experiment | What uncertainty would you resolve first? |

This is a practice timebox; follow an interviewer's direction. In low-level
design, leave enough time for classes and executable methods. Do not spend the
whole round on high-level architecture when implementation was requested.

## 1 · Bookmark service

[Build a private bookmark API with ownership and version checks](../curriculum/03-production/01-system-design/problems/bookmark-service.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 2 · Notification platform

[Deliver notifications with preferences and priority](../curriculum/03-production/01-system-design/problems/notification-platform.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 3 · File synchronization

[Synchronize files with resumable uploads and conflicts](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/file-synchronization.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 4 · Multi-tenant migration

[Migrate tenant data with a resumable backfill](../curriculum/04-scale-and-evolution/04-migrations/problems/multi-tenant-migration.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 5 · AI support assistant

[Draft support replies without granting tool authority](../curriculum/04-scale-and-evolution/03-ai-systems/problems/support-assistant.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## Explain alternatives sympathetically

For each design, defend one alternative before deciding: synchronous versus queued, SQL versus key-value, strong versus eventual reads, regional versus multi-region. State the constraint that changes your answer.

[Concepts](../curriculum/03-production/01-system-design/mechanism-reference.md) · [AWS implementation](../curriculum/03-production/03-infrastructure/aws/README.md) · [Practice rubric](../practice/README.md)

## Focused briefs by prerequisite

Use the owning chapter first, then state the contract, trace the baseline visual,
and work through the failure and follow-ups. Constructed workload numbers are
practice assumptions, not company production measurements.

### Security

- [Record permission changes with durable audit evidence](../curriculum/02-applications/05-security/problems/audit-trail.md)
- [Enforce tenant access in APIs, caches and exports](../curriculum/02-applications/05-security/problems/tenant-isolation.md)

### System design

- [Build versioned API routing and admission policies](../curriculum/03-production/01-system-design/problems/api-gateway-platform.md)
- [Enforce API quotas across concurrent gateways](../curriculum/03-production/01-system-design/problems/api-quota.md)
- [Reserve rooms and handle recurring local times](../curriculum/03-production/01-system-design/problems/calendar-availability.md)
- [Build checkout that recovers from uncertain payments](../curriculum/03-production/01-system-design/problems/checkout-payment.md)
- [Build a versioned shared document editor](../curriculum/03-production/01-system-design/problems/collaborative-editor.md)
- [Build restaurant discovery and authoritative checkout](../curriculum/03-production/01-system-design/problems/food-delivery-marketplace.md)
- [Collect news feeds with freshness and deduplication](../curriculum/03-production/01-system-design/problems/news-aggregator.md)
- [Run programming submissions inside isolated workers](../curriculum/03-production/01-system-design/problems/online-judge.md)
- [Build chat with durable messages and reconnect recovery](../curriculum/03-production/01-system-design/problems/realtime-chat.md)
- [Assign drivers safely with expiring offers](../curriculum/03-production/01-system-design/problems/rideshare-dispatch.md)
- [Build a following feed with current access checks](../curriculum/03-production/01-system-design/problems/social-feed.md)
- [Reserve concert seats with expiring holds](../curriculum/03-production/01-system-design/problems/ticket-inventory.md)
- [Build short links with unique aliases and safe redirects](../curriculum/03-production/01-system-design/problems/url-shortener.md)
- [Process uploads and publish complete video renditions](../curriculum/03-production/01-system-design/problems/video-processing.md)
- [Build resumable uploads and authorized video playback](../curriculum/03-production/01-system-design/problems/video-streaming-platform.md)
- [Deliver signed webhooks with retries and replay](../curriculum/03-production/01-system-design/problems/webhook-delivery.md)

### CI/CD and progressive delivery

- [Release invoice changes with stable cohorts and rollback](../curriculum/03-production/02-delivery/problems/feature-rollout.md)

### Observability

- [Ingest and query metrics with bounded cardinality](../curriculum/03-production/04-observability/problems/metrics-platform.md)
- [Find database-pool waiting in slow API requests](../curriculum/03-production/04-observability/problems/slow-request.md)

### Reliability and incident response

- [Build restartable CSV export jobs](../curriculum/03-production/05-reliability/problems/durable-jobs.md)
- [Schedule reports without duplicate logical runs](../curriculum/03-production/05-reliability/problems/job-scheduler.md)

### Data at scale

- [Aggregate click events with late arrivals and reconciliation](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/ad-click-aggregator.md)
- [Protect a database with versioned cache fills](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-cache.md)
- [Implement replicated writes and fenced leadership](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-key-value-store.md)
- [Search documents without leaking revoked content](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/document-search.md)
- [Ingest events with durable acceptance and replay](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/event-ingestion.md)
- [Compute trending topics from duplicate and late events](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/trending-counts.md)
- [Build typeahead with stale-response protection](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/typeahead-search.md)
- [Build a durable crawler with per-host limits](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/web-crawler.md)

### Performance and cost

- [Reject excess API work before queues grow without bound](../curriculum/04-scale-and-evolution/02-performance-cost/problems/overload-shedding.md)

### AI systems

- [Build a document assistant with current permissions](../curriculum/04-scale-and-evolution/03-ai-systems/problems/knowledge-assistant.md)
- [Serve recommendations with safe fallback ranking](../curriculum/04-scale-and-evolution/03-ai-systems/problems/personalized-ranking.md)

### Migrations and recovery

- [Erase account data across stores and in-flight work](../curriculum/04-scale-and-evolution/04-migrations/problems/erasure-workflow.md)
- [Design and rehearse regional write failover](../curriculum/04-scale-and-evolution/04-migrations/problems/regional-failover.md)

### CrowdStrike track

- [File-scanning platform: upload once, scan with many engines, one report](../curriculum/05-crowdstrike/03-architecture/problems/file-scanning-platform.md)
- [Real-time event message system with per-key order and safe replay](../curriculum/05-crowdstrike/03-architecture/problems/event-message-system.md)
- [Telemetry ingestion from millions of endpoints, with detections in seconds](../curriculum/05-crowdstrike/03-architecture/problems/telemetry-ingestion.md)
- [Content rollout with rings, golden signals, and rollback in minutes](../curriculum/05-crowdstrike/03-architecture/problems/content-rollout-rings.md)
- [Endpoint management control plane: inventory, policy, and commands for millions of hosts](../curriculum/05-crowdstrike/03-architecture/problems/endpoint-control-plane.md)
- [Searchable event store with hot and cold tiers](../curriculum/05-crowdstrike/03-architecture/problems/searchable-event-store.md)
- [Rate limiter and distributed queue as building blocks, with an idempotent endpoint](../curriculum/05-crowdstrike/03-architecture/problems/rate-limiter-and-queue.md)
- [Design Redis, briefly](../curriculum/05-crowdstrike/03-architecture/problems/design-redis.md)
- [Worker pool for template jobs at scale](../curriculum/05-crowdstrike/03-architecture/problems/worker-pool-template-jobs.md)
