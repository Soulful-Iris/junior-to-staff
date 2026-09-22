# Practice an AI-assisted change

[Curriculum](../../README.md) · [Problem solving and AI-assisted engineering](README.md)

## Your first engineering conversation

> “A customer saves quantity zero, but the old value stays. An AI supplied the
> patch and passing tests. What should happen, what assumption is wrong, and
> what evidence would you require before accepting a repair?”

For this exercise, current `7` plus supplied `0` must save `0`; omitted quantity
keeps `7`; negative or null input is rejected. Agree on those examples first.
Then trace the request, name the invariant, ask for a small implementation,
inspect its diff, and make an intentionally broken version fail the same test.

Start with [the change loop](change-loop.md)
and [working with AI](working-with-ai.md).
Every chapter now opens with a concrete review problem. Project indexes let you
choose one independently readable brief, with follow-up diagrams and checks.

## Learn from the diagrams

The original diagrams remain the visual foundation. Follow moving requests, shrinking budgets, and multiplying retry branches. Use the [coding route](../02-data-structures-algorithms/practice-sequence.md) for focused algorithm animations and the [production casebook](../../../indexes/production-cases.md) for AWS failure mechanisms.


## Apply the concepts to production failures

Use the [production casebook](../../../indexes/production-cases.md) to review an AI-generated design against recent incident mechanisms. Ask for the invariant, failure injection, recovery behavior, and evidence before accepting a patch.
