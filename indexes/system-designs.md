# System design · worked examples and design briefs

These are original practice prompts chosen to exercise the concepts. They are not a ranked list of current company questions. Recent reported question families and their limits are in [research](../docs/research/interview-evidence.md).

The five longer worked examples below explain a baseline; they are not five deployed applications. For the full set of shorter architecture briefs, start at the [system-design chapter](../curriculum/03-production/01-system-design/README.md) and follow the [curriculum](../curriculum/README.md) into reliability, data and AI. Runnable artifacts identify their source directory and test command explicitly.

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
