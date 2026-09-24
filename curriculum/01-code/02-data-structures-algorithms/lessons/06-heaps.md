# Heaps: keep the next best candidate

[Curriculum](../../../README.md) · [Data structures and algorithms](../README.md)

> “A stream is too large to sort after every update. Keep its three largest observations. What does the smallest retained value tell you about a new arrival?”

With retained [4,7,7], discard 2 but admit 9 and remove 4. Then ask why a cheapest tentative route can still have an obsolete heap entry.

The coding-practice chapter will apply this tool to complete problems. Here, focus on the mechanism and trace how its state changes.

**Working example:** Return the K **largest observations** (duplicates count), then compute shortest distances with nonnegative edge weights. “Largest” is different from “most frequent”: a value seen once can be largest.

```mermaid
flowchart TD
  A["A: distance 0"] -->|10| B["B: first 10, improved to 2"]
  A -->|1| C["C: distance 1"]
  C -->|1| B
  B --> Q["Heap still contains old B:10"]
  Q --> S["Skip when popped: 10 is stale"]
```

**The idea:** A heap orders the next candidate, not every element. Dijkstra skips stale entries whose distance is no longer current.

## First, what does a heap actually guarantee?

A Python `heapq` is a **min-heap**: its smallest value is always at position 0. The *rest of its internal list is not sorted*. `heappush` and `heappop` each take O(log k) work for k retained entries. To retain the three largest arrivals, keep the **smallest winner at the root**, ready to evict when a larger number arrives.

```python
from heapq import heappush, heapreplace
winners = []
for value in [4, 7, 7, 2, 9]:
    if len(winners) < 3:
        heappush(winners, value)
    elif value > winners[0]:
        heapreplace(winners, value)
print(sorted(winners, reverse=True))  # [9, 7, 7]
```

Before the 9 arrives, the retained values are `[4, 7, 7]`; arrival 2 loses to the smallest winner, 4. When 9 arrives it replaces 4. The diagram below shows *heap repair*, not a sorted array. Another use of a heap is Dijkstra's shortest paths: it selects the **cheapest tentative route**, and an older, more expensive entry can stay in the heap after an improved route appears.

![Repair the heap along one branch](../../../../assets/learning/heap-sift.svg)

[Static view](../../../../assets/learning/heap-sift-still.svg)

## Check the mechanism

Predict each expected result, then trace the state that produces it. Explain the boundary case before opening the reference.

**Cost:** Top k largest stream: O(n log(k+1)) updates, O(k) retained space. Lazy-heap Dijkstra: O(V + E log(E+1)) time, O(V+E) space.

| Task / input | Expected | Boundary |
| --- | --- | --- |
| Top 2, arrivals `[4, 1, 7, 3]` | `[7, 4]` | Discard smaller arrivals. |
| Top 2, arrivals `[5, 5, 4]` | `[5, 5]` | Repeated observations count separately. |
| Top 0, arrivals `[4, 7]` | `[]` | Store nothing. |
| Top 5, arrivals `[4, 7]` | `[7, 4]` | Return only what arrived. |
| Routes `A→B:10, A→C:1, C→B:1` | Best A→B is 2 | The old cost-10 heap entry is stale. |
| Source A, isolated D | Distance to D is infinity | Do not invent a route. |
| Edge cost −1 | Reject for Dijkstra | Its nonnegative-weight assumption fails. |

For the *largest-observations stream*, each of `n` arrivals costs at most O(log(k+1)); retained state is O(k), and presenting a descending snapshot costs O(k log(k+1)). Counting `n` samples and retaining the k most frequent of `u` distinct values is a different task with a bound such as `O(n + u log(k+1))`. Keep frequency and magnitude problems separate. For Dijkstra, `V` is vertices and `E` edges; a heap may contain stale tentative routes, so storage can reach O(V+E), and heap operations cost up to O(log(E+1)).

**Pass before moving on:** Explain what the root guarantees and why FIFO BFS cannot replace Dijkstra for weighted edges.

**Changed requirement:** Your K is almost the number of observations retained for a finite batch. Compare sorting with a heap, including the cost of returning a sorted snapshot.

<details>
<summary>After attempting: reference and explanation</summary>

Compare the [largest-observations implementation](../problems/26-top-k-stream/solution.py) with `shortest_paths` in [algorithms.py](../algorithms.py). `top_k_frequent` solves a different ranking question. Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>
