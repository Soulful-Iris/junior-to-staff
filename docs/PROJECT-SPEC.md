# How the projects are written

Internal spec, 2026-09-21. Bruno's words, which set all of this:

> *"5 well thoughout projects PER section. And maybe 5 projects after an ACT
> (group of sections)... Its important to know that the coding isnt the most
> important thing but the thought process and ways of organiZing prompts. Things
> to have in mind. Productionize real world thoughts and actions."*

> *"This doc has to be as real life as possible. You know I have AWS access. So
> including these things and services and which services to go to for each
> architecture with explanations and hows is VERY VERY important."*

> *"Animations should be everywhere to help understand and visualize lessons."*

The original request above is historical context. The current supplied inventory
is 25 section projects, 15 act projects, and five spine projects. Sixteen other
chapter directories do not claim five supplied section projects. Each project
now lives on its own page, under the [shared teaching standard](LEARNING-EXPERIENCE.md).

## Three levels, and they do different jobs

| level | where | how many | scale |
|---|---|---|---|
| **section projects** | `tiers/<tier>/<section>/projects/<project>.md`, linked by `projects.md` | 25 supplied across five sections | One section's skill, isolated. |
| **act projects** | `acts/act-<n>-<tier>/projects/<project>.md`, linked by act README | 5 per act, 15 total | Integrates the whole tier. Pick one of five. |
| **the spine** | `projects/` | 5 total | the whole guide. One system growing, for anyone who prefers continuity to variety. |

An "act" is a tier. His word, and it is the better one: a tier is a rank, an act
is a stretch of work with a shape.

## The shape of a section project

Seven parts, these headings, in this order. Target 350-550 words each.

### `### <n>. <name>`
One line under it in italics: what you end up with, concretely.

### `**Build**`
Two or three sentences. What exists when you are done. No feature lists.

### `**The thought process**`
**This is the part that matters and the part every other guide omits.** Not the
steps — the *decisions*, in the order you have to make them, and what you are
weighing in each. Write it as the reasoning someone would narrate out loud:
"first you have to decide X, because until you have, Y is unanswerable."

If this section reads like a tutorial, rewrite it.

### `**How to organise the prompts**`
The literal sequence of asks, numbered, each as a fenced block. Not one big
prompt — the *order*, with a sentence after each saying what that ask is for
and what you check before moving on.

Bruno asked for this explicitly and it is the closest thing this guide has to a
differentiator. The rule: **each ask ends somewhere you can check.** A sequence
where step three cannot be verified before step four is a sequence that has
delegated your judgment.

### `**On AWS**`
Name the services. Say **why that one and not the obvious neighbour**, and
sketch the how in three or four lines. The comparison is the teaching: Lambda
versus Fargate versus EC2, SQS versus EventBridge versus Kinesis, RDS versus
DynamoDB versus Aurora Serverless. Include the free-tier or near-free option
where one exists, because the reader has an account and a bill.

No prices unless you checked them this session and say when.

### `**What productionising it means**`
The gap between the thing that works and the thing you could leave running.
Specific: what fails at 3am, what costs money while you sleep, what a second
person needs to run it, what happens when the input is hostile.

### `**The learning**`
Two or three sentences. The thing that stays with you when the code is deleted.
If it is generic ("learn about queues") it is not the learning — the learning is
what you now believe that you did not before.

### `**How you would know it is wrong**`
Three to five checks that can actually go red. Same standard as the sections.

## The shape of an act project

Same seven parts, bigger, 700-1,100 words, plus two more:

### `**The architecture**`
A diagram, in the house style, of the thing being built. This is the "how the
project should look" he asked for. Show the pieces, what moves between them,
and where it can fail.

### `**Stage it**`
The build order, in three or four stages, each of which leaves something
runnable. An act project you cannot stop halfway through is a project people
abandon at 60%.

## Animations

He asked twice, and he is right that they carry things a static picture cannot.
Use motion **only where time is part of the lesson** — a request travelling, a
queue filling and draining, a rollout stepping 1% to 10% to everyone, retries
multiplying, a cache going cold. Plain SMIL inside the SVG (`<animate>`,
`<animateMotion>`); no scripts, no external libraries.

Two hard rules:

1. **It must read correctly frozen on the first frame.** GitHub previews, PDF
   exports and a paused tab all show frame one.
2. **A loop must return to its start** so it does not jump.

## House visual style, non-negotiable

- first element `<rect width="W" height="H" rx="10" fill="#faf9f7"/>`; `viewBox` and `width`/`height` both set
- ink `#1f2b24` and `#3f3b36`; muted `#6d6459` and `#8a857d`; rules `#ded9d1` and `#c9c3b8`
- accent green `#2f6f4e`, tint `#eef2ef`; warm accent `#c2703d` / `#a85d2f` for cost, danger and failure only
- `ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif` for prose; `ui-monospace, SFMono-Regular, Menlo, monospace` for small-caps labels
- under 780px wide, no external fonts, no raster images, no scripts
- **text must not overflow its shape or sit on a line.** A 12px sans character
  is roughly 6.5px wide, and that estimate has been optimistic twice — count,
  then render it and look.

## The rule that applies to all of it

Every diagram gets rendered in chromium and **looked at** before it is
committed. Of the first twenty in this repo, about half had a defect visible
only in the picture: a dot near a curve rather than on it, a label clipped at
the canvas edge, an annotation lying across the line it pointed at, light text
crossing onto a light background mid-sentence.

None of that is findable by reading the file.
