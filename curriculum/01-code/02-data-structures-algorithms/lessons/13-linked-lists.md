# Linked lists: preserve the reachable chain

You are reversing a chain of records without allocating replacement nodes. Changing the first link can make the rest of the records unreachable if you have not saved another reference to them. Follow the two-node example below and name which variable still reaches each node after every assignment.

A linked-list node stores a value and a reference to another node. An array index locates a slot; a link points to an object. To reach the third node from the head, follow two links. The useful skill is changing connections without losing the remaining chain.

![A linked chain with head, current node, and saved next reference](../../../../assets/foundations/links.svg)

```python
from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: int
    next: "Node | None" = None

head = Node(4, Node(9))
print(head.next.value)  # 9
```

`eq=False` keeps node identity meaningful: two separate nodes containing 4 are not the same node. The end is `None`. An empty list has `head = None`.

## Change one link safely

To reverse a chain, save the unreversed suffix before replacing a link:

```python
previous = None
current = head
while current is not None:
    following = current.next
    current.next = previous
    previous = current
    current = following
head = previous
```

After each iteration, `previous` owns the reversed prefix and `current` owns the remaining suffix. Reversing `4 → 9 → None` yields `9 → 4 → None`; forgetting `following` can disconnect the 9.

## Cost depends on the handle you have

Finding an arbitrary value is O(n). Inserting after an already-known node is O(1). In a singly linked list, deleting a known node may still require its predecessor. A doubly linked list stores both `previous` and `next`, enabling O(1) removal with a node handle at the cost of more links to maintain.

This is why an LRU cache combines a dictionary with a doubly linked list: the map finds the node, and the list moves it in recency order. State explicitly whether an operation reuses caller-owned nodes or returns a new chain.

**Check:** empty and one-node chains survive reversal; repeated values remain separate nodes; a cycle needs detection or a documented exclusion before a traversal can terminate.

## Trace the first reversal step

For the initial chain 4 then 9, all variables refer to nodes or `None`:

| Assignment | What remains reachable |
|---|---|
| `following = current.next` | `following` still reaches node 9 |
| `current.next = previous` | Node 4 now ends at `None` |
| `previous = current` | `previous` reaches the reversed prefix, node 4 |
| `current = following` | `current` reaches the unprocessed suffix, node 9 |

Without the first assignment, reading `current.next` after overwriting it would yield `None`. The value 9 still exists in memory only if another reference kept it alive, but this algorithm would have lost its route to it.
