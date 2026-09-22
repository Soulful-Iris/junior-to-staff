# 04 · Sorted data: binary search and intervals

**Build:** Find the first index ≥ target; then merge overlapping closed intervals.

![Sorted data: binary search and intervals](../../../../assets/learning/binary-halving.svg)

[Static diagram](../../../../assets/learning/binary-halving-still.svg)

**The idea:** Search keeps `[lo, hi)` shrinking. Merging sorts by start, so only the last emitted interval can overlap the next.

Closed: `[1,3] + [3,4] → [1,4]`. Half-open meetings: `[1,3)` and `[3,4)` do not conflict.

## Your 45-minute session

1. **5 min:** draw one example and a simple solution.
2. **25 min:** implement `lower_bound, merge_intervals` without the reference.
3. **10 min:** test `[1,2,2,5], 2 → 1`; empty list; target beyond the end; nested intervals; touching endpoints.
4. **5 min:** explain the cost and answer the changed requirement.

**Cost:** Search: O(log n) time, O(1) space on sorted data. Merge: O(n log n) time, O(n) space including the sorted copy.

**Pass before moving on:** Explain both midpoint updates and draw the difference between closed and half-open intervals.

**Changed requirement:** Calendar meetings are half-open intervals. Should 09:00–10:00 merge with 10:00–11:00?

<details>
<summary>After attempting: reference and explanation</summary>

Compare `lower_bound, merge_intervals` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>

[Previous](03-prefix.md) · [Next: Graphs: visit once, then track prerequisites](05-graphs.md)
