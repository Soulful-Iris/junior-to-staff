# System design · worked examples and changing constraints

These are original practice prompts chosen to exercise the concepts. They are not a ranked list of current company questions. Recent reported question families and their limits are in [research](../research/README.md).

## A 45-minute practice structure

| Minutes | Produce | Check before moving on |
|---|---|---|
| 0–5 | Users, top two use cases, non-goals | Are you solving the asked product? |
| 5–10 | Scale, latency, durability, consistency | Which numbers change a decision? |
| 10–18 | API, data ownership, minimal end-to-end flow | Can one real request succeed? |
| 18–32 | One or two deep dives | Which bottleneck or failure matters most? |
| 32–40 | Recovery, operations, security, cost | What happens when a dependency is slow? |
| 40–45 | Tradeoffs and next experiment | What uncertainty would you resolve first? |

This is a practice timebox; follow an interviewer's direction. In LLD, leave enough time for classes and executable methods. Do not spend the whole round on HLD when implementation was requested.

## 1 · Bookmark service · junior foundation

[Bookmark service candidate page](designs/bookmark-service.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 2 · Notification platform · senior core

[Notification platform candidate page](designs/notification-platform.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 3 · File synchronization · senior full stack

[File synchronization candidate page](designs/file-synchronization.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 4 · Multi-tenant migration · staff core

[Multi-tenant migration candidate page](designs/multi-tenant-migration.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## 5 · AI support assistant · optional specialization

[Support assistant candidate page](designs/support-assistant.md) — opening contract, baseline, worked approach, changing assumptions, and assessment.

## Explain alternatives sympathetically

For each design, defend one alternative before deciding: synchronous versus queued, SQL versus key-value, strong versus eventual reads, regional versus multi-region. State the constraint that changes your answer.

[Concepts](concepts.md) · [AWS implementation](../aws/README.md) · [Practice rubric](../practice/README.md)
