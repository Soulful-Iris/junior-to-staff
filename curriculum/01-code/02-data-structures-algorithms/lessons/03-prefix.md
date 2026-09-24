# Prefix sums: count possible starts

[Curriculum](../../../README.md) · [Choose data structures and reason about algorithms](../README.md)

> “Count all contiguous transaction ranges that sum to 1 in [1,-1,1]. Negative values and repeated cumulative totals are allowed.”

There are three ranges. Explain why a window based only on whether the sum is too large cannot decide which boundary to move.

The coding-practice chapter will apply this tool to complete problems. Here, focus on the mechanism and trace how its state changes.

**Working example:** Count nonempty contiguous ranges summing to K. `[1,-1,1], 1 → 3`.

![Prefix sums: count possible starts](../../../../assets/learning/prefix-counts.svg)

[Static diagram](../../../../assets/learning/prefix-counts-still.svg)

**The idea:** A prior prefix equals `current_prefix - K`. Store its frequency. Seed `{0:1}` and look up before inserting.

## First, what is a prefix sum?

A **subarray** is a contiguous stretch. A prefix sum is the total from the start through the current item. For `[1, -1, 1]`, the running totals after each item are `1, 0, 1`. If a past total was 0 and the current total is 1, the stretch *between* them sums to 1. Negative numbers can make a running total rise or fall, so a window that only shrinks when the total gets too large is unreliable.

```python
counts = {0: 1}  # one empty prefix, before reading any item
prefix = 0
answer = 0
for value in [1, -1, 1]:
    prefix += value
    answer += counts.get(prefix - 1, 0)  # 1 is the desired sum
    counts[prefix] = counts.get(prefix, 0) + 1
print(answer)  # 3
```

This dictionary maps **prefix total → number of earlier times we saw it**. A set would remember only whether a total occurred, losing multiple valid starting positions. `counts.get(key, 0)` means “how many times, or zero if the key is absent.” The seed `{0: 1}` accounts for ranges starting at index 0.

| Item / current total | Needed earlier total | Earlier count | New qualifying ranges |
| --- | ---: | ---: | --- |
| `1` / `1` | 0 | 1 | `[1]` at positions 0–0 |
| `-1` / `0` | −1 | 0 | none |
| `1` / `1` | 0 | 2 | positions 0–2 and 2–2 |

**Read the animation:** the counter on the right is not an index map. It records the *frequency* of a prefix total. Notice the current total is counted only after its matches to earlier totals, excluding an empty range made by using the current state twice.

## Check the mechanism

Predict each expected result, then trace the state that produces it. Explain the boundary case before opening the reference.

**Cost:** Running sum from each start: O(n²). Frequency map: expected O(n) time and O(n) space.

| Numbers, target | Expected count | Qualifying ranges |
| --- | ---: | --- |
| `[1, -1, 1]`, `1` | 3 | positions 0–0, 0–2, 2–2 |
| `[0, 0]`, `0` | 3 | positions 0–0, 0–1, 1–1 |
| `[]`, `0` | 0 | The empty range does not count. |
| `[2, -2, 2]`, `0` | 2 | positions 0–1 and 1–2 |
| `[1, 2]`, `9` | 0 | No qualifying range. |

`n` is the number of input values. Trying all possible starting positions and running to every ending position examines O(n²) ranges. Keeping one running total and a dictionary uses expected O(n) lookup/update work and up to O(n) stored distinct totals. Even with an iterator, the dictionary may still grow with the stream.

**Pass before moving on:** Explain why a set undercounts and why sum-based shrinking fails with negative values.

**Changed requirement:** Consume an iterator instead of a stored list. Which memory still grows?

<details>
<summary>After attempting: reference and explanation</summary>

Compare `subarray_sum` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>
