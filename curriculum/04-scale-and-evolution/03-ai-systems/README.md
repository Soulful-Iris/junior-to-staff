# Build AI features with evidence and controlled actions

Design, implement, evaluate, and operate AI features with explicit permission, state, quality and task-budget boundaries.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Measure capacity and control performance costs](../02-performance-cost/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [AI systems](evaluation-and-budgets.md) |
| 2 | [May we ship a tagger that passes every regression?](labs/evaluations/README.md) |
| 3 | [Draft support replies without granting tool authority](problems/support-assistant.md) |
| 4 | [Serve recommendations with safe fallback ranking](problems/personalized-ranking.md) |
| 5 | [Build a document assistant with current permissions](problems/knowledge-assistant.md) |
| 6 | [Build and deploy the AI project workbench](aws-project-workbench.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Enforce identity, ownership and tenant boundaries](../../02-applications/05-security/README.md) · [Set reliability objectives and recover from failures](../../03-production/05-reliability/README.md).

## Build a project

Build in this order. The four new projects include working reference code, local sessions, AWS deployment instructions, expected results, six visuals each, failure tests, and engineer FAQs. They share the workbench introduced above.

1. [Build evidence-backed answers with permission rechecks](projects/01-evidence-desk.md)
2. [Require exact human approval before agent actions](projects/02-approval-desk.md)
3. [Route extracted invoices through validation and review](projects/03-invoice-review.md)
4. [Track AI evaluation evidence and serving versions](projects/04-release-evidence.md)

Then use the open-ended brief to design your own feature:

- [Decide whether an AI feature improves a reading list](projects/an-ai-feature-you-can-defend.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Migrate live systems and verify recovery](../04-migrations/README.md).
