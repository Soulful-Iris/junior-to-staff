# Path A · AI-assisted engineering

Learn the concept, ask for a bounded implementation, then prove the result. The original 21 chapters and projects are this path's curriculum.

## Junior → senior → staff

| Stage | Reading route | Build | Exit demonstration |
|---|---|---|---|
| Junior | [01 change loop](../../tiers/01-junior/01-the-change-loop/) → [02 AI collaboration](../../tiers/01-junior/02-working-with-an-ai/) → [03 frontend](../../tiers/01-junior/03-frontend/) → [04 backend](../../tiers/01-junior/04-backend/) → [05 data](../../tiers/01-junior/05-data-and-databases/) → [06 tests](../../tiers/01-junior/06-testing/) → [07 shipping](../../tiers/01-junior/07-shipping-it/) | [P1](../../projects/p1-it-works/) and [P2](../../projects/p2-it-survives/) | Trace a request; reject a plausible but incorrect AI patch with a failing test |
| Senior | [08 design](../../tiers/02-senior/08-system-design/) → [09 reliability](../../tiers/02-senior/09-reliability/) → [10 observability](../../tiers/02-senior/10-observability/) → [11 security](../../tiers/02-senior/11-security/) → [12 delivery](../../tiers/02-senior/12-delivery/) → [13 scale](../../tiers/02-senior/13-data-at-scale/) → [14 performance](../../tiers/02-senior/14-performance-and-cost/) → [15 AI systems](../../tiers/02-senior/15-ai-systems/) | [P3](../../projects/p3-under-load/) and [P4](../../projects/p4-it-reasons/) | Explain measured overload and recovery, and judge an AI feature with a fixed evaluation set |
| Staff | [16 scope](../../tiers/03-staff/16-scope-and-leverage/) → [17 writing](../../tiers/03-staff/17-writing-that-decides/) → [18 strategy](../../tiers/03-staff/18-technical-strategy/) → [19 migrations](../../tiers/03-staff/19-migrations/) → [20 incidents](../../tiers/03-staff/20-risk-and-incidents/) → [21 enabling others](../../tiers/03-staff/21-making-others-faster/) | [P5](../../projects/p5-it-changes/) | Make a reversible cross-team decision and demonstrate a finished migration |

Prefer independent projects? Use the [three acts](../../acts/README.md). Use [the detailed workflow](../../docs/HOW-TO-USE.md) for acceptance criteria and prompting habits.

## Use the new visuals actively

Each chapter now has a before/after animation, an implementation sequence, and a still storyboard. Watch once, hide it, and reconstruct the state transitions. The animated highlights represent event order; they are not measured performance or simulations of AWS internals.

Ask an assistant: “Use the chapter's invariant. Give me a small implementation with one deliberately broken variant and a test that distinguishes them. Do not reveal the bug until I have predicted the result.” You still own the prediction and the review.

[Choose a path](../README.md) · [Switch to interviews](../interviews/README.md)
