# Windows: move boundaries, avoid rescanning

[Curriculum](../../../README.md) · [Data structures and algorithms](../README.md)

> “Our analyzer receives abba. How long is its longest contiguous span with no repeated character?”

The answer is 2, not 3. Trace what the second b invalidates and why seeing the final a must not move the left boundary backward.

This is a short prerequisite lesson. Attempt the complete [longest unique window problem](../problems/04-longest-unique-window/README.md), then [minimum covering window](../problems/05-minimum-covering-window/README.md), with their contracts, tests and changed requirements.

**Build:** Find the longest substring without repeated characters. `abba → 2`.

![Windows: move boundaries, avoid rescanning](../../../../assets/learning/window-moves.svg)

[Static diagram](../../../../assets/learning/window-moves-still.svg)

**The idea:** The active window contains unique characters. Move left to `max(left, last_seen[char] + 1)`.

## First, what is a window?

A **substring** is a contiguous piece of text. In `"abba"`, `"ab"` and `"bb"` are substrings; `"aa"` is not. A window is the current substring between inclusive positions `left` and `right`. Its length is `right - left + 1`. We want the longest window whose characters are all different.

```python
text = "abba"
left, right = 0, 1
print(text[left:right + 1])  # "ab"; Python's slice end is exclusive
last_seen = {"a": 0, "b": 1}  # character -> latest position
```

On the next `b` at position 2, the `b` at position 1 invalidates `"abb"`. Shift `left` to `2`. On the final `a`, its old position 0 lies *outside* the current window, so `left` must stay at 2. The `max` in the formula prevents the boundary from moving backward.

| Character at `right` | `left` after update | Current window | Best length |
| --- | ---: | --- | ---: |
| `a` at 0 | 0 | `"a"` | 1 |
| `b` at 1 | 0 | `"ab"` | 2 |
| `b` at 2 | 2 | `"b"` | 2 |
| `a` at 3 | 2 | `"ba"` | 2 |

**Read the animation:** each shift discards a prefix, never a suffix. The dictionary remembers the *last* position of each character, unlike the two-sum dictionary, which remembers the *first* position of each number.

```python
left = max(left, last_seen.get(char, -1) + 1)
best = max(best, right - left + 1)
last_seen[char] = right
```

`get(char, -1)` returns −1 when the key has not appeared. That makes a first occurrence keep `left` at 0. Write these three lines in this order: move the boundary, measure the valid window, then record the current position.

## Your 45-minute session

1. **5 min:** draw one example and a simple solution.
2. **25 min:** implement `longest_unique` without the reference.
3. **10 min:** use the exact input/output table below; trace the first and last rows by hand.
4. **5 min:** explain the cost and answer the changed requirement.

**Cost:** Repeatedly check substrings: up to O(n³). Last-seen window: O(n) time, O(u) space for u distinct characters.

| `text` | Expected longest length | Why |
| --- | ---: | --- |
| `"abba"` | 2 | `"ab"` and `"ba"` qualify; `"abb"` does not. |
| `"aaaa"` | 1 | Every longer window repeats `a`. |
| `""` | 0 | No characters, so no nonempty window. |
| `"dvdf"` | 3 | `"vdf"` is unique; the old `d` must be discarded. |
| `"tmmzuxt"` | 5 | `"mzuxt"`; the final `t` does not move `left` backward. |

Here `n` is the number of characters and `u` is the number of *distinct* characters stored. Each character enters the window once and `left` only moves right, so total scan work is O(n); the dictionary can hold up to `u` keys. The naïve version can check O(n²) substrings and spend up to O(n) examining each.

**Pass before moving on:** Trace all four characters of abba without moving left backward.

**Changed requirement:** Return the substring, not only its length. Define which answer wins a tie.

<details>
<summary>After attempting: reference and explanation</summary>

Compare `longest_unique` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>

[Previous](01-maps.md) · [Next: Prefix sums: count possible starts](03-prefix.md)
