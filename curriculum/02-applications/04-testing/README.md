# Find defects and evaluate engineering evidence

Reproduce a defect, build a check that catches it, and assess a proposed repair.

<section class="chapter-context" markdown="1">

## Find evidence that distinguishes a repair from a passing result

A quantity update reports success while losing zero. A transaction importer returns healthy HTTP responses while storing the wrong cents or skipping a page after restart. You will use the required behavior to decide what evidence can reveal those defects.

Start with the small quantity bug, then investigate the supplied multi-module importer and review three proposed patches. The learning exercises discuss checks for application behavior. They do not change this guide’s automatic publishing workflow.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Connect a usable interface to an API](../03-frontend/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Choose checks that reveal the behavior a change can break](testing-strategy.md) |
| 2 | [Preserve zero when applying a quantity update](labs/quantity-debug/README.md) |
| 3 | [Repair decimal amounts and restart recovery in a transaction importer](labs/importer/README.md) |
| 4 | [Review three importer patches against data and retry contracts](labs/importer/review/README.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Build HTTP APIs and reliable background work](../01-backend/README.md) · [Model data and enforce transactional rules](../02-databases/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Measure whether existing checks detect real defects](projects/01-the-suite-that-can-fail.md)
- [Protect API response types, units and compatibility](projects/02-the-contract-nobody-breaks-by-accident.md)
- [Reproduce and remove order-dependent failures](projects/03-the-flake-hunter.md)
- [Measure API capacity with controlled arrival rates](projects/04-the-load-test-that-finds-the-real-limit.md)
- [Design and run a synthetic reading-list journey](projects/05-the-test-that-runs-in-production-forever.md)

## Reference guides

- [Choose an evidence exercise: defects, contracts, load or user journeys](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Enforce identity, ownership and tenant boundaries](../05-security/README.md).
