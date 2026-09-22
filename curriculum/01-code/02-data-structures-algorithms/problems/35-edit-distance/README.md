# Edit distance

[Curriculum](../../../../README.md) · [Data structures and algorithms](../../README.md) · [All coding problems](../../../../../indexes/coding.md)

> “A text tool compares a source string with a target. One operation inserts,
> deletes, or replaces one character, each costing one. Return the minimum number
> of operations. Explain which prefixes your state describes before optimizing
> its memory.”

Constructed practice question. Prerequisite: [DP](../../lessons/08-dp.md).
Levenshtein distance counts these three operations; adjacent transposition is not
a separate permitted operation. Python strings here are sequences of Unicode code
points, which may differ from user-perceived characters.

| Contract | Required behavior |
|---|---|
| Input | Two strings, compared case-sensitively by code point |
| Output | Minimum unit-cost insertion/deletion/replacement count |
| Boundaries | Equal strings cost 0; empty versus length n costs n |
| Failure | Nonstrings raise `ValueError` |
| Scope | Distance only; no edit script, normalization, transposition, or weighted costs |

`kitten → sitting` costs 3: replace k→s, replace e→i, append g. `ab → ba` costs 2,
not 1, because swapping is excluded. A list of characters raises `ValueError` rather
than silently changing the input contract. Ask whether an actual edit script or
only a threshold decision is required; both affect retained state.

```mermaid
flowchart TD
  D["D(i-1,j): shorter source"] -->|"delete source character: +1"| X["D(i,j)"]
  I["D(i,j-1): shorter target"] -->|"insert target character: +1"| X
  R["D(i-1,j-1): both shorter"] -->|"match +0 or replace +1"| X
```

Before reading the answer, fill the boundary row and column for `cat → cut`.
Explain why `D(0,j)=j` is a sequence of real operations rather than a magic constant.

<details>
<summary>Solution, prefix recurrence, and follow-ups</summary>

The baseline branches recursively over insertion, deletion, and replacement. Many
branches revisit the same pair of remaining suffixes; without memoization, work
grows exponentially. A full DP table removes that repetition and makes the state
meaning inspectable before any rolling-row optimization.

Let `D(i,j)` be the minimum cost to convert the first i source characters into
the first j target characters. The final operation either deletes the final source
character, inserts the final target character, or aligns those two characters
with zero/matching or one/replacement cost. Take the minimum of the three pictured
predecessors. Boundary cells consume or produce all characters of one prefix.

**Invariant:** when computing cell `(i,j)`, its upper, left, and diagonal
predecessors already contain optimal prefix costs. Every edit script has one of
these final actions, and every predecessor plus that action is a valid script.
This establishes both a lower bound and a construction attaining the recurrence.

| Source prefix / target prefix | empty | c | cu | cut |
|---|---:|---:|---:|---:|
| empty | 0 | 1 | 2 | 3 |
| c | 1 | 0 | 1 | 2 |
| ca | 2 | 1 | 1 | 2 |
| cat | 3 | 2 | 2 | 1 |

Only the previous row and current row are needed for distance. Put the shorter
string on columns, using symmetry of unit costs. For lengths m,n, time is O(mn)
when both are nonempty, or more generally O((m+1)(n+1)); auxiliary space is
O(min(m,n)+1). Rows are numeric costs, and the returned integer needs constant
word-model output space. Swapping inputs would need reconsideration if insertion
and deletion had different costs.

Follow the three candidate costs into the first focused cell, then watch the
frontier and two-row memory band advance. The full grid preserves teaching history.

![Edit-distance predecessor costs arrive before the cell commits and the frontier advances](../../../../../assets/learning/dp-edit-frontier.svg)

[Open motion study](../../../../../assets/learning/dp-edit-frontier.svg) ·
[Read the completed still](../../../../../assets/learning/dp-edit-frontier-still.svg).

**Follow-up 1 — return an edit script.** Predict which information rolling rows
discard. Preserve a full table or backpointers and walk from `(m,n)` to `(0,0)`.
Specify deterministic tie handling. A divide-and-conquer reconstruction can reduce
memory, but it requires additional reasoning rather than reading discarded cells.

```mermaid
flowchart TD
  A["cat to cut: D(3,3)=1"] -->|"match t; diagonal"| B["ca to cu: D(2,2)=1"]
  B -->|"replace a with u; diagonal"| C["c to c: D(1,1)=0"]
  C -->|"match c"| Z["empty to empty"]
```

**Follow-up 2 — only accept distance ≤k.** If lengths differ by more than k, reject
immediately. Restrict computation to a diagonal band and cap costs above k,
carefully representing cells outside the band as unreachable. This is useful
when k is small; it is not a general shortcut for an unrestricted exact distance.

Senior depth derives state/boundaries and verifies an independent recursive
oracle. Lead depth clarifies Unicode normalization and user-visible edit semantics.

Reference: [solution.py](solution.py); tests cover all short binary strings,
symmetry, empty inputs, transposition exclusion, and code-point behavior.

```bash
python -m unittest discover -s curriculum/01-code/02-data-structures-algorithms/problems/35-edit-distance -p 'test_*.py'
```

</details>
