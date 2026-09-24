# Maintain an exact streaming median

[Curriculum](../../../../README.md) · [Data structures and algorithms](../../README.md) · [All coding problems](../../../../../indexes/coding.md)

> “A monitoring process receives integer observations and asks for the median after
> each arrival. Re-sorting all history is too expensive. Keep an exact answer,
> including the average of the middle pair when the count is even. What state
> must grow even if a query only returns one number?”

Constructed practice question. Prerequisite: [heaps](../../lessons/06-heaps.md).
The median divides ordered observations into lower and upper halves. A max-heap
exposes the largest lower-half value; Python's min-heap can represent it by negation.

| Contract | Required behavior |
|---|---|
| Input | Integer observations through `add(value)` |
| Output | `median()` returns an exact `fractions.Fraction` |
| Boundaries | Odd count uses middle value; even count averages middle pair; duplicates count |
| Failure | Empty median or noninteger observation raises `ValueError` |
| Scope | All history, append only; no window removal, approximation, or constant-memory promise |

## The tool before the challenge

The median splits sorted values into two halves. Two heaps can maintain that split incrementally: a max-heap for the lower half (Python uses negated numbers) and a min-heap for the upper:
```python
from heapq import heappush
from fractions import Fraction
lower, upper = [], []
heappush(lower, -3)  # lower-half maximum is -lower[0] = 3
heappush(upper, 7)   # upper-half minimum is upper[0] = 7
print(Fraction(-lower[0] + upper[0], 2))  # Fraction(5, 1)
```
After each add, rebalance sizes and enforce every lower value ≤ every upper value. Ask how the contract represents half-integer medians.

### A design choice worth saying aloud

`lower_half` and `upper_half` own opposite sides of the median; Python negates lower values to emulate a max-heap. Keep the size difference at most one and every lower value ≤ every upper value. Return `Fraction` for exact half-integers, including inputs too large for lossless float conversion.

<!-- interview-rehearsal:start -->

## What the interviewer expects

The interviewer gives you the scenario and the contract above. Explain what a
successful call returns, walk through one example below, and name what your
state means *before* choosing a data structure.

**Done means:** `median()` returns an exact `fractions.Fraction`.

Now predict each output before looking at the reference; invalid input should
leave any existing state unchanged unless the contract says otherwise.

### Test-case scenarios to settle before coding

| Case | Exact input or state | Expected result | What it is testing |
|---|---|---|---|
| Odd count | add 5,1,9 | `Fraction(5,1)` | Median is the ordered middle. |
| Even count | add 1,2 | `Fraction(3,2)` | Return an exact average. |
| Duplicates | add 4,4,4,4 | `Fraction(4,1)` | Multiplicity is preserved. |
| Empty | median before any add | `ValueError` | No sentinel number represents absence. |
| Huge integers | two values beyond float precision | exact `Fraction` | Do not overflow or round through float. |
| Invalid/atomic | boolean/noninteger observation | `ValueError`; prior median unchanged | Heap balance survives rejected input. |

For each case, show which branch or state change produces that result.

<!-- interview-rehearsal:end -->

After arrivals `[5,1,9,2]`, medians are `5`, `3`, `5`, and `7/2`. The final answer
is not one of the observed values. Negative and arbitrarily large Python integers
are accepted; conversion through a float could overflow or round. Ask whether
exact fractions are appropriate for the caller's display/API contract.

```mermaid
flowchart TD
  L["lower max-heap: 2,1"] -->|"largest lower = 2"| M["median = (2+5)/2"]
  H["upper min-heap: 5,9"] -->|"smallest upper = 5"| M
```

Implement independently. State both invariants: a size rule alone is insufficient,
and correctly ordered halves alone do not identify the middle if sizes drift.

<details>
<summary>Solution, balancing, and follow-ups</summary>

Appending then sorting n observations costs O(n log n) for one snapshot. Maintaining
a sorted list makes median lookup cheap but insertion O(n) because values shift.
Two heaps avoid maintaining the full order inside either half; only their boundary
values matter for median selection.

Insert into lower if it is empty or the observation is no greater than lower's
maximum; otherwise insert into upper. If lower exceeds upper by more than one,
move lower's maximum to upper. If upper becomes larger, move its minimum to lower.
For odd totals return lower's maximum; for even totals average both roots exactly.

**Invariant:** every lower value is ≤ every upper value, and lower has either the
same size as upper or exactly one extra. Insertion chooses a valid side relative
to the dividing value. Moving the appropriate extreme during rebalancing preserves
cross-half order. Thus the roots are exactly the middle one/two order statistics.

| Arrival | Lower values | Upper values | Median |
|---:|---|---|---|
| 5 | {5} | {} | 5 |
| 1 | {1} | {5} | 3 |
| 9 | {1,5} | {9} | 5 |
| 2 | {1,2} | {5,9} | 7/2 |

Each arrival performs O(log(n+1)) heap work; a query reads O(1) roots. State is
O(n) values and O(1) per-operation working slots, excluding growing heap storage.
These are word-model costs. Large integer comparisons, negation, and Fraction
construction also depend on operand bit length; exactness is preserved rather
than treating conversion to float as a harmless presentation step.

**Follow-up 1 — delete expired observations.** Predict the median after deleting
1 from the example: remaining `[2,5,9]` has median 5. A heap cannot directly remove
an arbitrary buried entry cheaply. Use indexed heaps, an ordered multiset, or lazy
deletion with unique identities, logical size counts, root pruning, and compaction.

```mermaid
flowchart TD
  A["lower physical heap contains expired 1"] -->|"mark identity deleted"| D["logical lower size decreases"]
  D -->|"rebalance with upper root 5"| B["live lower: 2,5; upper:9"]
  B -->|"read live root"| M["median 5"]
```

**Follow-up 2 — merge summaries from several machines.** Averaging local medians
does not produce the global median: partition sizes and value distributions matter.
For exact arbitrary values, retain enough order information or exchange selection
queries over distributed data. For bounded memory, choose an approximate quantile
summary and define its error guarantee; the two heaps are not a compact mergeable
summary just because querying them is constant-time.

Senior depth proves both invariants and checks every prefix against sorting.
Lead depth distinguishes exact, approximate, windowed, and distributed contracts
before committing to storage and communication budgets.

Reference: [solution.py](solution.py); tests verify all cross-half values, sizes,
seeded prefix medians, empty behavior, and integers too large for floats.

```bash
python -m unittest discover -s curriculum/01-code/02-data-structures-algorithms/problems/41-streaming-median -p 'test_*.py'
```

</details>
