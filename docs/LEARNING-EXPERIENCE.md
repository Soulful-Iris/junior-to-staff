# Teach the problem before the solution

This standard applies to **both paths**. A reader should hear a clear problem,
see concrete behavior, and learn how to make the next decision. A list of terms,
an unexplained animation, or a project assignment without a starting point does
not meet the standard.

## Open the conversation

Begin each substantive lesson or project with an interviewer-style brief:

> “Here is the system we have. Here is what is going wrong. Your job is to
> preserve this property while handling this new constraint. Before coding or
> drawing, what would you clarify?”

Make that brief specific to the subject. Name the user, operation, current
behavior, and desired outcome. Explain unfamiliar terms when introduced. In the
AI path, the learner plays the engineer directing and reviewing implementation;
in the interview path, the learner implements and explains independently first.

Follow with a small contract table: inputs or workload, expected output, boundary
behavior, and deliberately excluded scope. Example numbers are teaching inputs,
not production benchmarks or advertised AWS limits. Include at least one worked
input/output pair and one failure case.

## Show an approach the learner can reuse

Explain an observable problem-solving method rather than presenting an answer as
an unexplained leap:

1. Restate the contract and ask the questions that change the design.
2. Walk through a tiny example. Identify the invariant that must remain true.
3. Draw or implement a simple baseline. Give a counterexample or measured cost.
4. Change the representation or boundary that causes the problem.
5. Trace the improved approach; explain why the invariant survives each change.
6. Check edge cases, complexity, resource budgets, and failure behavior.

Use short explanations of decisions, alternatives, and evidence. Do not pad a
page with a transcript of internal deliberation. State what a strong candidate
would say aloud and what evidence would change the choice.

## Draw as the requirements change

A substantive project or coding problem needs at least two distinct useful
visuals: its initial mechanism and a changed requirement or failure. Architecture
projects should normally include a baseline box diagram, a corrected design, and
a follow-up design. Label arrows with operations or data, and show where state
and authority live. A database box is not a substitute for a schema or invariant.

Use structures suited to the concept: a tree for recursive return values, a
table for a DP state, a sequence for racing writes, a state machine for an editor,
and boxes for API/cache/queue/store boundaries. Ask the reader to predict a
transition or redraw the system before revealing the follow-up diagram.

Preserve the original illustrations. Add motion where elapsed time or changing
state teaches something static frames cannot. Avoid slideshow animations and
repeated decorative templates. SVGs must be readable frozen, include accessible
text and a still alternative, and be rendered and inspected before commit.
Mermaid diagrams must also be rendered and inspected, not only syntax-checked.

## One project, one page

Each of the existing section and act projects gets its own Markdown page. Keep
the former bundled page as a short index with a suggested order, prerequisites,
and the property each project demonstrates. Preserve useful existing teaching,
working AI prompt sequences, AWS choices, and checks during the move. Repair
relative links and preserve old entry points.

A project page contains:

- A concrete opening brief, prerequisite links, and sample behavior.
- A baseline diagram and the failure it admits.
- The decisions in a sensible order, with the invariant and trade-offs.
- A runnable starting command where code is supplied; otherwise an explicit
  statement that this is a build brief, with staged deliverables and checks.
- Two or more follow-up questions with changed assumptions, expected reasoning,
  and diagrams showing the resulting change.
- AI-path prompts that each end at a verifiable checkpoint; interview-path
  instructions that keep the candidate brief separate from the solution.
- Senior expectations, additional lead scope where relevant, and observable
  acceptance checks. Completion is practice evidence, not a hiring prediction.

## At least forty complete coding problems

The coding route must contain at least forty distinct, individually linked
problems. Multiple language translations, hints, and changed inputs do not count
as extra problems. Each problem needs a full contract, worked example, baseline,
invariant, visual trace, runnable reference, meaningful tests, time and auxiliary
space bounds, and follow-ups that change the problem. Explain prerequisite
concepts before using them. Use Python for algorithms and TypeScript for browser
and asynchronous work where it serves the lesson.

Keep answers behind a separate link or disclosure. Provide an ordered progression
and role-specific detours, then an unfamiliar assessment. A green reference test
suite verifies supplied code; it does not assess the reader.

## Audit closure and evidence

Track every finding from [issue #1](https://github.com/Soulful-Iris/junior-to-staff/issues/1)
in [AUDIT-IMPLEMENTATION.md](AUDIT-IMPLEMENTATION.md). Corrections must reach both
paths, including project briefs and illustrations that repeat the claim. Each
finding needs concrete changed files, a check of the failed guarantee or missing
skill, and an honest account of validation limits.

Interview research must be dated **2025-09-22 or later**, preferably **2026-03-22
or later**, for this review. Separate publication dates from interview dates and
undated official guidance. Technical documentation supports behavior, not a claim
that a company asks a question. All newly constructed practice prompts must be
identified as constructed; never imply company attribution without evidence.
