# junior → staff

An end-to-end guide to being a software engineer, for someone who will build
most of the code by directing an AI and needs to be able to **judge what comes
back**.

![The arc: three tiers and five projects, rising in complexity](assets/the-arc.svg)

Three tiers. Five projects. The same system growing the whole way, rather than
five unrelated toys.

---

## Why this exists

Most roadmap repos are a list of things to learn with links attached. They go
stale, nobody finishes them, and they teach the names of technologies rather
than the judgment that decides between them.

This one is built on a different bet: **the part of engineering that does not
get automated is knowing what to ask for, what good looks like, and how to tell
when you have been handed something that is plausible and wrong.** So every
section here carries four things a roadmap does not:

- the **failure it prevents**, concretely
- what to **ask Claude for**, in words, and why the ask is shaped that way
- **how you would know it is wrong** — checks that can actually go red
- a **slice of the running project**, with acceptance criteria you can check yourself

If every external link in this repo died tomorrow, it would still teach. That is
the standard it is written to. See [docs/STYLE.md](docs/STYLE.md) for the rules
every section follows.

---

## How to use it

1. **Read a section.** They are written to be read, not skimmed.
2. **Build the slice.** Each section adds one thing to the project you already
   have. Use Claude for it; the section tells you what to ask.
3. **Run the checks.** Every section has a "how you would know it is wrong".
   Actually run them. A green result you never tried to make go red is not
   evidence of anything.
4. **Move on when the acceptance criteria pass**, not when you feel finished.

You do not have to do the tiers in order if you already work at that level. You
do have to do the projects in order — each one is the previous one under more
pressure.

Longer version: [docs/HOW-TO-USE.md](docs/HOW-TO-USE.md).

---

## The five projects

| | project | what it proves you can do |
|---|---|---|
| **P1** | it works | ship a small full-stack thing with auth, data and tests that bite |
| **P2** | it survives | the same system with CI/CD, infrastructure as code, backups and enough observability to debug it at 3am |
| **P3** | it holds under load | queues, caching, idempotency and rate limits, then break it on purpose and measure what happens |
| **P4** | it reasons, provably | an AI feature with a real evaluation harness, guardrails, and a cost and latency budget |
| **P5** | it changes safely | a migration of the system you built, with a design doc, a rollout plan, kill criteria and a written postmortem |

Each project has its own brief in [projects/](projects/) with scope, acceptance
criteria, the architecture decisions you are being asked to make, and the
failures you should deliberately induce.

---

## The tiers

### Junior — build a thing that works

You can take a requirement and produce something that runs, and you can tell
whether it runs.

### Senior — build a thing that survives

You can build something that keeps working when it is under load, when a
dependency fails, when somebody else changes it, and at three in the morning
when you are asleep.

### Staff — change what gets built

Your leverage stops being the code you write. It becomes the decisions you make
and the other engineers you make faster. This tier is about scope, strategy,
migrations, risk, and knowing when the answer is not to build the thing.

*(The section list is being filled in. What is here is real; what is not here
yet is not pretending to be.)*

---

## Status

This guide is under construction, in the open. Sections land one at a time and
each one is complete when it lands — there are no stubs pretending to be
chapters.

| | |
|---|---|
| written | 1 |
| in progress | the rest |
| last updated | 2026-09-21 |

Nothing in here is "production-ready" by assertion. Where something is untested
or unverified, it says so.
