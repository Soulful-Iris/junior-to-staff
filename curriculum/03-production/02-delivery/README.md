# Deploy changes and control feature exposure

Build once, verify compatibility, and release a change with stop conditions.

<section class="chapter-context" markdown="1">

## Keep mixed versions compatible while releasing a change

An old server writes `email`, while a new server expects `contact_email`. They share a database during rollout. Returning to the old application artifact does not undo rows already changed by the new version.

Plan expansion, compatible readers and writers, backfill, exposure, and retirement. Use the configuration case to study a rollout that is syntactically valid but unusable. You finish with a sequence and recovery boundary, not just a successful deployment command.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Design services from requirements to failure behavior](../01-system-design/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Deploy compatible versions and control feature exposure](delivery-pipeline.md) |
| 2 | [Roll out routing configuration without activating unusable backends](cases/configuration-rollout.md) |
| 3 | [Release invoice changes with stable cohorts and rollback](problems/feature-rollout.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Provision and operate application infrastructure on AWS](../03-infrastructure/README.md) · [Trace requests and diagnose production symptoms](../04-observability/README.md) · [Migrate live systems and verify recovery](../../04-scale-and-evolution/04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Deploy from main and roll back compatible artifacts](projects/twenty-deploys-a-day.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Provision and operate application infrastructure on AWS](../03-infrastructure/README.md).
