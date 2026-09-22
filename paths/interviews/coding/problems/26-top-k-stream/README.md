# 26 · Top k observations in a stream

> “An operations screen receives integer latency samples indefinitely and displays
> the largest k seen so far. Keeping every sample exhausts memory. Preserve exact
> results after every arrival while retaining at most k samples. Do repeated values
> count separately, and what should happen before k arrivals?”

Constructed practice question. Prerequisite: [heaps](../../lessons/06-heaps.md).
A min-heap keeps its smallest member at the root. Its internal array is only
partially ordered; reading that array is not the same as a sorted answer.

| Contract | Required behavior |
|---|---|
| Input | Nonnegative integer k; integer observations through `add(value)` |
| Output | `largest()` returns up to k values in descending order |
| Boundaries | Duplicates count; k=0 retains nothing; negative samples allowed |
| Failure | Negative/noninteger k or noninteger sample raises `ValueError` |
| Scope | All history; fixed k; no deletion, timestamps, or distinct-only semantics |

For k=3 and arrivals `[4,1,7,7,2]`, the successive answers are `[4]`, `[4,1]`,
`[7,4,1]`, `[7,7,4]`, `[7,7,4]`. Distinct-only `[7,4,2]` would violate the contract.
After zero arrivals return `[]`; an invalid sample must leave retained state intact.

```mermaid
flowchart TD
  R["root 4: weakest retained"] -->|"heap child"| A[7]
  R -->|"heap child"| B[7]
  X["incoming 2"] -->|"2 does not beat root; discard"| R
```

Before reading the solution, explain why a *min*-heap helps find the largest
values. Implement arrival and presentation as separate operations.

<details>
<summary>Solution, exchange argument, and follow-ups</summary>

The baseline appends to an unbounded list and sorts after every arrival. For n
arrivals it retains O(n) values and costs O(n log n) for one complete snapshot.
Keeping a sorted array of k values bounds memory but requires O(k) shifts on an
insertion. If k is tiny that may be an acceptable, simpler choice.

Use a min-heap of at most k observations. Fill it initially. Once full, compare an
arrival with the smallest retained value: discard anything no larger, or replace
the root and restore the heap. Equal values need no replacement because observation
identity is excluded; the multiset result is unchanged.

**Invariant:** after each arrival, the heap's multiset equals the largest
min(k,n) observations of the processed prefix. An incoming value below the cutoff
cannot displace a winner. A value above it must replace one weakest winner. This
exchange argument proves exactness without sorting historical losers.

| Arrival | Heap as a multiset | Decision |
|---:|---|---|
| 4, 1, 7 | {1,4,7} | Fill three slots |
| 7 | {4,7,7} | Replace cutoff 1 |
| 2 | {4,7,7} | Discard below cutoff 4 |

Each `add` costs O(log(k + 1)) worst case and O(1) for a discarded value. Retained
state is O(k). `largest()` costs O(k log(k + 1)) time and O(k) additional space for
a sorted snapshot; the caller cannot mutate the heap through that snapshot. Across
n adds the bound is O(n log(k + 1)), with the k=0 branch taking O(n) total work.

**Follow-up 1 — k grows from 3 to 4.** Predict the fourth-largest value after the
example. It is 2, already discarded. A larger heap cannot reconstruct lost history.
Retain a declared maximum k, replay an external log, or explicitly reset the query.

```mermaid
flowchart TD
  L["replayable observation log"] -->|"recompute with k=4"| H["retained: 2,4,7,7"]
  O["old heap: 4,7,7"] -->|"insufficient history alone"| Q["fourth value unknown"]
```

**Follow-up 2 — last five minutes only.** Expiration can remove a winner and reveal
a previously discarded sample. Keep a window-aware ordered multiset or two heaps
with delayed deletion and bounded cleanup. Timestamp storage and tie identities
become necessary; attaching timestamps only to the existing k winners is insufficient.

Senior depth separates update/query complexity and proves multiset behavior.
Lead depth defines retention and approximation policies before promising bounded
memory for changing windows or k values.

Reference: [solution.py](solution.py). Tests compare every seeded prefix against
sorting, check k=0/large k, duplicates, negatives, and independent snapshots.

```bash
python -m unittest discover -s paths/interviews/coding/problems/26-top-k-stream -p 'test_*.py'
```

</details>
