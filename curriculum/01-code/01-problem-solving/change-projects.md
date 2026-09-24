# Practice reviewable changes and integration decisions

[Curriculum](../../README.md) · [AI-assisted code changes](README.md)

Read [the section](change-loop.md) first. Work in this order; each project isolates one skill. Each link opens one complete build brief with a concrete contract, a baseline, two changed requirements, and the original staged AI prompts.

These are five project briefs, not five supplied applications. All prompts are constructed practice.

<a id="1-the-history-a-stranger-can-debug-from"></a>

### 1. Rewrite private commit history to explain a change

[Rewrite private commit history to explain a change](projects/change-loop/01-the-history-a-stranger-can-debug-from.md) — Preserve the final tree while making decisions discoverable.

<a id="2-the-change-small-enough-to-judge"></a>

### 2. Split a tagging feature into runnable changes

[Split a tagging feature into runnable changes](projects/change-loop/02-the-change-small-enough-to-judge.md) — Separate reviewable changes without unsafe intermediate states.

<a id="3-the-pipeline-that-can-refuse"></a>

### 3. Demonstrate CI enforcement in a disposable repository

[Demonstrate CI enforcement in a disposable repository](projects/change-loop/03-the-pipeline-that-can-refuse.md) — Prove each merge gate refuses a named harmful change.

<a id="4-the-review-you-automate-away"></a>

### 4. Automate deterministic review rules and retain human judgment

[Automate deterministic review rules and retain human judgment](projects/change-loop/04-the-review-you-automate-away.md) — Automate deterministic review rules while preserving human judgment.

<a id="5-two-greens-that-make-a-red"></a>

### 5. Check the combined behavior of independently valid changes

[Check the combined behavior of independently valid changes](projects/change-loop/05-two-greens-that-make-a-red.md) — Test semantic integration against the base that will actually land.
