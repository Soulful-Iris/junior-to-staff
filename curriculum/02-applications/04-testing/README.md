# Testing, debugging, and code review

Reproduce a defect, build a check that catches it, and assess a proposed repair.

[Curriculum](../../README.md) · [About this part](../README.md)

## Before this chapter

[Frontend and full-stack integration](../03-frontend/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Learn in this order

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Testing](testing-strategy.md) |
| 2 | [Quantity investigation · zero is intentional](labs/quantity-debug/README.md) |
| 3 | [Transaction importer · diagnose another team's package](labs/importer/README.md) |
| 4 | [Three PRs before the finance release](labs/importer/review/README.md) |

## Go deeper on the same problem

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Backend and APIs](../01-backend/README.md) · [Databases and transactions](../02-databases/README.md).

## Apply the concept

Each link opens one existing project brief with its own context, diagrams, AI prompts, AWS choices and follow-ups.

- [The suite that can fail](projects/01-the-suite-that-can-fail.md)
- [The contract nobody breaks by accident](projects/02-the-contract-nobody-breaks-by-accident.md)
- [The flake hunter](projects/03-the-flake-hunter.md)
- [The load test that finds the real limit](projects/04-the-load-test-that-finds-the-real-limit.md)
- [The test that runs in production, forever](projects/05-the-test-that-runs-in-production-forever.md)

## Supporting material

- [Testing — five projects](projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Security](../05-security/README.md).
