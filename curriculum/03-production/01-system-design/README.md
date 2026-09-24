# Design services from requirements to failure behavior

Turn requirements and workload estimates into an explainable architecture.

**Artifact types:** the short architecture pages below are **design briefs**, not completed applications. They supply a contract, diagrams and questions to work through. A **worked design** explains a particular solution; an **executable reference** links to source and a test command; a **deployment lab** supplies setup and cleanup steps. None of these labels alone means a live cloud deployment was verified.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Enforce identity, ownership and tenant boundaries](../../02-applications/05-security/README.md)

Start each project with its application background and assignment. Run its local example, then use the workload to size the implementation: [The constants you estimate with](../../01-code/01-problem-solving/estimation-constants.md) is the per-second, latency and availability arithmetic these designs assume.

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [System design](design-method.md) |
| 2 | [Draw the system, then break it](whiteboard.md) |
| 3 | [Architecture · understand the mechanism before naming a service](mechanism-reference.md) |
| 4 | [Build a private bookmark API with ownership and version checks](problems/bookmark-service.md) |
| 5 | [Enforce API quotas across concurrent gateways](problems/api-quota.md) |
| 6 | [Reserve concert seats with expiring holds](problems/ticket-inventory.md) |
| 7 | [Build chat with durable messages and reconnect recovery](problems/realtime-chat.md) |
| 8 | [Build a following feed with current access checks](problems/social-feed.md) |
| 9 | [Process uploads and publish complete video renditions](problems/video-processing.md) |
| 10 | [Build checkout that recovers from uncertain payments](problems/checkout-payment.md) |
| 11 | [Deliver notifications with preferences and priority](problems/notification-platform.md) |
| 12 | [Build a versioned shared document editor](problems/collaborative-editor.md) |
| 13 | [Deliver signed webhooks with retries and replay](problems/webhook-delivery.md) |
| 14 | [Build short links with unique aliases and safe redirects](problems/url-shortener.md) |
| 15 | [Assign drivers safely with expiring offers](problems/rideshare-dispatch.md) |
| 16 | [Build restaurant discovery and authoritative checkout](problems/food-delivery-marketplace.md) |
| 17 | [Reserve rooms and handle recurring local times](problems/calendar-availability.md) |
| 18 | [Build resumable uploads and authorized video playback](problems/video-streaming-platform.md) |
| 19 | [Collect news feeds with freshness and deduplication](problems/news-aggregator.md) |
| 20 | [Build versioned API routing and admission policies](problems/api-gateway-platform.md) |
| 21 | [Run programming submissions inside isolated workers](problems/online-judge.md) |

The 15 catalog-sourced prompts distributed across this and later chapters link to community interview-question entries. The catalog tags candidate reports with companies, but usually omits interview dates. Treat these as widely listed prompt types, not verified reports from the past year or a current company rubric. See the [source review and recency limits](../../../docs/research/interview-design-problem-set-2026.md).

Work through each project from the application background to the local demonstration. Implement the named behavior and record its successful and failing outcomes. Then use the local-to-AWS table to identify the adapters and infrastructure needed for deployment. The later chapters return to these boundaries under observability, outages, large data, AI serving, and regional recovery.

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Set reliability objectives and recover from failures](../05-reliability/README.md) · [Process, search and store data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Measure capacity and control performance costs](../../04-scale-and-evolution/02-performance-cost/README.md).

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Deploy changes and control feature exposure](../02-delivery/README.md).
