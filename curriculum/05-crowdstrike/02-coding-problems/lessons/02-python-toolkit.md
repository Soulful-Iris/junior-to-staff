# Python toolkit for these rounds

[Curriculum](../../../README.md) · [Coding problems](../README.md)

> "You chose Python. Which standard-library calls should be reflex by the time the interviewer says 'now make it a stream'?"

| Need | Call | Used in |
|---|---|---|
| Counting | `collections.Counter`, `defaultdict(int)` | [44](../problems/44-busiest-host/README.md), [50](../problems/50-log-parser/README.md) |
| Top-k | `heapq.nlargest(k, items, key=...)`; a fixed-size min-heap | [44](../problems/44-busiest-host/README.md) |
| Merge sorted iterables | `heapq.merge(*streams, key=...)` | [51](../problems/51-merge-k-streams/README.md) |
| Binary search | `bisect.bisect_right(keys, t)` | [46](../problems/46-time-based-kv/README.md) |
| Ordered eviction | `collections.OrderedDict` with `move_to_end` and `popitem(last=False)` | [47](../problems/47-lru-cache-ttl/README.md) |
| Queues | `collections.deque` (O(1) both ends); `queue.Queue(maxsize=n)` for threads; `asyncio.Queue` for coroutines | [56](../problems/56-worker-pool/README.md) |
| Threads | `threading.Thread`, `Lock`, `Event`, `Semaphore`; `concurrent.futures.ThreadPoolExecutor` | [56](../problems/56-worker-pool/README.md) |
| Streams | generators: `for line in f`, `yield`; `itertools.islice`, `groupby`, `chain` | [44](../problems/44-busiest-host/README.md), [50](../problems/50-log-parser/README.md) |
| Hashing | `hashlib.sha256()` fed in chunks with `.update()` | T3 |
| Memoization | `functools.lru_cache` | recursion problems |
| Graphs | `collections.deque` for BFS; explicit stack for DFS on big grids; `heapq` for Dijkstra | [48](../problems/48-number-of-islands/README.md), [54](../problems/54-network-delay/README.md) |
| Time | `time.monotonic()` for limiters, never wall-clock | [49](../problems/49-token-bucket/README.md) |
| Typing and structure | `dataclasses.dataclass`, `typing.Optional`, `Iterable` | everywhere |

## Say the complexity as you go

| Structure | Insert | Lookup | Remove | Order |
|---|---|---|---|---|
| dict / set | O(1) avg | O(1) avg | O(1) avg | none |
| OrderedDict | O(1) | O(1) | O(1) | insertion; movable |
| heapq | O(log n) | O(1) min | O(log n) | partial |
| sorted list + bisect | O(n) | O(log n) | O(n) | full |
| deque | O(1) ends | O(n) middle | O(1) ends | insertion |

## Three habits that read as senior

1. Name the memory bound the moment the input becomes a stream.
2. Write the baseline that passes the six scenarios before optimizing; the reported time-out failure was a candidate optimizing a solution that did not yet work.
3. Put the invariant in one sentence above the loop: "the heap holds the k largest seen so far," "the window holds only events within the last 600 seconds."

Back to the [chapter](../README.md).
