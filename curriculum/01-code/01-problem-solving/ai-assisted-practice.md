# Repair a quantity update that loses zero

An inventory API accepts partial updates to a product. A missing quantity means keep the stored number, but an explicit zero means no stock remains. The supplied small example in the linked lab uses a truthiness fallback and therefore loses zero.

This is a focused review exercise. You will write the input/output contract, explain the failing expression, propose the smallest repair and demonstrate the real runtime inputs. You are not being asked to build a complete inventory service.

[Curriculum](../../README.md) · [AI-assisted code changes](README.md)

## Your starting input and finish line

Start from `current = 7` and send `{"quantity": 0}`. The broken expression returns 7. The repaired boundary must return 0, retain 7 when the field is omitted, and reject the invalid cases you explicitly choose. Keep invalid input from changing stored state.

Use the [quantity lab and its four-line starting function](../../02-applications/04-testing/labs/quantity-debug/README.md). Read the code first. Ask an assistant to explain the distinction between a missing property, null and zero, then compare that explanation with the language behavior. Hand over the patch and a small transcript of the agreed cases, including any outcome that remains unsupported.

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
