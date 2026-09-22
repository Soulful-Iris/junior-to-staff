# 10 · Stateful coding: design an LRU cache

> “Capacity is two entries: put a, put b, get a, then put c. Which key must disappear, and what must remain constant-time?”

Evict b. Lookup and eviction order are different responsibilities; derive the map and pointer invariants before writing get or put.

This is a short prerequisite lesson. Attempt the complete [manual lru cache problem](../problems/28-manual-lru-cache/README.md), then [expiring key value store](../problems/29-expiring-key-value-store/README.md), with their contracts, tests and changed requirements.

**Build:** Implement get and put for a cache with capacity measured in entries.

![Stateful coding: design an LRU cache](../../../../assets/learning/lru-order.svg)

[Static diagram](../../../../assets/learning/lru-order-still.svg)

**The idea:** The map finds an entry. Recency order chooses eviction. A get moves the existing node to the most-recent end.

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

Compare `LRU` in [algorithms.py](../algorithms.py). Use [pattern notes](../pattern-notes.md) for the invariant and [contracts](../reference.md) for complexity edge cases. Reimplement tomorrow without copying.

</details>

[Previous](09-search.md) · [Next: TypeScript practical round](../practical.md)
