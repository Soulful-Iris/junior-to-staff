# Path A · AI-assisted engineering

Learn the concept, ask for a bounded implementation, then prove the result. The original 21 chapters and projects are this path's curriculum.

## Your first engineering conversation

> “A customer saves quantity zero, but the old value stays. An AI supplied the
> patch and passing tests. What should happen, what assumption is wrong, and
> what evidence would you require before accepting a repair?”

For this exercise, current `7` plus supplied `0` must save `0`; omitted quantity
keeps `7`; negative or null input is rejected. Agree on those examples first.
Then trace the request, name the invariant, ask for a small implementation,
inspect its diff, and make an intentionally broken version fail the same test.

Start with [the change loop](../../tiers/01-junior/01-the-change-loop/README.md)
and [working with AI](../../tiers/01-junior/02-working-with-an-ai/README.md).
Every chapter now opens with a concrete review problem. Project indexes let you
choose one independently readable brief, with follow-up diagrams and checks.

## Junior → senior → staff

| Stage | Reading route | Build | Exit demonstration |
|---|---|---|---|
| Junior | [01 change loop](../../tiers/01-junior/01-the-change-loop/) → [02 AI collaboration](../../tiers/01-junior/02-working-with-an-ai/) → [03 frontend](../../tiers/01-junior/03-frontend/) → [04 backend](../../tiers/01-junior/04-backend/) → [05 data](../../tiers/01-junior/05-data-and-databases/) → [06 tests](../../tiers/01-junior/06-testing/) → [07 shipping](../../tiers/01-junior/07-shipping-it/) | [P1](../../projects/p1-it-works/) and [P2](../../projects/p2-it-survives/) | Trace a request; reject a plausible but incorrect AI patch with a failing test |
| Senior | [08 design](../../tiers/02-senior/08-system-design/) → [09 reliability](../../tiers/02-senior/09-reliability/) → [10 observability](../../tiers/02-senior/10-observability/) → [11 security](../../tiers/02-senior/11-security/) → [12 delivery](../../tiers/02-senior/12-delivery/) → [13 scale](../../tiers/02-senior/13-data-at-scale/) → [14 performance](../../tiers/02-senior/14-performance-and-cost/) → [15 AI systems](../../tiers/02-senior/15-ai-systems/) | [P3](../../projects/p3-under-load/) and [P4](../../projects/p4-it-reasons/) | Explain measured overload and recovery, and judge an AI feature with a fixed evaluation set |
| Staff | [16 scope](../../tiers/03-staff/16-scope-and-leverage/) → [17 writing](../../tiers/03-staff/17-writing-that-decides/) → [18 strategy](../../tiers/03-staff/18-technical-strategy/) → [19 migrations](../../tiers/03-staff/19-migrations/) → [20 incidents](../../tiers/03-staff/20-risk-and-incidents/) → [21 enabling others](../../tiers/03-staff/21-making-others-faster/) | [P5](../../projects/p5-it-changes/) | Make a reversible cross-team decision and demonstrate a finished migration |

Prefer independent projects? Use the [three acts](../../acts/README.md). Use [the detailed workflow](../../docs/HOW-TO-USE.md) for acceptance criteria and prompting habits.

## Learn from the diagrams

The original diagrams remain the visual foundation. Follow moving requests, shrinking budgets, and multiplying retry branches. Use the [coding route](../interviews/coding/README.md) for focused algorithm animations and the [production casebook](../interviews/production/README.md) for AWS failure mechanisms.

[Choose a path](../README.md) · [Switch to interviews](../interviews/README.md)

## Apply the concepts to production failures

Use the [production casebook](../interviews/production/README.md) to review an AI-generated design against recent incident mechanisms. Ask for the invariant, failure injection, recovery behavior, and evidence before accepting a patch.
