# Why the patterns work

Use these notes after attempting the [problem set](README.md). The complete implementations are in [algorithms.py](algorithms.py); compare your invariant with the code before comparing line by line.

## Complement map

For two-sum, each index asks whether an earlier element completes its target. Look up the complement before inserting the current index, so a single value is not reused twice. The map remembers earlier work. With `[3,3]`, the second 3 finds the first. If you need every valid pair, one stored index per value is no longer enough; change the output contract before changing the implementation.

## Binary search

Keep a half-open interval `[lo, hi)` containing the possible insertion point. If `nums[mid] < target`, every index through mid is too small, so `lo=mid+1`. Otherwise the first qualifying value can still be mid, so `hi=mid`. Each iteration shrinks the interval; termination at `lo==hi` yields the first index whose value is at least target, or n if none. Sorting an unsorted input first adds O(n log n) work and may lose original positions.

## Interval merging

Sort by start. The only output interval the next interval can overlap is the last one: earlier outputs end before that last interval starts. If the next start is within the last closed interval, extend its end to the maximum. Otherwise append a new interval. For half-open intervals `[start,end)`, a meeting ending at 10 does not conflict with one starting at 10; choose `<` rather than `<=` when that is the desired contract.

## Top K with a heap

Count values, then maintain the K strongest candidates. The smallest retained candidate is the one to replace when a better item appears. This spends O(log K) per considered distinct value instead of sorting all u values. If K is almost u, sorting is simpler and can be competitive. Deterministic ties matter for reproducible tests. A heap is not a sorted list: only its root has the guaranteed extremal position.

## BFS and Dijkstra

BFS uses a FIFO queue because all edges cost one step: discovering a node from the current distance layer gives its shortest unweighted distance. Mark nodes when enqueued, otherwise several parents can enqueue the same node. A grid is just a graph with implicit neighbor edges.

Dijkstra's smallest tentative distance becomes final under nonnegative edge weights. A later shorter route pushes a new heap entry; the old entry remains but is skipped when popped. Negative edges violate the reasoning. For non-unit positive weights, FIFO BFS does not generally yield minimum cost.

## Dependency order

Indegree counts unfinished prerequisites. Only zero-indegree tasks can enter the ready queue. Completing a task decrements each outgoing dependent once. Deduplicate repeated prerequisite pairs, or counts and decrements can disagree. If fewer than V tasks finish, a cycle prevents completion. This answers “find an order,” not every scheduling optimization involving durations, priorities, or limited parallelism.

## Dynamic programming

For coin change, define `dp[x]` as the minimum number of coins that sum to x. `dp[0]=0` is the base case. Every nonempty solution ends with some coin c, leaving a smaller subproblem x-c. Therefore consider `1+dp[x-c]` for each usable coin. Increasing x ensures dependencies are already computed. An unreachable sentinel must exceed any possible valid answer. Greedy largest-first fails for `[1,3,4]` and amount 6 because 4+1+1 is worse than 3+3.

Memory optimization must respect dependencies. Reducing an O(A) table without proving which older states are needed can silently change the algorithm. O(A×m) is pseudo-polynomial in the numeric amount, not polynomial in the number of bits used to encode A.

## Monotonic stack

For daily temperatures, keep unresolved indices whose temperatures are non-increasing from bottom to top. A warmer value resolves every colder index at the top. Each index is pushed once and popped at most once, so the nested loop is O(n) amortized. Equal temperatures do not resolve one another because the question says *strictly* warmer. Store indices rather than only temperatures so you can compute the waiting distance.

## Backtracking

Word search explores a choice, marks the cell used, recurses, then undoes the mark. The used set belongs to the current path, not all explored paths. A cell rejected in one attempted path may be valid in another. Check the final character before exploring beyond it. The number of paths can grow exponentially; pruning helps typical cases but does not turn the worst case into linear time. Test that no successful or failed search mutates the caller's board.

## Trie

A trie stores shared prefixes as paths. Inserting `app` does not automatically insert `ap`; a terminal marker distinguishes a complete word from a prefix. Exact lookup walks one edge per character. Memory depends on stored prefixes and child representation. For autocomplete you also need ranking and a bound on returned candidates; a trie alone does not decide what suggestions are best.

## LRU

Lookup and recency are different jobs. The dictionary points to an entry; a doubly linked list moves that entry without a scan. OrderedDict exposes the combination in Python. Every successful get and every put refreshes recency; overwrite must not increase size. Capacity zero is a legitimate boundary. TTL, byte limits, and multi-threaded access require additional policies and synchronization.

## Choose the language intentionally

Python: know dictionary/set operations, `deque.popleft`, `heapq`, tuple ordering, and recursion limits. Repeated slicing copies data; a recursive function that looks logarithmic can allocate more than expected. Python strings iterate code points, which are not always displayed characters.

TypeScript: know Map/Set, explicit numeric comparators for sorting, Promise scheduling, AbortSignal, and runtime validation. `Array.shift()` can incur linear work; an index-based queue avoids repeated moves. Type stripping runs code but is not type checking. Static typing cannot validate network JSON or stop a logical race.

## Retrieval test

For each pattern, write its invariant, a minimal counterexample to the naive approach, and a changed requirement that breaks your current solution. If you can only reproduce the reference code, repeat this exercise before adding another problem.

[Problem set](README.md) · [Practical coding](practical.md)
