# 02 · Windows: move boundaries, avoid rescanning

**Build:** Find the longest substring without repeated characters. `abba → 2`.

![Windows: move boundaries, avoid rescanning](../../../../assets/learning/window-moves.svg)

[Static diagram](../../../../assets/learning/window-moves-still.svg)

**The idea:** The active window contains unique characters. Move left to `max(left, last_seen[char] + 1)`.

## Your 45-minute session

1. **5 min:** draw one example and a simple solution.
2. **25 min:** implement `longest_unique` without the reference.
3. **10 min:** test `abba`; `aaaa`; empty text; a repeated character outside the current window.
4. **5 min:** explain the cost and answer the changed requirement.

**Cost:** Repeatedly check substrings: up to O(n³). Last-seen window: O(n) time, O(u) space for u distinct characters.

**Pass before moving on:** Trace all four characters of abba without moving left backward.

**Changed requirement:** Return the substring, not only its length. Define which answer wins a tie.

<details>
<summary>After attempting: reference and explanation</summary>

Compare `longest_unique` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>

[Previous](01-maps.md) · [Next: Prefix sums: count possible starts](03-prefix.md)
