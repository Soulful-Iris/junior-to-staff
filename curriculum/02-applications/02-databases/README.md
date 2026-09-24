# Model data and enforce transactional rules

Model authoritative data, explain a query plan, and protect concurrent writes.

<section class="chapter-context" markdown="1">

## Decide what a row means and who may change it

Several people can read the same bookmark while each has their own read/unread state. Two buyers can also race for the last item in stock. These examples show why a correct-looking table and a transaction keyword do not by themselves enforce the product’s rules.

Model identity and access patterns first. Then inspect query plans and drive conflicting writes in two PostgreSQL sessions. Keep the supplied PostgreSQL lab separate from the starter API’s SQLite database. Explain both returned rows and rejected operations.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Build HTTP APIs and reliable background work](../01-backend/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Model shared data and enforce changes with database constraints](data-models-and-queries.md) |
| 2 | [Prevent overselling and write skew with the right transaction boundary](labs/postgresql/README.md) |
| 3 | [Drive conflicting transactions in two PostgreSQL sessions](labs/postgresql/schedules.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Process, search and store data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Migrate live systems and verify recovery](../../04-scale-and-evolution/04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Store receipts with reviewable extraction and corrections](projects/a-receipt-tracker.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Connect a usable interface to an API](../03-frontend/README.md).
