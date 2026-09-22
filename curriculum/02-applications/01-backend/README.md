# Backend and APIs

Trace a request, define its contract, and coordinate bounded work.

[Curriculum](../../README.md) · [About this part](../README.md)

## Before this chapter

[Data structures and algorithms](../../01-code/02-data-structures-algorithms/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Learn in this order

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Backend](request-lifecycle.md) |
| 2 | [A valid HTTP 200 with an invalid body](labs/api-contract/README.md) |
| 3 | [Runtime boundaries · which work can overlap?](labs/bounded-executor/runtime.md) |
| 4 | [Bounded fan-out · preserve order under partial failure](labs/fan-out/README.md) |
| 5 | [Bounded blocking queue with shutdown](problems/42-bounded-blocking-queue/README.md) |
| 6 | [Bounded executor · four workers, eight queued tasks](labs/bounded-executor/README.md) |

## Go deeper on the same problem

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Databases and transactions](../02-databases/README.md) · [Security](../05-security/README.md) · [Reliability and incident response](../../03-production/05-reliability/README.md).

## Apply the concept

Each link opens one existing project brief with its own context, diagrams, AI prompts, AWS choices and follow-ups.

- [The request you can trace end to end](projects/01-the-request-you-can-trace-end-to-end.md)
- [The three-second budget](projects/02-the-three-second-budget.md)
- [The fetch that cannot be aimed inward](projects/03-the-fetch-that-cannot-be-aimed-inward.md)
- [The API that does not break its callers](projects/04-the-api-that-does-not-break-its-callers.md)
- [The job that survives a restart](projects/05-the-job-that-survives-a-restart.md)
- [A link-rot watcher](projects/a-link-rot-watcher.md)
- [A public form](projects/a-public-form.md)

## Supporting material

- [Backend — five projects](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Databases and transactions](../02-databases/README.md).
