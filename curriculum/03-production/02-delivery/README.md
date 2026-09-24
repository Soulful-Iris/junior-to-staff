# Deploy changes and control feature exposure

Build once, verify compatibility, and release a change with stop conditions.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Design services from requirements to failure behavior](../01-system-design/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Delivery](delivery-pipeline.md) |
| 2 | [Configuration is executable behavior](cases/configuration-rollout.md) |
| 3 | [Release invoice changes with stable cohorts and rollback](problems/feature-rollout.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Provision and operate application infrastructure on AWS](../03-infrastructure/README.md) · [Trace requests and diagnose production symptoms](../04-observability/README.md) · [Migrate live systems and verify recovery](../../04-scale-and-evolution/04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Deploy from main and roll back compatible artifacts](projects/twenty-deploys-a-day.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Provision and operate application infrastructure on AWS](../03-infrastructure/README.md).
