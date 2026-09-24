# Find defects and evaluate engineering evidence

Reproduce a defect, build a check that catches it, and assess a proposed repair.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Connect a usable interface to an API](../03-frontend/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Testing](testing-strategy.md) |
| 2 | [Quantity investigation · zero is intentional](labs/quantity-debug/README.md) |
| 3 | [Transaction importer · diagnose another team's package](labs/importer/README.md) |
| 4 | [Three PRs before the finance release](labs/importer/review/README.md) |

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

- [Testing — five projects](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Enforce identity, ownership and tenant boundaries](../05-security/README.md).
