# Word ladder

[Curriculum](../../../../README.md) · [Data structures and algorithms](../../README.md) · [All coding problems](../../../../../indexes/coding.md)

> “A word-game editor changes one letter per move. Each intermediate word must be
> in our dictionary. Players need the fewest moves between two words, including
> a path they can inspect. How would you distinguish impossible from zero moves?”

Constructed practice question. Prerequisite: [BFS](../../lessons/05-graphs.md).
A graph may be **implicit**: its edges are generated from the current word rather
than stored. Breadth-first search visits states by increasing number of moves.

| Contract | Required behavior |
|---|---|
| Input | Equal positive-length lowercase ASCII endpoints and dictionary words |
| Output | A shortest endpoint-inclusive list, or `[]` when impossible |
| Membership | Start need not be in dictionary; a different end must be |
| Boundaries | Equal endpoints return `[start]`; repeated dictionary entries collapse |
| Failure/scope | Invalid lengths/characters raise `ValueError`; no insertions or deletions |

<!-- interview-rehearsal:start -->

## What the interviewer expects

The opening scenario is the product context; the table above is the callable
contract. Your job is to connect them. Before coding, say what the output means,
walk one normal case and one case that could disprove a tempting shortcut, then
name the invariant your implementation will preserve. Start with a correct
baseline, improve it deliberately, and derive time and space from actual work.

**Done means:** A shortest endpoint-inclusive list, or `[]` when impossible.

Passing the happy path alone is not done; your answer
must make a deliberate decision for every scenario below without mutating input
unless the contract explicitly permits it.

### Test-case scenarios to settle before coding

| Case | Exact input or state | Expected result | What it is testing |
|---|---|---|---|
| Representative | `hit` to `cog` through standard dictionary | a shortest endpoint-inclusive path | BFS returns minimum transformations. |
| Same endpoint | `same` to `same` | `["same"]` | Zero transformations still includes the endpoint. |
| Missing end | end absent from dictionary | `[]` | A different end must be admitted. |
| Unreachable | valid words split into components | `[]` | Valid input need not have a solution. |
| Duplicates | dictionary repeats a word | same path semantics | Repeated entries do not create states. |
| Invalid | mixed lengths or non-lowercase ASCII | `ValueError` | Neighbor generation depends on the alphabet contract. |

Do not merely list these cases in an interview. For each one, point to the branch,
state transition, or invariant that makes the expected result inevitable. If your
design cannot explain a row, the design is not finished yet.

<!-- interview-rehearsal:end -->

`hit → cog` using `{hot,dot,dog,lot,log,cog}` has four moves, with answer
`[hit,hot,dot,dog,cog]`. The equally short route through lot/log is also valid.
With only `{hot,cog}`, return `[]`. Clarify whether all shortest paths are needed;
returning one predecessor per word deliberately answers only one-path queries.

```mermaid
flowchart TD
  H["hit: depth 0"] -->|"i to o"| O["hot: depth 1"]
  O -->|"h to d"| D["dot: depth 2"]
  O -->|"h to l"| L["lot: depth 2"]
  D -->|"t to g"| G["dog: depth 3"]
  L -->|"t to g"| X["log: depth 3"]
  G -->|"d to c"| C["cog: depth 4"]
  X -->|"l to c"| C
```

Try an independent implementation. Explain when a word becomes visited and whether
two parents are allowed to enqueue it before you open the solution.

<details>
<summary>Solution, representation choice, and follow-ups</summary>

The direct baseline compares every pair of dictionary words and stores an edge
when exactly one character differs. For N words of length L this costs O(N²L),
even if the reachable component is tiny. DFS can find a route but its first route
need not be shortest: exploration order can follow a long detour first.

Instead generate each one-character replacement on demand. Check membership in a
set, mark the word discovered immediately, and save its parent. The BFS queue
contains the current distance layer followed by the next. **Invariant:** the first
discovery of a word fixes its minimum move count, because every generating parent
has the smallest unprocessed distance. Marking only on removal permits duplicate
queue entries and redundant parent assignment.

| Removed word | Newly discovered | Saved parent evidence |
|---|---|---|
| hit | hot | hot ← hit |
| hot | dot, lot | both ← hot |
| dot, lot | dog, log | dog ← dot; log ← lot |
| dog | cog | cog ← dog; reconstruct backward |

The fixed 26-letter alphabet does not make Python string creation free. Each of
26L candidates costs O(L) to construct/hash, giving O(NL²) search time in the
worst case, plus O(NL) input validation. Stored dictionary and discovered strings
use O(NL) space; parent/queue entries add O(N). The returned path uses O(PL) if its
strings are counted, with P words. No quadratic adjacency table is retained.

**Follow-up 1 — return every shortest path.** Predict what is lost when cog stores
only dog. Save *all* parents at the preceding depth, finish the entire winning
layer, and traverse the resulting parent DAG. Output may be exponential; report
output-sensitive bounds rather than promising linear total work.

```mermaid
flowchart TD
  C[cog] -->|"parent at depth 3"| D[dog]
  C -->|"additional shortest parent"| L[log]
  D -->|"parent"| T[dot]
  L -->|"parent"| O[lot]
  T -->|"parent"| H[hot]
  O -->|"parent"| H
```

**Follow-up 2 — large dictionary, one pair.** Bidirectional BFS expands the smaller
frontier from start/end and joins compatible layers. Keep separate visited/depth
maps and reconstruct both halves. It can reduce explored states but does not
remove the need to account for neighbor generation or prove the stopping rule.

Senior depth is deriving the implicit graph and proving shortestness. Lead depth
adds dictionary versioning and query-memory limits if this becomes a service.

Reference: [solution.py](solution.py); tests validate actual edges, optimal length,
unreachable endpoints, identity, duplicates, and malformed words.

```bash
python -m unittest discover -s curriculum/01-code/02-data-structures-algorithms/problems/22-word-ladder -p 'test_*.py'
```

</details>
