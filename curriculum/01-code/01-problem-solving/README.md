# AI-assisted code changes

Clarify a requirement, make a bounded change, and verify the result.

<section class="chapter-context" markdown="1">

## Start with a change small enough to explain

A customer sets a quantity to zero, but the application restores the old value. You will turn that symptom into a precise contract, inspect a proposed change, and explain what evidence supports the repair. AI can draft code, but it cannot decide the product’s missing rules for you.

Begin with the change loop, then use the zero-quantity exercise. You finish with a reviewable patch, a concrete input/output example, and a record of assumptions. No cloud account is needed.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

Start here; bring an editor and the ability to run the supplied examples.

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Make code changes reviewable and recoverable](change-loop.md) |
| 2 | [Specify and verify an AI-generated change](working-with-ai.md) |
| 3 | [Repair a quantity update that loses zero](ai-assisted-practice.md) |
| 4 | [Estimate request rates, storage, latency and availability](estimation-constants.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Testing and debugging](../../02-applications/04-testing/README.md).

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

- [Practice specification, AI review and independent evidence](ai-projects.md)
- [Practice reviewable changes and integration decisions](change-projects.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [APIs and background work](../../02-applications/01-backend/README.md).
