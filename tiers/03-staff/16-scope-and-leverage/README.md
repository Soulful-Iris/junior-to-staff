# 16 · Scope and leverage

> Staff tier · feeds **P5 (it changes safely)**

## The one-liner

Staff is not senior with more years on it. It is a different job, and the change
is in **scope**: from one team over a quarter to several teams over years, and
from being the person who solves the problem to being the person who decides
which problem gets solved. The uncomfortable part is that the skill that got you
here — writing excellent code fast — stops being the thing you are measured on.

## The failure it prevents

The common way this goes wrong is not failure. It is a very good senior engineer
doing very good senior work for three more years and quietly wondering why
nothing changes.

They ship more than anyone. They are the person you want on a hard bug. They are
also picking up whatever lands in front of them, and every one of those choices
is locally correct, and the sum is a career that plateaus with excellent
reviews. Meanwhile somebody with less raw ability wrote the document that
decided what the team would spend the next year on.

That is not a story about politics. It is a story about **leverage**: the
difference between doing the work and changing what work gets done.

## The mental model

Every published engineering ladder draws the same line in slightly different
words. Dropbox's framework describes its staff level as delivering multi-year,
multi-team product or platform goals, and expects org-optimal decisions over
locally optimal ones. Etsy's talks about directing solutions to significantly
complex, *unscoped* problems. CircleCI splits its levels explicitly: the first
three are about becoming a highly effective individual contributor, the next
three about using those skills to create leverage across larger groups.

The detail worth pausing on, because it is counterintuitive and it is stated in
the framework rather than inferred: **Dropbox's code-fluency expectations stop
rising at the senior level.** Growth past senior is direction, talent and
culture. You are not expected to code better. You are expected to code as a
means.

*(Read from the published ladders on 2026-09-21. Every company words this
differently; the shape is remarkably consistent.)*

### What the job actually contains

The StaffEng project surveyed around thirty staff engineers and their work
sorted into five buckets:

1. **Setting technical direction** — deciding what gets built and on what.
2. **Mentorship, and separately sponsorship.** These are not the same and the
   second one costs you something. Mentorship is advice. Sponsorship is spending
   your own credibility to put someone in a room, on a project, or in a promotion
   packet. Most guides say "mentor more". The ladders reward the other one.
3. **Being in the room** — getting into the conversations where decisions are
   made, and being useful once there rather than merely present.
4. **Exploring ambiguity** — the problems normal process cannot digest because
   nobody can say what they are yet.
5. **Glue work** — the coordination, unblocking and quiet repair that makes a
   group function.

### The four archetypes

Staff is at least four different jobs, and which one exists depends on the
company rather than on you.

![The four staff archetypes positioned by organisation size and by whether their scope is one team cluster or the whole organisation](../../../assets/diagrams/staff-archetypes.svg)

- **Tech Lead** — guides one team or a small cluster. The commonest by far.
- **Architect** — owns a domain such as APIs or infrastructure. Requires intimate business and user context; the version that sits above the business is the failure mode, not the ideal.
- **Solver** — pointed at one critical problem after another. Common where planning centres on individuals. Carries a transience risk: you are never anywhere long enough to be missed.
- **Right Hand** — extends a senior leader's attention and borrows their authority. Only exists at real scale.

Choosing the wrong archetype for your organisation is a named failure mode. An
architect role at a forty-person company is a title with no work under it.



## What good looks like

- You can name the three problems your organisation will regret not solving, and say which one you are on.
- Your work has a written form other people can act on without you in the room.
- Somebody else got a better job because you spent credibility on them.
- You say no to work that is beneath your leverage, and you say it in a way that leaves the work getting done by somebody for whom it is growth.
- You are in the meeting where the decision happens, and you speak about the thing rather than about the technology.

Done badly — and StaffEng names these, which is why they are worth quoting:

- **Snacking.** Picking easy, satisfying, low-impact work because it feels productive. This is the trap for exactly the people who are good at the work.
- **Preening.** Visible, low-impact work. The demo that impresses and changes nothing.
- **Chasing ghosts.** Imposing the solution from your last company onto a problem that is not the same problem.
- **Glue work without the title.** Tanya Reilly's finding, and it is uncomfortable: the person who coordinates, mentors and prevents outages is frequently told they lack technical contribution. The work is necessary, it is undervalued, and women do measurably more of it. Do it visibly and credited as leading, or do less of it.

