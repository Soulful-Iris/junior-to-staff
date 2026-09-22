# 4. The review you automate away

[Curriculum](../../../../README.md) · [Problem solving and AI-assisted engineering](../../README.md) · [Project index](../../../../../indexes/projects.md)

## The reviewer's brief

> Your reviewers spend half their comments on formatting and still miss ownership bugs. Sort the last 20 comments and automate only rules with a defensible oracle. What must remain a human decision?

This is a **constructed practice brief**, not an attributed company question.
Prerequisites: [the section](../../change-loop.md). This page is a build brief; it does not ship a runnable application. The original build and prompt sequence below defines the implementation checkpoints.

| Case | Exact input or workload | Expected outcome |
|---|---|---|
| Small example | 20 comments: 8 formatting, 4 imports, 3 naming, 5 behavioral concerns. | 12 deterministic comments map to formatter/linter checks; the 8 judgment comments retain a human owner. |
| Boundary / failure | The AI review gives a style verdict and silently approves a missing owner check. | Its contract is violated; human behavioral review remains required. |
| Scope | Five subsequent PRs form a small local experiment, not a universal productivity study. | Explain any additional assumption before implementing it. |

Before looking at the guidance, state the invariant in one sentence and trace the example. In interview practice, implement or sketch independently, then reveal the reasoning. During AI-assisted practice, use the prompts below and verify each checkpoint before the next request.

## Baseline and the failure to explain

```mermaid
flowchart TD
 A["PR diff"] --> B["Human review"]
 B -->|12 mechanical comments| C["Formatting discussion"]
 B -->|8 judgment comments| D["Behavior and design"]
```

The baseline consumes the same attention on deterministic and contextual decisions. Automating a subjective rule without measuring false positives can increase the review burden.

<details>
<summary>Reveal the approach and decisions</summary>

Classify comments with examples, enforce a small deterministic set, and keep the AI pass advisory with a bounded job. The invariant is that mechanical enforcement does not grant behavioral approval. Count overrides and correctly found seeded defects alongside comment volume.

</details>

## Follow-up 1 · The repository is already large

**Changed requirement:** Turning on a formatter touches 500 files. How do reviewers retain a useful history? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Land one behavior-preserving mechanical change and a separate enforcement change. Existing tests should remain unmodified. Record formatter version and exclude unrelated fixes so blame and rollback remain interpretable.

```mermaid
flowchart TD
 A["Pinned formatter"] -->|mechanical-only commit| B["500 formatted files"]
 B -->|unchanged tests| C["Behavior check"]
 D["Separate required job"] -->|future diffs| B
```

</details>

## Follow-up 2 · The AI endpoint is unavailable

**Changed requirement:** The model is down during an urgent security patch. Should the patch wait? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Choose and document an advisory fail-open policy with a human reviewer for this exercise. Deterministic gates still run. Record the skipped AI pass, then compare later findings; its absence must not silently become a behavioral approval.

```mermaid
flowchart TD
 A["Pull request"] --> B["Deterministic required checks"]
 A --> C["AI first pass unavailable"]
 C -->|record skip| D["Human behavior review"]
 B --> E["Merge decision"]
 D --> E
```

</details>

## Evidence to bring to review

Build in three stops: reproduce the small case and baseline failure; implement the protected boundary; then replay both changed requirements with captured outputs. Record commands, fixtures, and observed results in your implementation README. A diagram is a prediction until those checks run.

**Senior expectation:** Catch the seeded behavioral bug after removing style noise. **Additional lead scope:** Assign rule ownership and a measurable exception-removal process. Completion demonstrates practice evidence; it does not establish interview readiness or multi-team delivery experience.

## Build and prompt sequence

*You end up with your review comments sorted into machine work and judgment,
and the machine pile at zero on your next five pull requests.*

**Build**

A corpus of real review comments — project 2 supplies plenty — sorted into
what a machine could have said and what needed a person. Then the machine
layer: a formatter that rewrites, a linter and import order that enforce, an
AI first pass constrained by contract. Then the count, re-run on your next
five PRs.

