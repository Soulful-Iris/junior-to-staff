# How this guide is written

This is the internal spec for the original AI-assisted engineering chapters.
The interview path uses [its teaching standard](../paths/interviews/TEACHING.md),
which includes concept instruction, code, and timed independent practice.
Both paths keep the rules on clarity, verification, and self-contained teaching.

## Who the reader is

Someone who can already make a computer do something, who is going to build most
of the code by directing an AI, and who needs to be able to **judge what comes
back**. They are not learning syntax. They are learning what to ask for, what
good looks like, and how to tell when they have been handed something that looks
right and is not.

Write for that person. Not for a bootcamp graduate, not for an interviewer, and
never for another engineer you are trying to impress.

## The shape of a section

Eight parts, in this order, with these headings. No section skips one.

### 1. `## The one-liner`
Two or three sentences. What this section buys you, in words the reader already
owns. If you cannot say it without jargon, you do not understand it yet.

### 2. `## The failure it prevents`
A concrete story of what goes wrong without this. A real shape of failure — the
deploy that took the site down at 2am, the query that was fine on 1,000 rows and
died on 2,000,000. Specific beats general. This is the part that makes someone
read the rest.

### 3. `## The mental model`
The actual idea, 300-600 words, **with a diagram**. Not a list of technologies.
The model is the thing that survives when the tools change: what moves, what
waits, what can fail, where state lives.

### 4. `## What good looks like`
A short checklist of properties, each one observable. Then the same list
inverted — what you see when it is done badly. The reader should be able to open
a codebase and place it on that scale.

### 5. `## Ask Claude for this`
The differentiator, and the reason this guide exists. Two or three worked
requests:

- **What to ask for** — the actual words, as a block. A specification, not a wish.
- **Why you are asking for it that way** — which constraint in the ask does the work.
- **What you should get back** — so a wrong answer is recognisable.
- **What to push back on** — the plausible-looking thing that is a mistake here.

A prompt that only works if you already knew the answer is not a teaching prompt.
Write ones that hold when the reader does not.

### 6. `## How you would know it is wrong`
Every section has one. The specific checks for THIS topic that can actually go
red: what to measure, what the number should be, what result would mean the thing
is broken. Name at least one check that would fail if the implementation were
subtly wrong rather than obviously broken.

The rule underneath it, which holds everywhere: **a check that cannot fail is not
a check.** Before believing a green result, say what it would have looked like if
the thing were broken. If the answer is "the same", it proved nothing.

### 7. `## Your slice of the project`
What the reader adds to the running project in this section. Concrete deliverable,
with acceptance criteria they can check themselves. It must build on what they
already have rather than starting a new toy.

### 8. `## Words you now own`
Six to twelve terms, one line each, in plain language. The point is to be able to
talk to engineers without bluffing.

## Rules

**Self-contained.** Links are a bonus, never load-bearing. If a link died
tomorrow the section still teaches. Never write "see the docs" as the
explanation.

**Diagrams earn their place.** Every section has at least one. Use mermaid for
structure (it renders natively on GitHub and stays editable); use a committed SVG
when the thing genuinely moves. A diagram that only restates the paragraph above
it is decoration — cut it.

**No unverified version numbers.** If you name a version, a price, or a limit,
you checked it this session and you say when. Anything you could not verify gets
said as "as of <date>, unverified" or left out. A number nobody checked is worse
than no number, because people trust tables.

**No hype.** No "production-ready" unless you say what would make it not. No
"best practice" without saying who decided and what the tradeoff costs. If
something is contested, say it is contested and give both sides in a sentence
each.

**Say what you are not covering.** A section that pretends to be complete teaches
someone they are finished when they are not.

**Register.** Plain, direct, a little dry. Short sentences carry the load.
Contractions are fine. No exclamation marks, no emoji in prose, no "let's dive
in". Assume intelligence, not knowledge.

## What this guide refuses to be

A link farm. A list of 115 demo scripts. A roadmap image with no teaching under
it. A repo where the newest folder is maintained and the other hundred are two
years stale.

The test for any page: **would this still be worth reading if every external link
in it were dead?** If not, rewrite it.
