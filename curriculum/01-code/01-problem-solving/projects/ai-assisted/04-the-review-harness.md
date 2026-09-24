# Collect evidence about changed behavior and affected callers

## Application background

A reading-list API and its export job can share a parameter parser. Changing that parser may affect both features even when a commit message describes a small interface change.

## Your assignment

**Deliver:** Build a review-evidence command that reads a diff, names affected callers and reports uncertainty rather than inventing coverage.

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

1. In your work directory create a small `parseLimit` function with API-list and export callers, or select equivalent real code. Keep a before revision and a revision changing how limit zero is handled. These example names are fixtures you create, not supplied files.

2. Write a command that accepts those two revisions, collects the diff and searches direct call sites and existing checks. Include file locations and report `NONE` when no relevant existing check is found.

3. Add a dynamically registered caller that static name search misses. Manually compare the report with actual calls and record the tool's limits; a generated review summary is evidence for a reviewer, not approval.

## Demonstrate the result

| Case | Exact input or workload | Expected outcome |
|---|---|---|
| Small example | Diff changes `parseLimit`; callers are API list and export; only API list has `test_limit_zero`. | Report both callers; name that test for API list and `NONE` for the uncovered export behavior. |
| Boundary / failure | A caller is registered dynamically and absent from simple text search. | Mark search limits and inspect runtime registration; do not claim complete call-graph coverage. |
| Scope | Ten recorded diffs; collector supplies evidence, never an approval verdict. | Explain any additional assumption before implementing it. |

Keep the exact input, observed output and before/after artifact in your exercise README. Label constructed fixtures as fixtures. A fresh reader should be able to repeat the comparison without your conversation history.

## Deployment scope

This assignment concerns local development evidence and workflow. AWS deployment is not required and no cloud resources are supplied or created. CI-policy exercises belong in a disposable repository; they do not change this guide's publish-on-main behavior. For a later application deployment, the [starter's local-to-AWS mapping](../../../../../examples/reading-list-starter/README.md) explains the missing adapters.

## Additional reasoning and harder requirements

<details>
<summary>Study the failure, follow-up requirements and implementation prompts</summary>


```mermaid
flowchart TD
 M["PR message: label only"] --> R["Reviewer"]
 D["Parser change"] --> A["API caller"]
 D --> E["Unseen export caller"]
```

The message describes intent; risk follows actual dependency edges. A named nearby test is not proof until it detects the proposed accident.

<details>
<summary>Reveal the approach and decisions</summary>

Collect changed symbols, references, and tests, then identify the semantic risk. The invariant is that every claimed protection names a test demonstrated to fail on that accident. Preserve `NONE` and uncertainty rather than manufacturing a reassuring match.

</details>

## Follow-up 1 · Prove a named test

**Changed requirement:** The tool says `test_limit_zero` catches an inverted condition. How do you verify that statement? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Introduce that condition on an isolated branch and run the named test. Capture the failure and restore the tree; a passing mutant disproves the coverage claim.

```mermaid
flowchart TD
 M["Invert limit condition"] --> T["Named test"]
 T --> F["Expected failing assertion"]
 F --> R["Restore clean tree"]
```

</details>

## Follow-up 2 · The change crosses a service

**Changed requirement:** The parser determines an outbound payload used by an independently deployed consumer. What evidence is missing? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Add the consumer contract and a provider negative fixture. Local references cannot enumerate deployed clients; identify a contract owner and document unknown consumers.

```mermaid
flowchart TD
 P["Changed provider"] --> C["Versioned wire contract"]
 C --> U["Independent consumer"]
 C --> T["Provider contract test"]
```

</details>

## Record the evidence and limitations

Build in three stops: reproduce the small case and baseline failure; implement the protected boundary; then replay both changed requirements with captured outputs. Record commands, fixtures, and observed results in your implementation README. A diagram is a prediction until those checks run.

**Senior expectation:** Reproduce one real coverage gap and disprove one mistaken protection claim. **Additional lead scope:** Assign cross-service contract ownership and characterize collector blind spots. Completion demonstrates practice evidence; it does not establish interview readiness or multi-team delivery experience.

## Detailed implementation and AI-assisted prompts

*You end up with a repeatable interrogation for any diff, and one number from
ten real ones: how often nothing would have caught an accidental change.*

**Build**

A written procedure plus a small script that collects evidence and answers
three questions of any diff: what behaviour changed, what could have changed
accidentally, which existing test would catch the accident. Run it on ten real
diffs from your history and tally how often the third answer is "none".

**The thought process**

A harness is not for replacing your reading; it is for making your tenth review
of the day as good as your first. Attention degrades invisibly, and a procedure
carries quality through fatigue — the reason experienced pilots still run the
checklist. The commit message describes the intended change; the accidental one
lives in the blast radius — every caller of a changed function, every other
user of a touched helper or config key. That is greppable, so the script
fetches evidence and holds no opinions.

The third question must end in a test's name or the word "none" — never
"probably the auth tests". Both answers are checkable: break the behaviour and
the named test must fail; plant the accident and a true "none" leaves the suite
green. If all ten diffs come back covered, ask what the answers would look like
if coverage were bad — the same, and the harness is agreeing with you, not
reviewing.

**How to organise the prompts**

**1 — design the procedure against real diffs.**

```
Here are three recent diffs from this repository. Draft the
procedure for interrogating any diff: for each of the three
questions, the mechanical evidence that answers it — commands, not
judgment. The third answer must be a test name or the word NONE.
```

The procedure must name commands you can run; any step beginning "consider
whether" is judgment smuggled in as evidence, so send it back.

**2 — build the collector.**

```
Write the evidence collector: given a diff, list the changed
functions, their callers, every other file using a helper or config
key this diff touches, and the tests exercising any of those.
Output file:line lists only. No prose, no conclusions.
```

Run it on a diff whose blast radius you already know — it must find the caller
you know about, or it will never surface the ones you do not.

**3 — the ten runs.**

```
Here is diff 4 of 10 and the collector's output. Answer the three
questions; every claim must cite file:line from the evidence. If no
existing test would catch the accidental change, write NONE — not
the nearest test.
```

Spot-verify two NONEs by making the accidental change for real: a green suite
means the NONE was true and the tally is data.

**On AWS**

It can run where the diff lives: **GitHub Actions**, on every pull request.
Estimate runner usage for the current repository plan. AWS enters only if the harness calls a model per diff
— then route it through **Bedrock** with invocation logging on, so each review
has a visible cost in **CloudWatch**; a review bot nobody meters gets quietly
expensive. And whatever runs it gets read-only credentials: it comments, it
never merges.

**What productionising it means**

The tally is the real product: a none-rate over time, saying whether the suite
grows with the code or falls behind it. The failure mode is ritual — people
reading the harness instead of the diff — so it cites evidence and asks
questions, never concludes "looks good". Alarm on the none-rate rising; that is
the trend it exists to catch.

**The learning**

The dangerous part of a change is the part the message never mentions, and
"none" is the most informative answer a review can produce — untooled reviews
almost never do. Ten diffs teach you your real safety margin as no coverage
percentage has.

**How you would know it is wrong**

- Plant an in-passing edit to a shared helper in a test diff. If question two
  does not list it, the blast-radius logic is decorative.
- Verify a named test the way you verify a NONE: break the behaviour; that
  test, specifically, must fail.
- Run the harness twice on one diff. Materially different answers mean a rumour
  generator; pin every claim to collector output.
- Ten out of ten covered. In my own record, answers shaped that much like good
  news have usually been the instrument — check it before you believe it.

---

[Back to the ordered project index](../../ai-projects.md)


</details>
