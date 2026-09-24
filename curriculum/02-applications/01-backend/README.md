# Build HTTP APIs and reliable background work

Trace a request, define its contract, and coordinate bounded work.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Choose data structures and reason about algorithms](../../01-code/02-data-structures-algorithms/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Backend](request-lifecycle.md) |
| 2 | [A valid HTTP 200 with an invalid body](labs/api-contract/README.md) |
| 3 | [Runtime boundaries · which work can overlap?](labs/bounded-executor/runtime.md) |
| 4 | [Bounded fan-out · preserve order under partial failure](labs/fan-out/README.md) |
| 5 | [Bounded blocking queue with shutdown](problems/42-bounded-blocking-queue/README.md) |
| 6 | [Bounded executor · four workers, eight queued tasks](labs/bounded-executor/README.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Model data and enforce transactional rules](../02-databases/README.md) · [Enforce identity, ownership and tenant boundaries](../05-security/README.md) · [Set reliability objectives and recover from failures](../../03-production/05-reliability/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Trace requests through a bookmark API](projects/01-the-request-you-can-trace-end-to-end.md)
- [Enforce a single deadline across API dependencies](projects/02-the-three-second-budget.md)
- [Build an SSRF-resistant link preview fetcher](projects/03-the-fetch-that-cannot-be-aimed-inward.md)
- [Evolve tag responses without breaking old clients](projects/04-the-api-that-does-not-break-its-callers.md)
- [Move title lookup into restartable background jobs](projects/05-the-job-that-survives-a-restart.md)
- [Build a link monitor with durable history and change alerts](projects/a-link-rot-watcher.md)
- [Build duplicate-safe form submission and CSV export](projects/a-public-form.md)

## Reference guides

- [Backend — five projects](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Model data and enforce transactional rules](../02-databases/README.md).
