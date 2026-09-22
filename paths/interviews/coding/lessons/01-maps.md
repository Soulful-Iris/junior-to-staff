# 01 · Maps: remember earlier work

> “Given prices [2,7,11,15] and a budget of 9, return two different positions that exactly spend it. Can the same position count twice?”

The result is (0,1); [3] cannot make 6. State which earlier positions are available before choosing a lookup structure.

This is a short prerequisite lesson. Attempt the complete [two sum problem](../problems/01-two-sum/README.md), then [group anagrams](../problems/03-group-anagrams/README.md), with their contracts, tests and changed requirements.

**Build:** Return two distinct indices that sum to a target. Try `[2,7,11,15], 9 → (0,1)`.

![Maps: remember earlier work](../../../../assets/learning/map-lookup.svg)

[Static diagram](../../../../assets/learning/map-lookup-still.svg)

**The idea:** For each value, ask whether its complement appeared earlier. Look up before inserting so you cannot reuse one index.

## Your 45-minute session

1. **5 min:** draw one example and a simple solution.
2. **25 min:** implement `two_sum` without the reference.
3. **10 min:** test `[3,3], 6`; `[3], 6`; an empty input; no valid pair.
4. **5 min:** explain the cost and answer the changed requirement.

**Cost:** Try every pair: O(n²). Remember earlier values: expected O(n) time, O(n) space.

**Pass before moving on:** Name the map key and value. Explain exactly why lookup comes before insertion.

**Changed requirement:** Return every matching pair. Explain why one saved index per value may no longer suffice.

<details>
<summary>After attempting: reference and explanation</summary>

Compare `two_sum` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>

[Coding start](../README.md) · [Next: Windows: move boundaries, avoid rescanning](02-windows.md)
