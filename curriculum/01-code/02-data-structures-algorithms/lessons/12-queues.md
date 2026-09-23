# Queues and deques: control who goes next

A **queue** serves the oldest waiting item first (FIFO). A **stack** serves the newest first (LIFO). A **deque** supports efficient operations at both ends, so it can implement either policy. The order determines whether a traversal explores nearby states or follows one branch deeply.

![Queue removes oldest work while a stack removes newest work](../../../../assets/foundations/queues.svg)

```python
from collections import deque

ready = deque(["A", "B"])
ready.append("C")
print(ready.popleft())  # A
print(list(ready))      # ['B', 'C']
```

Appending and removing at either deque end are O(1). Removing `list[0]` with `pop(0)` shifts the remaining entries, making it a poor queue for large traversals. A deque is not intended for fast arbitrary middle indexing.

## Use the order as part of the proof

In BFS, newly discovered neighbors join the back while the oldest discovered node leaves the front. Every distance-d node is processed before distance d+1, which gives shortest paths when every edge has equal cost. Mark a node visited when enqueueing it so two parents cannot schedule it twice.

For a tree level, capture the initial queue length, then remove exactly that many nodes; appended children belong to the next level. In a dependency scheduler, the queue holds only work whose prerequisites are complete.

## A queue is not a complete work system

An in-memory deque alone does not define capacity, waiting, cancellation, persistence, or concurrent ownership. Those contracts appear later in the bounded queue and durable-job exercises. Here, predict the state after append-left, append-right, pop-left, and pop-right before adding those concerns.

Source: [Python queue operations](https://docs.python.org/3/tutorial/datastructures.html#using-lists-as-queues)
