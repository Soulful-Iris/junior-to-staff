# AI systems

Design, implement, evaluate, and operate AI features with explicit permission, state, quality and task-budget boundaries.

[Curriculum](../../README.md) · [About this part](../README.md)

## Before this chapter

[Performance and cost](../02-performance-cost/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Learn in this order

| Step | Existing lesson or exercise |
|---|---|
| 1 | [AI systems](evaluation-and-budgets.md) |
| 2 | [May we ship a tagger that passes every regression?](labs/evaluations/README.md) |
| 3 | [Support assistant](problems/support-assistant.md) |
| 4 | [Personalized ranking: low latency and evidence of quality](problems/personalized-ranking.md) |
| 5 | [Knowledge assistant: the citation that lost access](problems/knowledge-assistant.md) |
| 6 | [Build and deploy the AI project workbench](aws-project-workbench.md) |

## Go deeper on the same problem

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Security](../../02-applications/05-security/README.md) · [Reliability and incident response](../../03-production/05-reliability/README.md).

## Apply the concept

Build in this order. The four new projects include working reference code, local sessions, AWS deployment instructions, expected results, six visuals each, failure tests, and engineer FAQs. They share the workbench introduced above.

1. [Evidence desk: a document assistant with citations and revocation](projects/01-evidence-desk.md)
2. [Approval desk: a support agent that proposes before it acts](projects/02-approval-desk.md)
3. [Invoice review: extract, validate, retry, and reconcile](projects/03-invoice-review.md)
4. [Release evidence: evaluate a candidate, promote it, and roll back](projects/04-release-evidence.md)

Then use the open-ended brief to design your own feature:

- [An AI feature you can defend](projects/an-ai-feature-you-can-defend.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Migrations and recovery](../04-migrations/README.md).
