# How to use the curriculum

Start with [the ordered subjects](../curriculum/README.md). Each chapter explains
what it teaches, what comes before it, and where to continue. The coding,
project, AWS and assessment indexes point to the same material.

## Start with the actual problem

Read the opening brief and contract before the worked answer. State an ordinary
example, a boundary case and the invariant. Predict the first diagram, then
implement or draw a simple correct baseline. Use the explanation to check your
reasoning and identify the repeated work or failed boundary.

Learn a chapter's core concepts before its exercises. You do not need to finish
all 42 coding problems before building an application. Advanced problems live
beside the concepts they need, including caching and concurrency. Later-topic
follow-ups link their dependencies so you can return after learning them.

Testing and ownership checks belong in the first implementation. The dedicated
testing and security chapters deepen those skills. System design comes before
CI/CD and infrastructure so service choices follow an understood architecture.

## One problem, increasing depth

Work the baseline first, then change the requirement. Senior follow-ups add
operating constraints and failure behavior. Staff/lead follow-ups add broader
ownership, compatibility, migration and decisions where the existing problem
supports that scope. These are criteria within a lesson, not separate reading paths.

Keep the candidate question visible and open the worked answer after an attempt.
Explain what the changed requirement invalidates, update the diagram or code,
and make a tempting broken solution fail a test. A supplied reference passing
its suite is evidence about the reference, not your independent performance.

## Use AI and keep responsibility for the result

The existing prompts practice specification, bounded implementation and review.
For an assisted exercise, make a request small enough to end at a runnable
checkpoint, ask about likely failure modes, inspect the diff and verify it.
Keep the acceptance criteria established before implementation.

For an independent assessment, use only its allowed tools. Close the reference
and assessor material. If AI is allowed, explain the generated code, catch its
failures, and own the decisions. [Working with AI](../curriculum/01-code/01-problem-solving/working-with-ai.md)
and [the first assisted change](../curriculum/01-code/01-problem-solving/ai-assisted-practice.md)
provide the original method and concrete examples.

## Choose an existing project

The [project index](../indexes/projects.md) groups 40 standalone briefs by subject.
Each page preserves its context, reasoning, staged prompts, AWS choices and checks.
For continuity, use [one reading-list system](../projects/reading-list/README.md)
through its five existing stages. Those stages depend on their predecessors;
they are not separate versions chosen by job title.

A project brief describes what you build. A lab that supplies reference code says
so and provides run commands. Local checks do not require an AWS deployment.
Follow a lab's explicit setup and scope before using infrastructure; the recorded
[verification limits](VALIDATION.md) remain in force.

## Decide what counts as evidence

Set acceptance criteria before building. Run the checks and deliberately break
the guarantee they claim to protect. Keep code, diagrams, inputs, outputs and
failed attempts. Use the [assessment packs](../practice/README.md) and
[attempt record](../practice/attempt-record.md) for unfamiliar sessions on separate
occasions. The [depth reference](../practice/depth.md) calibrates the same work
under increasing scope; it is not an employer pass-rate prediction.

Close the page and reconstruct the explanation, then revisit it after a delay.
Use what you could not retrieve to choose a prerequisite. Do not substitute
rereading or a familiar memorized answer for an unfamiliar independent attempt.

## Keep claims and corrections traceable

Research retains its original dates, sources and limitations. An undated technical
reference is not evidence of a recent interview question. Verify dated or
provider-specific claims before relying on them for a new application.

Report an outdated claim with what you checked and when; an acceptance check that
cannot fail; an unclear prerequisite; or a diagram that adds no information.
The curriculum teaches engineering judgment and practice. It does not replace
all language/framework documentation, real organizational experience or actual
candidate assessment.
