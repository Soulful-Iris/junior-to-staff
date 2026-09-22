# 03 · Prefix sums: count possible starts

**Build:** Count nonempty contiguous ranges summing to K. `[1,-1,1], 1 → 3`.

![Prefix sums: count possible starts](../../../../assets/learning/prefix-counts.svg)

[Static diagram](../../../../assets/learning/prefix-counts-still.svg)

**The idea:** A prior prefix equals `current_prefix - K`. Store its frequency. Seed `{0:1}` and look up before inserting.

## Your 45-minute session

1. **5 min:** draw one example and a simple solution.
2. **25 min:** implement `subarray_sum` without the reference.
3. **10 min:** test `[0,0], 0 → 3`; negative values; range starting at index zero.
4. **5 min:** explain the cost and answer the changed requirement.

**Cost:** Running sum from each start: O(n²). Frequency map: expected O(n) time and O(n) space.

**Pass before moving on:** Explain why a set undercounts and why sum-based shrinking fails with negative values.

**Changed requirement:** Consume an iterator instead of a stored list. Which memory still grows?

<details>
<summary>After attempting: reference and explanation</summary>

Compare `subarray_sum` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>

[Previous](02-windows.md) · [Next: Sorted data: binary search and intervals](04-order.md)