## Ask Claude for this

The model cannot do your politics. It is very good at the two things that block
most people: making a vague idea specific, and arguing against you honestly.

**Request 1 — turn a feeling into a scoped problem**

```
I think <the thing you believe is wrong> is the biggest technical problem
facing us. Interrogate that.

Ask me the five questions you would need answered to know whether it is
real, whether it is the biggest, and whether it is solvable in a year.
Do not offer solutions yet.
```

*Why:* staff work starts as an instinct, and an instinct handed to an executive
gets dismissed. Making yourself answer five specific questions is the cheapest
version of the work you would otherwise do badly in public.

*What you should get back:* questions about evidence, cost, who else is
affected, and what happens if nothing is done. If it starts proposing an
architecture, tell it to stop and answer again.

**Request 2 — steelman the thing you rejected**

```
Here is the design I am proposing and the alternative I rejected.

Make the strongest possible case for the alternative. Assume the person
arguing for it is smarter than me and knows something I do not. What
would they know?
```

*Why:* the "alternatives considered" section of a design doc is where its
credibility lives, and a weak steelman is visible from space. If you cannot
argue the other side better than its advocates, you have not finished deciding.

*Push back on:* a polite, balanced comparison. You asked for an argument, not a
table.

**Request 3 — find who disagrees before they find you**

```
Here is my proposal. List the teams or roles whose work it makes harder,
what they lose, and the objection each would raise in review.

Rank them by how likely that objection is to stop this.
```

*Why:* the disagreement surfaced in review is a cheap early warning that the
project itself will slip. Finding it a week before the review, and going to
those people first, is most of what "being in the room" actually means.

## How you would know it is wrong

Staff work has long feedback loops, which is precisely why it needs deliberate
checks rather than a feeling of productivity.

1. **Count what you did last quarter and ask what would have happened without you.** If the honest answer is "somebody else would have done it a bit slower", that is senior work, done well.
2. **Look for your name on something you did not attend.** A document being used in a meeting you are not in is leverage. Being needed in every meeting is the opposite.
3. **Ask whether you can point at a person whose situation you changed.** Sponsorship leaves a trace: a promotion, a project, a role.
4. **Check the snacking ratio.** Of the last ten things you worked on, how many were chosen because they were satisfying? There is no correct number, but if it is ten, you know.
5. **Test the archetype against the org, not your preference.** If you are trying to be an architect in a company that has no such role, the absence of progress is structural rather than personal.
6. **Have somebody who will tell you no.** Long feedback loops plus a deferential team is how people spend two years on the wrong thing while everyone is polite about it.

## Your slice of the project

For **P5**, before any code:

- Write down the three problems your system will have in a year, and rank them. Not the bugs. The structural ones.
- Pick one, and write the one-page version of why it matters, what it costs to fix, and what happens if nobody does.
- Identify who would object, and what they lose.

**Acceptance criteria:** somebody who did not build this system can read your
one page and tell you back what the problem is and why it is worth a quarter. If
they cannot, the page is not finished — and it is the page that is wrong, not
the reader.

## Words you now own

- **leverage** — the ratio between what changes and how much of you it took.
- **scope** — how far your decisions reach, in teams and in time.
- **sponsorship** — spending your credibility on someone else's opportunity. Distinct from, and costlier than, mentorship.
- **archetype** — the shape a staff role takes in a given organisation: tech lead, architect, solver, right hand.
- **snacking** — easy, satisfying, low-impact work.
- **preening** — visible, low-impact work.
- **chasing ghosts** — importing your last company's solution to a problem that is not the same.
- **glue work** — the coordination and repair that makes a group function; necessary, chronically uncredited.
- **org-optimal** — the choice that is best for the organisation even when it is worse for your team. The staff tiebreak.
- **unscoped problem** — one where nobody can yet say what the work is. Defining it *is* the work.

---

**Not covered here:** the artefacts themselves — design docs, RFCs, strategy —
are **17 · Writing that decides** and **18 · Technical strategy**. Promotion
mechanics are real and are deliberately not the organising idea of this tier; if
you do the work in this section, the packet writes itself, and if you optimise
for the packet you will end up preening.

[Choose your learning path](../../../paths/README.md) · [Interview applications](../../../paths/interviews/README.md)
