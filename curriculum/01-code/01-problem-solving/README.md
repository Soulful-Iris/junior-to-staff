# Specify, implement and review changes with AI

Clarify a requirement, make a bounded change, and verify the result.

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

Start here; bring an editor and the ability to run the supplied examples.

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [The change loop](change-loop.md) |
| 2 | [Working with an AI that writes the code](working-with-ai.md) |
| 3 | [Practice an AI-assisted change](ai-assisted-practice.md) |
| 4 | [The constants you estimate with](estimation-constants.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Find defects and evaluate engineering evidence](../../02-applications/04-testing/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Specify tag behavior for independent implementers](projects/ai-assisted/01-the-spec-that-survives-a-stranger.md)
- [Evaluate generated rate-limiter code with a simple reference](projects/ai-assisted/02-the-verification-you-could-not-have-written-yourself.md)
- [Build reusable AI instructions and evaluate transfer](projects/ai-assisted/03-the-prompt-library.md)
- [Collect evidence about changed behavior and affected callers](projects/ai-assisted/04-the-review-harness.md)
- [Record and revisit uncertain engineering decisions](projects/ai-assisted/05-the-honest-log.md)
- [Rewrite private commit history to explain a change](projects/change-loop/01-the-history-a-stranger-can-debug-from.md)
- [Split a tagging feature into runnable changes](projects/change-loop/02-the-change-small-enough-to-judge.md)
- [Demonstrate CI enforcement in a disposable repository](projects/change-loop/03-the-pipeline-that-can-refuse.md)
- [Automate deterministic review rules and retain human judgment](projects/change-loop/04-the-review-you-automate-away.md)
- [Check the combined behavior of independently valid changes](projects/change-loop/05-two-greens-that-make-a-red.md)

## Reference guides

- [Working with an AI that writes the code — five projects](ai-projects.md)
- [The change loop — five projects](change-projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Choose data structures and reason about algorithms](../02-data-structures-algorithms/README.md).
