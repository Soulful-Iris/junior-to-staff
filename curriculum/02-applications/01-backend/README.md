# APIs and background work

Trace a request, define its contract, and coordinate bounded work.

<section class="chapter-context" markdown="1">

## Follow one save from HTTP input to durable data

A research team saves links in a shared reading list. The API accepts a URL, records it, and may attempt to obtain a display title. The URL can be safely saved even when that optional lookup fails. The later lessons introduce concurrent work, deadlines, tracing, and durable jobs around this interaction.

Start with the supplied local HTTP/SQLite API. Each project tells you which behavior is already implemented and which boundary you will add. AWS diagrams describe deployment responsibilities, while local commands remain the first runnable step.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Data structures and algorithms](../../01-code/02-data-structures-algorithms/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Follow an HTTP request from validation to durable state](request-lifecycle.md) |
| 2 | [Validate provider responses before returning an API result](labs/api-contract/README.md) |
| 3 | [Distinguish I/O overlap from parallel CPU execution](labs/bounded-executor/runtime.md) |
| 4 | [Fetch a bounded batch while preserving order and partial results](labs/fan-out/README.md) |
| 5 | [Bounded blocking queue with shutdown](problems/42-bounded-blocking-queue/README.md) |
| 6 | [Bound accepted work and make executor shutdown predictable](labs/bounded-executor/README.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Data models and transactions](../02-databases/README.md) · [Identity and authorization](../05-security/README.md) · [Reliability and incident recovery](../../03-production/05-reliability/README.md).

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

- [Choose a backend project: tracing, deadlines, fetching, contracts or jobs](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Data models and transactions](../02-databases/README.md).
