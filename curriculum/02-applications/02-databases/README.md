# Model data and enforce transactional rules

Model authoritative data, explain a query plan, and protect concurrent writes.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Build HTTP APIs and reliable background work](../01-backend/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Data and databases](data-models-and-queries.md) |
| 2 | [Two buyers, one unit, and a transaction that is not enough](labs/postgresql/README.md) |
| 3 | [Candidate worksheet: drive two independent sessions](labs/postgresql/schedules.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Process, search and store data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Migrate live systems and verify recovery](../../04-scale-and-evolution/04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Store receipts with reviewable extraction and corrections](projects/a-receipt-tracker.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Connect a usable interface to an API](../03-frontend/README.md).
