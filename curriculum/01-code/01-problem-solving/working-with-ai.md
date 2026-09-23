# Working with an AI that writes the code

[Curriculum](../../README.md) · [Problem solving and AI-assisted engineering](README.md)

> Project connection · feeds **every project in this guide**

## At the whiteboard

> “An assistant implemented quantity updates and supplied passing tests.
> A customer cannot save zero. What should you check before accepting a repair?”

| Request with current quantity `7` | Expected result for this exercise |
|---|---|
| `{ "quantity": 0 }` | Save `0` |
| `{}` | Keep `7` |
| `{ "quantity": -1 }` | Reject; keep `7` |
| `{ "quantity": null }` | Reject; keep `7` |

Missing, null and zero are different product cases. Agree on the contract before
accepting the implementation; do not let a convenient language expression pick
it silently.

```mermaid
flowchart TD
  Wish[Vague request] --> Code[Generated implementation]
  Code --> Tests[Tests repeat implementation assumptions]
  Tests --> Green[Green result with a wrong contract]
  User[Customer saves zero] --> Failure[Old quantity remains]
  Code --> Failure
```

## Reason through the review

1. Use the four cases above as an independent oracle.
2. Inspect the smallest patch. `value || current` loses zero; `??` still needs
   the chosen null validation.
3. Exercise the real request boundary. JSON input is not validated by a
   TypeScript annotation.
4. Restore the known zero-handling defect in a disposable copy. The zero test
   should fail. This checks sensitivity to that defect, not all defects.

```mermaid
flowchart TD
  Contract[Agreed examples] --> Tests[Contract tests]
  Request[Bounded request] --> Code[Candidate patch]
  Code --> Tests
  Mutant[Known wrong zero handling] --> Tests
  Tests --> Decision[Review results and remaining limits]
```

## The mental model

![Specification and generation lead to verification; the result must be checked against an independently chosen expectation.](../../../assets/diagrams/verify-bottleneck.svg)

Specify the behavior, generate a candidate, then verify it. Faster generation
does not tell you how much review a particular patch needs. Measure your own
specification, implementation, review and rework time separately.

The important distinction is **where the expectation comes from**, not whether
the test was written before or after the code, or by a person or an assistant.

| Check | What it tells you |
|---|---|
| A post-implementation test expects saving `0` to store `0`, from the product contract | Useful evidence for that case, even on its first green run |
| `assert result == result` | Nothing about whether the result is correct |
| Restore `value || current`; the zero test fails | The test detects this known zero-handling defect |
| Replace `x + 0` with `x` for ordinary integers; tests stay green | This equivalent change does not alter the supported behavior |
| A mocked database returns the expected row | Checks caller logic, not actual SQL or database isolation |

Test-first development is a useful workflow. A deliberately failing run is a
useful negative control. Neither chronology nor one killed mutant proves the
whole implementation correct.

## Ask an assistant for useful evidence

```text
State the contract and concrete normal, empty and invalid-input examples.
List important assumptions and unresolved questions; do not invent concerns.
Implement one reviewable slice and name the boundaries its tests exercise.
Report the exact commands and results, including failures and skipped checks.
```

For a regression, ask for a test that fails on the known buggy version and passes
on the repair. For already-correct behavior, a green first run is acceptable:
explain the independent expectation and add a meaningful negative control when
it would strengthen the evidence.

```text
Review the diff, not its description.
What behavior changes? What could change accidentally?
Which checks cover those risks, and what remains untested?
Support approval or requested changes with evidence; approval unchanged is valid.
```

## What to inspect before accepting

Read the diff and the assertions. Check swallowed exceptions, default values
standing in for failed calls, authorization boundaries and added dependencies.
Use real integrations where their behavior is the claim; use fakes where you
need controlled caller-state tests. Neither substitutes for the other.

A short homemade replacement is not automatically safer than a maintained
library. Compare the required behavior, security surface, maintenance cost,
license and dependency graph—not just line count.

## Your slice of the project

Before P1, keep a short `DECISIONS.md`: the chosen contract, meaningful
alternatives, unresolved assumptions and how they were checked. Record actual
unknowns; do not accept confusing code merely to fill a required list.

**Acceptance:** demonstrate the four quantity cases, explain the patch, show
what the tests do and do not establish, and justify the review decision. A clean
patch may be accepted without a forced objection. For interview practice,
attempt a fresh variant unaided and record any prior exposure or tool use.

## Words you now own

**Specification:** the requested behavior. **Oracle:** the independent expected
result. **Negative control:** a known-bad case used to check detection.
**Equivalent mutant:** a changed implementation with the same supported
behavior. **Swallowed error:** a failure hidden instead of handled explicitly.

## Draw it from memory · Keep the author separate from the oracle

```mermaid
flowchart TD
  Spec[Behavior and forbidden changes] --> AI[AI-generated candidate]
  Spec --> Cases[Independently chosen boundary cases]
  AI --> Sandbox[Isolated execution]
  Cases --> Oracle[Expected results]
  Sandbox --> Compare[Observed vs expected]
  Oracle --> Compare
  Compare -->|mismatch| Spec
  Compare -->|bounded evidence| Review[Review and acceptance]
```

**Redraw challenge:** show how a plausible explanation and a passing tautology
can coexist with the zero-handling defect.

[Research notes and limits](../../../docs/research/junior-foundation-research-2026.md) · [Learning sequence](../../README.md) · [Independent practice](../../../practice/interview-guide.md)
