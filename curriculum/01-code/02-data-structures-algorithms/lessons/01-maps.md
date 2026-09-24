# Maps: remember earlier work

[Curriculum](../../../README.md) · [Choose data structures and reason about algorithms](../README.md)

> “Given prices [2,7,11,15] and a budget of 9, return two different positions that exactly spend it. Can the same position count twice?”

**What the interviewer is asking:** Return the *positions* of two different items whose values add to the target. Positions start at 0. In `[2, 7, 11, 15]`, the values at positions 0 and 1 are `2 + 7 = 9`, so the answer is `(0, 1)`. A list with only one `3` cannot produce two distinct positions totaling 6; `[3, 3]` can.

## First, what is a map?

A **map** stores a value under a key so you can look up that key later. Python calls it a **dictionary** (`dict`). Here we remember values already encountered and where they appeared: the key `2` stores index `0`. Braces create a dictionary; a colon separates a key from its value:

```python
visited = {}
visited[2] = 0
print(visited)       # {2: 0}
print(2 in visited)  # True
print(visited[2])    # 0
```

This is different from a list: `prices[0]` retrieves the value at position 0, which is `2`; `visited[2]` retrieves the position previously recorded for value 2, which is `0`. The dictionary lets us find earlier values without scanning the list again. The same idea works for prices, transactions, or any stream of numbers.

## Watch the question change at each position

At index `j`, calculate `target - value`, called the **complement**. Ask whether that complement appeared earlier. If it did, return its recorded index and `j`. Otherwise, remember the current value and its index for later lookups.

| Current index `j` | Value | Dictionary *before* lookup | Decision |
| ---: | ---: | --- | --- |
| 0 | 2 | `{}` | Complement `7` is absent; remember `2 → 0`. |
| 1 | 7 | `{2: 0}` | Complement `2` appeared at index 0; return `(0, 1)`. |

The values 11 and 15 are never visited: the first valid right-hand index is 1. **Lookup comes before insertion** so that `[3]` with target 6 does not falsely match index 0 to itself. With `[3, 3]`, the first 3 records `3 → 0` and the second 3 finds it at index 1.

![Maps: remember earlier work](../../../../assets/learning/map-lookup.svg)

[Static diagram](../../../../assets/learning/map-lookup-still.svg)

**Read the picture:** The numbered boxes on the left are indices 0–3, holding the prices. The large box on the right is the **Python dictionary**: `2 → 0` means “value 2 appeared at index 0.” The green arrow remembers it; the orange arrow looks for it when 7 arrives, because `9 - 7 = 2`. The returning arrow carries the two *indices*, `(0, 1)`. Pause the motion after each arrow and predict what is in the dictionary.

## From a direct search to the dictionary

The simple approach tries each pair of distinct indices. This map remembers earlier values so each new item can look up its complement directly. This short snippet shows the main idea; the full problem also validates input types.

```python
def two_sum(prices: list[int], target: int) -> tuple[int, int] | None:
    visited: dict[int, int] = {}
    for j, value in enumerate(prices):
        complement = target - value
        if complement in visited:
            return visited[complement], j
        visited.setdefault(value, j)
    return None
```

`setdefault(value, j)` saves an index only if the value has not appeared already. This keeps the *earliest* eligible index if values repeat. Before each lookup, the dictionary holds only values from **earlier** indices; insertion after lookup prevents reusing the current item. The coding-practice chapter adds validation and more difficult tie cases.

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

**Before moving on:** Say what `2 → 0` means. Trace `[3, 3]` aloud and explain why reversing lookup/insertion would falsely accept `[3]`.

**Changed requirement:** Return every matching pair. Explain why one saved index per value may no longer suffice.

<details>
<summary>After attempting: reference and explanation</summary>

First predict `[3, 3, 3]`, target 6: `(0, 1)`, `(0, 2)`, `(1, 2)`. Keeping only the first index of value 3 would lose `(1, 2)`. Store a **list of earlier indices** for each encountered value instead; generating `p` pairs takes at least O(p) output work. Compare the validated [two sum solution](../problems/01-two-sum/solution.py).

</details>

[Coding start](../practice-sequence.md) · [Next: Windows: move boundaries, avoid rescanning](02-windows.md)
