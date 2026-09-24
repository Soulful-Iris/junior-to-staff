# Stacks: keep unresolved work

[Curriculum](../../../README.md) · [Data structures and algorithms](../README.md)

> “For [73,74,71,75], return how long each day waits for a strictly warmer one.”

The output is [1,2,1,0]. Equal temperatures do not qualify. Identify the unresolved days before trying to optimize repeated forward scans.

The coding-practice chapter will apply this tool to complete problems. Here, focus on the mechanism and trace how its state changes.

**Working example:** For each temperature, return days until a strictly warmer day. `[73,74,71,75] → [1,2,1,0]`.

![Stacks: keep unresolved work](../../../../assets/learning/monotonic-stack.svg)

[Static diagram](../../../../assets/learning/monotonic-stack-still.svg)

**The idea:** Store unresolved indices in non-increasing temperature order. A new warmer value resolves colder indices at the top.

## First, what is a stack?

A **stack** keeps the most recently added item on top. Python lists can push with `append` and pop with `pop`. Here the stack holds **day positions**, not temperatures: we must eventually return how many days each earlier position waited. The temperatures at those positions are non-increasing from the bottom to the top of the stack.

```python
temperatures = [73, 74, 71, 75]
waiting = []                  # indices still waiting for a warmer day
answer = [0] * len(temperatures)
for day, temperature in enumerate(temperatures):
    while waiting and temperatures[waiting[-1]] < temperature:
        earlier = waiting.pop()
        answer[earlier] = day - earlier
    waiting.append(day)
print(answer)  # [1, 2, 1, 0]
```

At 74, day 0 is resolved. At 75, both 71 (day 2) and 74 (day 1) are popped. Equal temperatures stay on the stack because the requirement is **strictly warmer**, not at least as warm. The animation's moving indices represent unresolved days waiting for an answer.

| Day / temperature | Stack after day (indices) | Answer so far |
| --- | --- | --- |
| 0 / 73 | `[0]` | `[0, 0, 0, 0]` |
| 1 / 74 | `[1]` | `[1, 0, 0, 0]` |
| 2 / 71 | `[1, 2]` | `[1, 0, 0, 0]` |
| 3 / 75 | `[3]` | `[1, 2, 1, 0]` |

## Check the mechanism

Predict each expected result, then trace the state that produces it. Explain the boundary case before opening the reference.

**Cost:** Scan forward for each day: O(n²). Monotonic stack: O(n) time and O(n) space.

| Temperatures | Expected waits | Why |
| --- | --- | --- |
| `[73, 74, 71, 75]` | `[1, 2, 1, 0]` | Day 3 resolves days 1 and 2. |
| `[70, 70]` | `[0, 0]` | Equal is not warmer. |
| `[75, 74, 73]` | `[0, 0, 0]` | No later warmer day. |
| `[70, 60, 80]` | `[2, 1, 0]` | One arrival resolves two waiting days. |
| `[]` | `[]` | No days. |

The `while` loop looks nested, but each of `n` indices enters the stack once and leaves it at most once, so total push/pop work is O(n). At worst a decreasing list leaves all `n` indices waiting: O(n) extra space. Trying every later day for every start is O(n²).

**Pass before moving on:** Prove linear total work by counting pushes and pops, even with the nested loop.

**Changed requirement:** Change strictly warmer to warmer-or-equal. Which comparison changes?

<details>
<summary>After attempting: reference and explanation</summary>

Compare `daily_temperatures` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>
