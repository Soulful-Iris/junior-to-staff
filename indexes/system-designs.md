# System design · worked examples and design briefs

These are original practice prompts chosen to exercise the concepts. They are not a ranked list of current company questions. Reported question families and their evidence limits are in [research](../docs/research/interview-evidence.md).

This catalog links **41 design and architecture practice pages**: five longer
worked examples and 36 focused briefs, grouped below by prerequisite chapter.
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

[Bookmark service candidate page](../curriculum/03-production/01-system-design/problems/bookmark-service.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 2 · Notification platform

[Notification platform candidate page](../curriculum/03-production/01-system-design/problems/notification-platform.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 3 · File synchronization

[File synchronization candidate page](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/file-synchronization.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 4 · Multi-tenant migration

[Multi-tenant migration candidate page](../curriculum/04-scale-and-evolution/04-migrations/problems/multi-tenant-migration.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 5 · AI support assistant

[Support assistant candidate page](../curriculum/04-scale-and-evolution/03-ai-systems/problems/support-assistant.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## Explain alternatives sympathetically

For each design, defend one alternative before deciding: synchronous versus queued, SQL versus key-value, strong versus eventual reads, regional versus multi-region. State the constraint that changes your answer.

[Concepts](../curriculum/03-production/01-system-design/mechanism-reference.md) · [AWS implementation](../curriculum/03-production/03-infrastructure/aws/README.md) · [Practice rubric](../practice/README.md)

## Focused briefs by prerequisite

Use the owning chapter first, then state the contract, trace the baseline visual,
and work through the failure and follow-ups. Constructed workload numbers are
practice assumptions, not company production measurements.

### Security

- [Audit trail: who changed this permission?](../curriculum/02-applications/05-security/problems/audit-trail.md)
- [Tenant isolation: an ID in the URL is not authority](../curriculum/02-applications/05-security/problems/tenant-isolation.md)

### System design

- [API gateway: route safely across many teams](../curriculum/03-production/01-system-design/problems/api-gateway-platform.md)
- [API quota: which request spends the last token?](../curriculum/03-production/01-system-design/problems/api-quota.md)
- [Calendar: reserve time without hiding conflicts](../curriculum/03-production/01-system-design/problems/calendar-availability.md)
- [Checkout: paid twice, ordered once?](../curriculum/03-production/01-system-design/problems/checkout-payment.md)
- [Collaborative editor: two people edit the same sentence](../curriculum/03-production/01-system-design/problems/collaborative-editor.md)
- [Food delivery: quote the right nearby options](../curriculum/03-production/01-system-design/problems/food-delivery-marketplace.md)
- [News aggregator: freshness without a write storm](../curriculum/03-production/01-system-design/problems/news-aggregator.md)
- [Online judge: untrusted code gets a small box](../curriculum/03-production/01-system-design/problems/online-judge.md)
- [Realtime chat: reconnect without losing the conversation](../curriculum/03-production/01-system-design/problems/realtime-chat.md)
- [Ride sharing: one driver, one accepted ride](../curriculum/03-production/01-system-design/problems/rideshare-dispatch.md)
- [Social feed: a popular author changes the shape](../curriculum/03-production/01-system-design/problems/social-feed.md)
- [Ticket inventory: one seat, two buyers](../curriculum/03-production/01-system-design/problems/ticket-inventory.md)
- [URL shortener: who owns the code?](../curriculum/03-production/01-system-design/problems/url-shortener.md)
- [Video processing: accept once, publish when ready](../curriculum/03-production/01-system-design/problems/video-processing.md)
- [Video streaming: keep playback smooth at the edge](../curriculum/03-production/01-system-design/problems/video-streaming-platform.md)
- [Webhook delivery: a timeout is not a rejection](../curriculum/03-production/01-system-design/problems/webhook-delivery.md)

### CI/CD and progressive delivery

- [Feature rollout: the switch that failed after 100%](../curriculum/03-production/02-delivery/problems/feature-rollout.md)

### Observability

- [Metrics platform: query the right time window](../curriculum/03-production/04-observability/problems/metrics-platform.md)
- [Slow request: the healthy average hid a timeout](../curriculum/03-production/04-observability/problems/slow-request.md)

### Reliability and incident response

- [Durable jobs: the queue drained, the work did not](../curriculum/03-production/05-reliability/problems/durable-jobs.md)
- [Job scheduler: fire once on time, recover after a crash](../curriculum/03-production/05-reliability/problems/job-scheduler.md)

### Data at scale

- [Ad click aggregator: count late events once](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/ad-click-aggregator.md)
- [Distributed cache: recover when one shard leaves](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-cache.md)
- [Key-value store: acknowledge only what survives](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-key-value-store.md)
- [Document search: results must follow permissions](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/document-search.md)
- [Event ingestion: change a schema without losing yesterday](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/event-ingestion.md)
- [Trending counts: the spike that breaks one partition](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/trending-counts.md)
- [Typeahead: useful suggestions before the next keystroke](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/typeahead-search.md)
- [Web crawler: be fast without attacking one site](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/web-crawler.md)

### Performance and cost

- [Overload: protect the requests that can finish](../curriculum/04-scale-and-evolution/02-performance-cost/problems/overload-shedding.md)

### AI systems

- [Knowledge assistant: the citation that lost access](../curriculum/04-scale-and-evolution/03-ai-systems/problems/knowledge-assistant.md)
- [Personalized ranking: low latency and evidence of quality](../curriculum/04-scale-and-evolution/03-ai-systems/problems/personalized-ranking.md)

### Migrations and recovery

- [Data erasure: one request, nine copies](../curriculum/04-scale-and-evolution/04-migrations/problems/erasure-workflow.md)
- [Regional failover: which acknowledged write survives?](../curriculum/04-scale-and-evolution/04-migrations/problems/regional-failover.md)
