# Rewrite private commit history to explain a change

## Application background

An engineer sees a title-fetch timeout of 800 ms in a reading-list service and wants to know why it is not 300 ms. The Git history contains several commits named `wip`, mixing the timeout change with a helper rename. The final code works, but its explanation is hard to recover.

In a private copy, reorganize that history so the reason for the behavior change is easy to find. Keep the final code identical. This exercise concerns Git commits, the saved revisions in source history, rather than database transactions.

The quality of the history is measured by what it lets a reader understand. A prettier sequence that changes delivered behavior does not satisfy the assignment.

## Your assignment

**Deliver:** Produce two private histories with the same final code and compare how easily a new reader can explain a timeout decision.

This is a constructed development-workflow exercise. Your output is the artifact named above and the observed comparison, rather than a production platform.

## Get the starting application and prepare your workspace

The [repository](https://github.com/Soulful-Iris/junior-to-staff) includes a small reading-list HTTP API with SQLite storage. Follow the [setup and request walkthrough](../../../../../examples/reading-list-starter/README.md) to save a URL and read it back before changing anything. The API has no tag endpoint, browser UI or production authentication yet.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/reading-list-starter/app.py --db /tmp/reading-list.sqlite3
```

Leave the server running while sending the documented requests in a second terminal. Use a separate working copy for the exercise. Any helper, specification, review command or Git branches named below are artifacts **you create**, not hidden supplied solutions.

## Complete the exercise

1. Use a disposable copy of the starter and initialize a separate Git repository there. Make three small commits: change a timeout, rename a helper and document the observed timeout outcome. Save the original branch.

2. Create a second private branch and reorganize commits and messages to separate the behavior change from the rename. Include the timing observation that motivated the value. Never rewrite a shared branch for this exercise.

3. Compare the branch tips with `git diff original..revised`: there should be no content difference. Give a fresh reader the timeout line and ask them to locate its rationale in each history. Record the lookup and missing evidence.

## Demonstrate the result

| Case | Exact input or workload | Expected outcome |
|---|---|---|
| Small example | Three commits change timeout 300 → 800, rename a helper, then add a timeout test. | The rewritten tip has an empty diff against the original tip. The reader cites the timeout decision and its test. |
| Boundary / failure | A rewrite accidentally restores timeout 300. | The tip comparison fails even if all rewritten commits look tidy. |
| Scope | Private practice branches. No rewriting a branch other people use. | Explain any additional assumption before implementing it. |

Keep the exact input, observed output and before/after artifact in your exercise README. Label constructed fixtures as fixtures. A fresh reader should be able to repeat the comparison without your conversation history.

## Deployment scope

This assignment concerns local development evidence and workflow. AWS deployment is not required and no cloud resources are supplied or created. CI-policy exercises belong in a disposable repository. They do not change this guide's publish-on-main behavior. For a later application deployment, the [starter's local-to-AWS mapping](../../../../../examples/reading-list-starter/README.md) explains the missing adapters.

## Additional reasoning and harder requirements

<details>
<summary>Study the failure, follow-up requirements and implementation prompts</summary>


```mermaid
flowchart TD
 L["Line: timeout 800"] -->|git blame and log| C["Three wip commits"]
 C -->|possible explanation| M["Measured deadline?"]
 C -->|possible explanation| A["Accidental default?"]
 M --> E["No cited decision evidence"]
 A --> E
```

The code records the chosen number, but not whether it came from a measured deadline or an accident. Faster lookup of a wrong explanation is not success.

<details>
<summary>Reveal the approach and decisions</summary>

First inventory decisions, then group commits by behavior and dependency. Preserve intermediate runnable states when possible. The invariant is byte-identical final trees. A test run alone cannot prove it. Measure a cited, correct answer separately from elapsed time.

</details>

## Follow-up 1 · A shared branch already exists

**Changed requirement:** A teammate has based two commits on the old history. How do you run the drill safely? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Keep the shared reference stable and create a separate rehearsal branch. Compare trees there. Use improved messages only on future shared work. The expected outcome is zero forced updates to the teammate’s base.

```mermaid
flowchart TD
 A["Shared main"] -->|unchanged base| B["Teammate commits"]
 A -->|copy| C["Private rehearsal"]
 C -->|compare final trees| D["Original tip"]
```

</details>

## Follow-up 2 · The explanation lives outside Git

**Changed requirement:** The decision cites a benchmark file that will disappear. What must survive a year? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Attach the input, units, observed result, and a stable artifact identifier to the decision record. A narrative with a broken evidence link is not recoverable. Re-run the stranger exercise from an offline clone or exported bundle.

```mermaid
flowchart TD
 A["Decision commit"] -->|why| B["Measured deadline"]
 A -->|artifact ID| C["Versioned benchmark fixture"]
 C -->|replay| D["Cited result"]
```

</details>

## Record the evidence and limitations

Build in three stops: reproduce the small case and baseline failure. Implement the protected boundary. Then replay both changed requirements with captured outputs. Record commands, fixtures, and observed results in your implementation README. A diagram is a prediction until those checks run.

**Senior expectation:** Show the empty diff and one correct independently cited answer. **Additional lead scope:** Define retention and the owner of decision artifacts. Completion demonstrates practice evidence. It does not establish interview readiness or multi-team delivery experience.

## Detailed implementation and AI-assisted prompts

*You end up with the same week of work told two ways, and a number: how long a
stranger takes to find out why a line changed in each.*

**Build**

Take a real week of your Stage 1 reading-list history — the honest one with `wip` in it. On a
copy, rewrite it into the sequence you would want at 3am: same final code,
different story. Then the experiment: a reader with no context gets one line
and one question — why is this here — against each version, timed.

**The thought process**

The first decision is not a git command, it is a list: what were the actual
decisions made that week? A `fixes` commit usually contains three. Commits are
supposed to map to decisions one for one, so until the list exists you cannot
say what the commits should have been.

Second: where rewriting is allowed. Shared history is a record other people
have built on. Rewriting it deletes their context. On a branch never pushed it
is a drill — with one honesty constraint: the final tree stays byte-identical.
You change the story, never the code, and `git diff` between the tips is the
proof.

Last: time-to-answer only counts when the answer is right and cited — the
stranger must name the commit that justifies the line. A fresh model session
with nothing but the clone is the perfect stranger: no memory of the ticket,
no politeness about a useless history.

**How to organise the prompts**

**1. The inventory.**

```
Read `git log -p` for the last week on this branch. List the distinct
decisions buried in it: behaviour changes, refactors, reversals, dead
ends. One line each. Do not touch the repository yet.
```

Check it against your memory of the week. A decision it missed was recorded
nowhere — a finding before anything is built.

**2. The plan.**

```
Plan a rewritten history for a copy of this branch: one commit per
decision, refactors separate from behaviour changes, each message one
line of what plus a body saying why and what we tried that did not
work. The final tree must stay byte-identical. Show me the plan first.
```

Read it as prose. Any commit that needs the word "and" gets split before you
approve.

**3. The execution.**

```
Execute the plan on a new branch, then run
`git diff <old-tip> <new-tip>` and show me the output. It must be
empty. If it is not, stop and tell me what differs.
```

The empty diff is the checkpoint: story changed, code untouched.

**4. The experiment**, in a fresh session with only the clone:

```
Why does line <N> of <file> say what it says? Use only git log, git
blame and the code. Cite the commit that justifies your answer.
```

Time it against both branches. Wrong-but-fast counts as wrong.

**On AWS**

The record belongs beside the code. **GitHub** fits this repository's review
workflow. **CodeCommit** is an AWS-hosted Git option when IAM integration and
AWS account controls are part of the requirement. Compare current collaboration
features and exportability rather than choosing by a historical service rumor.
Keep an independent `git bundle` snapshot in a versioned **S3** bucket if you
need an offsite repository record. Verify that it restores the refs you intend
and budget storage/retention. CodeCommit capability checked 2026-09-22 against
[the official overview](https://docs.aws.amazon.com/codecommit/latest/userguide/welcome.html).

**What productionising it means**

The rewrite is a drill, not a workflow. The production version is writing
history well on the way in: a message check in project 3's pipeline, a
protected main so nobody rewrites what others built on, and the inventory
prompt run before a week of work instead of after it.

**The learning**

A history has a reader, and the reader arrives at the worst possible moment.
Watch a stranger answer "why is this line here" in ninety seconds against one
telling and give up against the other, and "backup versus record" stops being
a slogan.

**How you would know it is wrong**

- `git diff` between the tips is not empty: you edited code, not story. Start over.
- The stranger answers as fast against the messy history: the question was answerable from code alone — pick a line whose *why* is not in the file.
- You cannot answer the same question about your own rewritten history a week later.
- Messages that narrate the diff — first word "update", "change", "fix" — survived the rewrite. Grep for them.

---

[Back to the ordered project index](../../change-projects.md)


</details>
