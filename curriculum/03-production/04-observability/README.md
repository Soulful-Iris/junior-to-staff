# Trace requests and diagnose production symptoms

Use logs, metrics, and traces to answer a concrete system question.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Provision and operate application infrastructure on AWS](../03-infrastructure/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Observability](logs-metrics-traces.md) |
| 2 | [Find database-pool waiting in slow API requests](problems/slow-request.md) |
| 3 | [Ingest and query metrics with bounded cardinality](problems/metrics-platform.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Set reliability objectives and recover from failures](../05-reliability/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Diagnose a reading-list incident from existing telemetry](projects/debuggable-at-three-in-the-morning.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Set reliability objectives and recover from failures](../05-reliability/README.md).
