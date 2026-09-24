# Trace LRU eviction before implementing its linked order

[Curriculum](../../README.md) · [Data systems at scale](README.md)

## What the cache remembers

A preview service keeps a few decoded objects so repeated reads can reuse them. Capacity counts entries in this exercise. When a new entry would exceed the limit, the service removes the entry whose most recent successful use is oldest. Reading a present entry changes that order even though its value stays the same.

Your task is to trace the sequence below, then implement the complete linked-list problem. No AWS cache is required. The shared `LRU` helper linked at the end uses an ordered-map library, while the standalone problem deliberately asks you to implement recency pointers yourself.

> “Capacity is two entries: put a, put b, get a, then put c. Which key must disappear, and what must remain constant-time?”

Evict b. Lookup and eviction order are different responsibilities; derive the map and pointer invariants before writing get or put.

This is a short prerequisite lesson. Attempt the complete [manual lru cache problem](problems/28-manual-lru-cache/README.md), then [expiring key value store](problems/29-expiring-key-value-store/README.md), with their contracts, tests and changed requirements.

**Build:** Implement get and put for a cache with capacity measured in entries.

![Stateful coding: design an LRU cache](../../../assets/learning/lru-order.svg)

[Static diagram](../../../assets/learning/lru-order-still.svg)

**The idea:** The map finds an entry. Recency order chooses eviction. A get moves the existing node to the most-recent end.

| Operation | Least recent → most recent | Outcome |
|---|---|---|
| Put a | a | One entry |
| Put b | a, b | Capacity reached |
| Get a | b, a | Reading a refreshes its position |
| Put c | a, c | Evict b, which was used least recently |


## Your 45-minute session

1. **5 min:** draw one example and a simple solution.
2. **25 min:** implement `LRU` without the reference.
3. **10 min:** test Capacity zero; overwrite; miss; get refreshes recency; put A, put B, get A, put C evicts B.
4. **5 min:** explain the cost and answer the changed requirement.

**Cost:** Scanning recency: O(capacity). Map plus linked order: expected O(1) get/put, O(capacity) space.

**Pass before moving on:** Show how one node is detached and reattached. Do not explain only OrderedDict syntax.

**Changed requirement:** Capacity is now bytes, with TTL. Can one insertion still guarantee O(1) work?

<details>
<summary>After attempting: reference and explanation</summary>

Compare `LRU` in [algorithms.py](../../01-code/02-data-structures-algorithms/algorithms.py). Use [pattern notes](../../01-code/02-data-structures-algorithms/pattern-notes.md) for the invariant and [contracts](../../01-code/02-data-structures-algorithms/reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>

[Previous](../../01-code/02-data-structures-algorithms/lessons/09-search.md) · [Next: TypeScript practical round](../../../indexes/practical-exercises.md)