**The thought process**

The first decision is the line itself. Mechanical means one right answer every
time it applies: formatting, import order, unused symbols, an obvious footgun.
Judgment means naming, design, "is this the right change at all". The
dangerous territory is the middle — rules right often but not always — because
every false positive spends the gate's credibility, and credibility does not
refill. Start strict and small.

Second: enforce beats advise. A formatter that rewrites ends the argument; a
linter that complains starts one. The state you are buying is that style stops
being reviewable because it stops being variable.

Third: adopting a formatter on an existing repo means one huge mechanical
diff. That is project 1's discipline arriving as policy — its own commit,
behaviour identical, tests untouched, mixed with nothing.

Fourth: the AI pass gets a job description, and it is the section's first-pass
read: map where human attention should go, name what is absent, no verdicts —
and no style, because machines now own style twice over.

**How to organise the prompts**

**1. The sort.**

```
Here are the review comments from my last N pull requests. For each:
could a machine have made this comment every time it applies, yes or
no? For each yes, name the tool or rule. For each no, name the
judgment it needed.
```

Sample ten yeses and argue where you disagree — a wrong yes is a future false
positive, cheap to catch now.

**2. The tools, one at a time.**

```
Add the formatter as two commits: one that only reformats, tests
untouched and green, and one that enforces it as a pipeline job. Then
the linter and import order, same shape. Show each enforcement going
red on a planted violation before we keep it.
```

The reformat commit's tests must pass unmodified, and every tool must have
been seen red once.

**3. The AI pass, with a contract.**

```
Wire a first-pass review on every PR with this contract: comment only
on behaviour, risk, and what is absent — tests, migration, rollback.
Never comment on style or formatting. End with the three hunks most
deserving of human attention, and no verdict.
```

Test the contract on a PR that is stylistically ugly and behaviourally fine.
One style comment is a breach — tighten and rerun.

**4. The count.**

```
For my next five PRs, sort every review comment into the two piles and
report the machine pile per PR. For each machine comment that still
occurred, name the missing or misconfigured rule.
```

The target is zero, and every non-zero names its own fix.

**On AWS**

The zero-setup machine pass is GitHub-side and covered in
[the section](../../change-loop.md). The AWS version exists for one reason: when the diff
must not leave your boundary, run the model through **Bedrock** from a small
**Lambda** on the PR webhook, the pipeline assuming an **OIDC** role. Bedrock
rides IAM, so no vendor API key sits in repository secrets for project 3's
scanner to find. Lambda beats **CodeBuild** for the bot because a diff fits in
memory and the work lasts seconds; a build container is the wrong shape. The
mechanical tools can stay in Actions. Estimate model invocations separately
from CI usage; neither a small diff nor IAM integration proves a zero bill.

**What productionising it means**

Keep a false-positive ledger: a rule overridden more than about weekly gets
fixed or deleted, because an ignorable gate teaches ignoring gates. Pin
formatter and linter versions — an unpinned formatter upgrade reformats the
world mid-PR. And decide in writing whether the AI pass fails open or closed
when its API is down; not deciding means finding out during an outage.

**The learning**

Reviewer attention is the loop's scarcest input, and every comment category
you automate is attention returned to questions only a person can answer. The
corollary: enforced checks disappear from consciousness, advisory ones become
noise, and almost nothing worth keeping lives in between.

**How you would know it is wrong**

- Plant one style violation and one real bug in the same PR. The machine must catch the style; the human pass must still catch the bug. A bug that sailed through on a green glow means you automated complacency.
- The comment mix is unchanged after a month: the tools are advisory, or not required, or not running.
- Overrides rise week on week: the rules spend credibility faster than they earn it.
- Turn the formatter off locally and push. The pipeline must catch it — advice dies, law holds.

---

[Back to the ordered project index](../../change-projects.md)
