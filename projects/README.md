# The five-project spine

One system, built five times over, each time under more pressure.

That is deliberate. Five unrelated toys teach you five beginnings and no
endings. The same system growing teaches you what a decision costs three months
later, which is the only way anyone learns to make them.

![The arc](../assets/the-arc.svg)

| | project | the question it answers | tier |
|---|---|---|---|
| [P1](p1-it-works/) | **it works** | can you build the thing at all? | junior |
| [P2](p2-it-survives/) | **it survives** | can someone else run it, and can you fix it at 3am? | junior → senior |
| [P3](p3-under-load/) | **it holds under load** | what happens when it is busy, and when a dependency dies? | senior |
| [P4](p4-it-reasons/) | **it reasons, provably** | can you add a model to it and prove it is any good? | senior |
| [P5](p5-it-changes/) | **it changes safely** | can you replace a load-bearing piece without stopping the world? | staff |

## What you are building

**A shared reading list.** People add links, tag them, mark them read, and see
what the group is reading. Small enough to finish, real enough to hurt.

It was picked for its failure modes, not its novelty:

- it has users and permissions, so authorisation is real
- it fetches URLs from the outside world, so it has an untrusted input and a slow dependency
- content arrives in bursts, so queues and backpressure are not hypothetical
- it accumulates text, so search, ranking and eventually a model all have something to work on
- it is boring, so nothing distracts from the engineering

You may substitute any system with those five properties. You may not substitute
one without them, because the later projects will have nothing to bite on.

## How a project works

Each page now starts with a constructed reviewer brief, exact sample behavior,
prerequisites, a baseline failure, and two changed-requirement diagrams with
reasoning kept behind disclosures. The retained build sequence has five parts:

1. **What done means** — the acceptance criteria, written before you start. Not "it feels finished."
2. **The decisions you are being asked to make** — the architecture points, stated as questions rather than answers, because the reasoning is the learning.
3. **Working with Claude on it** — what to ask for, in what order, and what to keep for yourself.
4. **How you would know it is wrong** — the checks. Run them. A check you never tried to make fail is not evidence.
5. **Break it on purpose** — the failures to induce deliberately, and what you should see when you do.

That last part is the one people skip, and it is where most of the learning is.
A system you have never seen fail is a system whose failure modes you are
guessing about.

## On using an AI for the code

On the AI-assisted path, direct implementation through the staged prompts and
verify every stopping point. On the interview path, attempt the brief and
follow-ups independently before revealing guidance; follow actual interview
tool rules. These pages are build briefs, not five supplied applications.

But there is a rule that runs through all five: **you must be able to say what
would make each piece wrong, before you accept it.** If you cannot, you have not
finished that slice, no matter what the screen shows. Every section gives you
the specific version of that question for its topic.

Passing reference tests checks supplied examples; it does not assess your
independent work. Use unfamiliar attempts and an independent reviewer to assess
transfer. A completed project is practice evidence, not a hiring prediction.

## The actual project inventory

There are **45 individually linked project briefs**: 25 section projects in five
selected sections, 15 act projects, and these five spine stages. The remaining
sixteen chapter directories have substantive lessons but no five-project set.
No language variant, hint, or follow-up is counted as another project.

| Collection | Briefs | Ordered index |
|---|---:|---|
| Change loop | 5 | [Section projects](../tiers/01-junior/01-the-change-loop/projects.md) |
| Working with AI | 5 | [Section projects](../tiers/01-junior/02-working-with-an-ai/projects.md) |
| Backend | 5 | [Section projects](../tiers/01-junior/04-backend/projects.md) |
| Testing | 5 | [Section projects](../tiers/01-junior/06-testing/projects.md) |
| Reliability | 5 | [Section projects](../tiers/02-senior/09-reliability/projects.md) |
| Act 1: junior | 5 | [Act projects](../acts/act-1-junior/README.md) |
| Act 2: senior | 5 | [Act projects](../acts/act-2-senior/README.md) |
| Act 3: staff | 5 | [Act projects](../acts/act-3-staff/README.md) |
| Continuous spine | 5 | P1–P5 in the table above |
