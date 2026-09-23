# Maps: remember earlier work

[Curriculum](../../../README.md) · [Data structures and algorithms](../README.md)

> “Given prices [2,7,11,15] and a budget of 9, return two different positions that exactly spend it. Can the same position count twice?”

**What the interviewer is asking:** Return the *positions* of two different items whose values add to the target. Positions start at 0. In `[2, 7, 11, 15]`, the values at positions 0 and 1 are `2 + 7 = 9`, so the answer is `(0, 1)`. A list with only one `3` cannot produce two distinct positions totaling 6; `[3, 3]` can.

## First, what is a map?

A **map** stores a value under a key so you can look up that key later. Python calls it a **dictionary** (`dict`). Here the key is a number we saw earlier, and the stored value is its *first index* in the list. Name the dictionary for both sides of that relationship and the rule for repeated values: `first_index_by_value`. It works for prices, transaction amounts, or any list of numbers. Braces create a dictionary; a colon separates a key from its value:

```python
first_index_by_value = {}
first_index_by_value[2] = 0
print(first_index_by_value)       # {2: 0}
print(2 in first_index_by_value)  # True
print(first_index_by_value[2])    # 0
```

This is different from a list: `prices[0]` means “the value *at index* 0”; `first_index_by_value[2]` means “the *first index saved under value* 2.” The keys come from input values, not from list indices. The name describes `value → first index`; `first_position` describes only the right-hand side, so a reader has to reconstruct the key from surrounding code. If the requirement changes to the *most recent* occurrence, the name and update rule must change together.

## Watch the question change at each position

At position `j`, the value is `value`. The missing value is `target - value`, called its **complement**. Before processing `j`, the dictionary contains only positions smaller than `j`. Ask whether that missing value is a key; if it is, return the stored earlier position and `j`.

| Current position `j` | Value | Missing value `9 - value` | Dictionary *before* lookup | Decision |
| ---: | ---: | ---: | --- | --- |
| 0 | 2 | 7 | `{}` | No 7 yet; save `{2: 0}`. |
| 1 | 7 | 2 | `{2: 0}` | Key 2 exists at position 0; return `(0, 1)`. |

The values 11 and 15 are never visited: the first valid right-hand position is 1. **Lookup comes before insertion** so that `[3]` with target 6 does not falsely match position 0 to itself. With `[3, 3]`, the first 3 is saved at 0 and the second 3 finds it at 1.

![Maps: remember earlier work](../../../../assets/learning/map-lookup.svg)

[Static diagram](../../../../assets/learning/map-lookup-still.svg)

**Read the picture:** The numbered boxes on the left are list positions 0–3, holding the prices. The large box on the right is the **Python dictionary**: `2 → 0` means “value 2 was first seen at position 0.” The green arrow saves that entry; the orange arrow looks for 2 when the current value is 7. The returning arrow carries the two *positions*, `(0, 1)`. Pause the motion after each arrow and predict what is in the dictionary.

## From a direct search to the dictionary

The simple approach tries each pair of different positions. The map saves the earliest position for each value, which also makes the answer deterministic if a value repeats. This short snippet shows the main idea; the full problem also validates input types.

```python
def two_sum(prices: list[int], target: int) -> tuple[int, int] | None:
    first_index_by_value: dict[int, int] = {}
    for j, value in enumerate(prices):  # j is the current position
        complement = target - value
        if complement in first_index_by_value:
            return first_index_by_value[complement], j
        first_index_by_value.setdefault(value, j)
    return None                          # examined every position; no pair
```

`j` is the right-hand index in the requested pair; that short name is useful inside this small loop. `complement` names the value needed to finish the sum. `setdefault(value, j)` adds the key only if absent. Without that guard, overwriting an earlier index can break the contract “smallest earlier index.” This name and update rule together express the invariant: **before each lookup, the dictionary maps each previously seen value to its earliest index**. The complete [two sum problem](../problems/01-two-sum/README.md) adds validation and more difficult tie cases.

## Try inputs that could break your answer

The exact return contract here is two distinct indices `(i, j)` with `i < j`, smallest possible `j` and then smallest `i`, or `None` if none exists. Read each expected result before checking the implementation.

| `prices`, `target` | Expected | Why |
| --- | --- | --- |
| `[2, 7, 11, 15]`, `9` | `(0, 1)` | `2 + 7 = 9`. |
| `[3, 3]`, `6` | `(0, 1)` | Same number, **different** positions. |
| `[3]`, `6` | `None` | There is only one position; it cannot be used twice. |
| `[]`, `9` | `None` | No positions exist. |
| `[1, 2, 3]`, `20` | `None` | No values form 20. |
| `[1, 4, 4]`, `5` | `(0, 1)` | The first valid right-hand position wins. |

For the full problem, `True` is not accepted as an integer despite Python normally treating `bool` as a subclass of `int`: `two_sum([True, 2], 3)` must raise `ValueError`.

## Explain time and extra memory in ordinary words

`n` means the number of prices. Trying all pairs can check roughly `n × (n − 1) / 2` pairs, so we say **O(n²) time**: work grows approximately with the square of input size. The dictionary version visits each position once and normally makes one quick hash lookup and at most one insertion per position: **expected O(n) time**. In the worst no-answer case it may remember every distinct value: **O(n) extra space**. “Extra” excludes the input list; it counts the dictionary. Hash lookups are *expected* fast, not a promise against pathological collisions.

**Before moving on:** Point to the dictionary key and value in `{2: 0}`. Trace `[3, 3]` aloud and explain why reversing lookup/insertion would falsely accept `[3]`.

**Changed requirement:** Return every matching pair. Explain why one saved index per value may no longer suffice.

<details>
<summary>After attempting: reference and explanation</summary>

First predict `[3, 3, 3]`, target 6: `(0, 1)`, `(0, 2)`, `(1, 2)`. One saved index for value 3 loses two pairs. A dictionary of **lists of earlier indices** can retain them; generating `p` pairs takes at least O(p) output work. Compare the validated `two_sum` in [algorithms.py](../algorithms.py). Reimplement tomorrow without copying.

</details>

[Coding start](../practice-sequence.md) · [Next: Windows: move boundaries, avoid rescanning](02-windows.md)
