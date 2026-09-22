# Coding foundations · complete practice problems

These are constructed practice questions, with no company attribution. Read the
candidate brief and contract before opening each page's solution disclosure.
Explain a baseline, name the invariant, implement independently, then use the
reference tests and a changed requirement to check your reasoning.

## Ordered progression

| Order | Problem | Prerequisite and property to explain |
|---:|---|---|
| 1 | [Two sum](01-two-sum/README.md) | Map lookup; earliest-index and lookup-before-insert invariants |
| 2 | [Valid anagram](02-valid-anagram/README.md) | 1; multiplicity and exact Unicode code-point semantics |
| 3 | [Group anagrams](03-group-anagrams/README.md) | 2; canonical keys and deterministic group order |
| 4 | [Longest unique window](04-longest-unique-window/README.md) | 1; forward-only boundaries and half-open indices |
| 5 | [Minimum covering window](05-minimum-covering-window/README.md) | 2, 4; occurrence deficits and shortest valid boundaries |
| 6 | [Subarray sum count](06-subarray-sum-count/README.md) | 1; prefix differences and historical frequencies |
| 7 | [Product except self](07-product-except-self/README.md) | 6; exclusive summaries and output versus working space |
| 8 | [Longest consecutive run](08-longest-consecutive/README.md) | 1; unique starts and aggregate work bounds |
| 9 | [Merge intervals](09-merge-intervals/README.md) | [Ordered data](../lessons/04-order.md); covered-set invariants and endpoint policy |
| 10 | [Meeting room capacity](10-meeting-room-capacity/README.md) | 9; multiplicity, event ordering, and capacity lower bounds |
| 11 | [Binary search boundary](11-binary-search-boundary/README.md) | Ordered data, 4; false/unknown/true regions and validation cost |
| 12 | [Rotated array search](12-rotated-array-search/README.md) | 11; ordered-half reasoning and duplicate ambiguity |
| 13 | [Shipping capacity](13-shipping-capacity/README.md) | 11; monotone feasibility and a separate greedy proof |
| 14 | [Reverse linked list](14-reverse-linked-list/README.md) | 7; node identity, pointer partitions, and mutation ownership |
| 15 | [Linked-list cycle entry](15-linked-list-cycle-entry/README.md) | 14; relative motion, entry proof, and read-only diagnostics |
| 16 | [Merge sorted lists](16-merge-sorted-lists/README.md) | 14, 15; stable identity-preserving splicing and shared-tail rejection |
| 17 | [Tree level order](17-tree-level-order/README.md) | 14; node/edge/depth definitions, FIFO frontiers, and tree-versus-DAG semantics |
| 18 | [Validate BST](18-validate-bst/README.md) | 11, 17; inherited bounds and boolean recursive return state |
| 19 | [Lowest common ancestor](19-lowest-common-ancestor/README.md) | 17, 18; identity, presence masks, postorder state, and absent selections |
| 20 | [Tree diameter](20-tree-diameter/README.md) | 17, 19; upward branch height versus local two-branch path |

Each page contains its local test command. To check this completed foundation
set from the repository root, run each suite in its own process so local
`solution` modules do not collide:

```bash
python - <<'PY'
from pathlib import Path
import subprocess
import sys

root = Path('paths/interviews/coding/problems')
for folder in sorted(root.iterdir()):
    if folder.is_dir() and folder.name[:2].isdigit() and 1 <= int(folder.name[:2]) <= 20:
        print(folder.name, flush=True)
        subprocess.run([sys.executable, '-m', 'unittest', '-v', 'test_solution.py'],
                       cwd=folder, check=True)
PY
```

## Coverage and limits

Problems 1–10 each have exact examples, boundary/invalid-input cases, and either
an exhaustive small-input oracle or deterministic randomized properties. The
oracles use a different approach: pair enumeration, sorting, direct substring
or range sums, explicit exclusion products, and occupied-time coverage. Tests
also cover tie-breaking, Unicode policy, duplicates, zero/negative values,
touching endpoints, and nonmutation where those contracts apply.

Problems 11–13 add linear boundary/rotation oracles and an exhaustive legal
partition oracle for shipping. The checked search wrappers honestly cost O(n)
validation even though their search loops use O(log n) comparisons. Problems
14–15 test identity, every small cycle entry position, nonmutation on rejection,
and 10,000-node chains without relying on recursion.

Problem 16 checks stable node order against a sorting oracle, malformed/cyclic
inputs, and shared-tail rejection before mutation. Problems 17–20 compare tree
results with independent depth-first grouping, inorder ordering, root-path
intersection, and all-pairs unweighted distance oracles. They test equal values
on distinct identities, absent/same-node LCA queries, malformed links, shared
children, cycles, and 3,000–5,000-node skewed trees. Every public tree function
uses an explicit stack or queue, and its O(n) structural-validation memory is
included in the stated bounds.

The complete foundation set has **20 standalone suites and 45 test methods**;
exhaustive loops and seeded cases perform many assertions within those methods.
Reference tests pass locally with Python's standard-library unittest runner.
Diagram rendering is a separate repository integration check, not evidence
provided by the unit suites.

All references use Python's standard library. Follow-up solutions are taught as
approaches and changed-state visuals; they are not advertised as implemented
APIs. Complexity assumes unit-cost arithmetic unless a lesson explicitly notes
large-integer cost. Hash-based bounds are expected, and Python sorting workspace
counts toward auxiliary memory. Passing these suites checks supplied code; an
unfamiliar independent attempt is separate evidence.

Senior practice: derive a test that would break the tempting shortcut, then
defend the proof and resource bounds. Lead practice: keep that coding floor and
explain API semantics, ownership, and migration when the follow-up changes the
representation. These are practice expectations, not hiring predictions.

For a frontend/product emphasis, revisit 2–5 for text/index semantics and 9–10
for scheduling contracts. For infrastructure/storage, emphasize 6, 11–13 and
14–20 for numeric boundaries, ownership, and deep structures. Both detours retain
the same independent implementation and testing requirement; no role detour
turns a supplied reference solution into an assessment.

Node classes are deliberately local to each problem so every folder runs by
itself. Build fixtures with that problem's `solution.Node`; importing a different
problem's Node class is not part of its accepted input contract.

[Coding home](../README.md)
