# Longest increasing subsequence

[Curriculum](../../../../README.md) · [Choose data structures and reason about algorithms](../../README.md) · [All coding problems](../../../../../indexes/coding.md)

> “A telemetry analyzer receives ordered integer measurements. It may skip noisy
> measurements but cannot reorder them. Return a longest strictly increasing
> subsequence, including the chosen values. Can you summarize partial solutions
> without losing the ability to reconstruct a real sequence?”

Constructed practice question. Prerequisites: [binary search](../../lessons/04-order.md)
and [DP state](../../lessons/08-dp.md). A subsequence preserves input order but need
not be contiguous. Strict increase means equal consecutive chosen values are invalid.

| Contract | Required behavior |
|---|---|
| Input | Finite integer sequence |
| Output | Values forming any longest strictly increasing subsequence |
| Boundaries | Empty returns `[]`; equal-only nonempty input returns one value |
| Failure | Noninteger values raise `ValueError`; input is not mutated |
| Scope | One witness; no count of witnesses or streaming deletions |

## The tool before the challenge

For longest *strictly increasing* subsequence, elements may skip positions; that differs from a contiguous window. A `tails` array stores the smallest possible ending value for an increasing subsequence of each length:
```python
from bisect import bisect_left
tails = [2, 5]
i = bisect_left(tails, 3)  # 1; replace tail 5 with 3
tails[i] = 3
```
`tails` is a compact summary, not necessarily a subsequence of the original input. Keep predecessor links if the output needs an actual witness.

### A design choice worth saying aloud

`smallest_tail_by_length` is a search summary, **not** the subsequence to return: replacements can combine elements that never formed one path. Keep predecessor links and original indices if the output needs a witness. Strict increasing uses `bisect_left`; a nondecreasing contract changes the comparison and duplicate case.

<!-- interview-rehearsal:start -->

## What the interviewer expects

The interviewer gives you the scenario and the contract above. Explain what a
successful call returns, walk through one example below, and name what your
state means *before* choosing a data structure.

**Done means:** Values forming any longest strictly increasing subsequence.

Now predict each output before looking at the reference; invalid input should
leave any existing state unchanged unless the contract says otherwise.

### Test-case scenarios to settle before coding

| Case | Exact input or state | Expected result | What it is testing |
|---|---|---|---|
| Representative | `[10,9,2,5,3,7,101,18]` | a length-4 witness such as `[2,3,7,18]` | Return values, not only length. |
| Empty | `[]` | `[]` | No witness exists. |
| All equal | `[2,2,2]` | one `2` | Increasing is strict. |
| Decreasing | `[5,4,3]` | any one value allowed by tie contract | Best length can be one. |
| Tails warning | `[3,5,6,2,4]` | `[3,5,6]` (length 3), **not** the possible tails array `[2,4,6]` | Value 6 preceded 2 and 4; tails are not one actual subsequence. |
| Invalid/atomic | noninteger/bool element | `ValueError`; input unchanged | Validate before reconstruction state. |

For each case, show which branch or state change produces that result.

<!-- interview-rehearsal:end -->

`[10,9,2,5,3,7,101,18]` can return `[2,3,7,18]` of length four. `[2,2,2]` returns
`[2]`, not all three. Sorting the input would change order and solve another task.
Ask whether the caller actually means nondecreasing: equality changes which binary
search boundary is correct.

```mermaid
flowchart TD
  A["2 at index 2"] -->|"chosen later index"| B["3 at index 4"]
  B -->|"chosen later index"| C["7 at index 5"]
  C -->|"chosen later index"| D["18 at index 7"]
  X["5 at index 3; skipped"] -->|"alternative middle choice"| C
```

Implement an O(n²) solution first if needed. Then explain what one length-l partial
sequence can offer a future value that another sequence of the same length cannot.

<details>
<summary>Solution, dominance, and follow-ups</summary>

The quadratic DP defines `length[i]` as the best sequence ending at i, scanning
earlier j with `values[j] < values[i]`. It is correct and easy to reconstruct, but
does O(n²) comparisons. The improvement follows a dominance argument: among
subsequences of the same length, the smaller final value permits at least as many
future extensions.

Maintain `tails[l-1]`, the smallest ending value of any length-l increasing
subsequence in the processed prefix. For x, find the first tail ≥x using lower
bound. Replace it, or append if no such tail exists. Tails remain increasing.
Store the input index associated with each tail and each element's predecessor
index before replacement, then reconstruct from the final longest tail.

**Invariant:** each tail is achievable at its claimed length, and no larger tail
is needed to decide future extendability. However the tails array as a whole need
not be one subsequence: its entries may come from incompatible input positions.
Predecessor links record historical compatible choices; replacing a tail does not
rewrite already stored predecessors.

| Input prefix ending with | Tails | Meaning |
|---|---|---|
| 3,5,6 | [3,5,6] | Length three exists |
| then 2 | [2,5,6] | Better length-one end |
| then 4 | [2,4,6] | Better length-two end; not a real length-three witness |

For n values, binary searches take O(n log(n+1)) time. Tails, input copy, indices,
and predecessors use O(n) auxiliary space; returned witness uses O(L). If only
length is requested, omit predecessor history and retain O(L) tails. The provided
implementation returns a witness and therefore honestly retains linear history.

**Follow-up 1 — nondecreasing subsequence.** Predict `[2,2,2]`: length three.
Use the first tail strictly greater than x (upper bound), so equal values extend
instead of replacing. Draw how the same observations now create three lengths.

```mermaid
flowchart TD
  A["first 2: length 1"] -->|"equality allowed"| B["second 2: length 2"]
  B -->|"equality allowed"| C["third 2: length 3"]
```

**Follow-up 2 — count longest subsequences.** A single minimal tail loses counts
and alternatives. Use quadratic DP storing `(best_length,count)` per endpoint,
or coordinate-compressed range structures that combine length and count carefully.
Define whether equal values at different indices count as different subsequences;
that decision changes the required counting semantics.

Senior depth explains the dominance proof, strict boundary, and why reconstruction
cannot simply return tails. Lead depth questions whether witness history fits a
long-running stream before promising bounded memory.

Reference: [solution.py](solution.py); tests use exhaustive subsets for small
seeded inputs and explicitly catch the “return tails” mistake.

```bash
python -m unittest discover -s curriculum/01-code/02-data-structures-algorithms/problems/34-longest-increasing-subsequence -p 'test_*.py'
```

</details>
