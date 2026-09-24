# Technical decisions and engineering effectiveness

Make options, ownership, adoption, and cross-team decisions explicit.

<section class="chapter-context" markdown="1">

## Make decisions another engineer can use

Several teams interpret the same amount field in different units. One person is required for every deploy. A migration has no owner for retiring the old path. These problems require decisions and adoption work beyond another local code change.

Write a decision record with options and consequences, find the actual delivery bottleneck, and define a strategy through observable rules. Your output should let another team act without needing you to repeat the explanation.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Live migrations](../04-migrations/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Choose the scope that removes repeated engineering work](scope-and-leverage.md) |
| 2 | [Write a design document that supports a decision](design-documents.md) |
| 3 | [Turn recurring constraints into a usable technical strategy](technical-strategy.md) |
| 4 | [Find delivery bottlenecks and reduce dependency on one engineer](engineering-effectiveness.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [System design under constraints](../../03-production/01-system-design/README.md) · [Live migrations](../04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Build a service template with overridable defaults](projects/the-paved-road.md)
- [Write a data-platform policy from concrete decisions](projects/the-strategy-you-found-rather-than-invented.md)
- [Compare a small export script with a custom platform](projects/the-thing-you-decided-not-to-build.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Optional specialization: [AI evaluation and guardrails](../03-ai-systems/README.md).
