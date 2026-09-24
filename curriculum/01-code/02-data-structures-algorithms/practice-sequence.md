# Choose a coding problem and work through its contract

[Curriculum](../../README.md) · [Choose data structures and reason about algorithms](README.md)

## Your first complete attempt

Begin with [Two sum](problems/01-two-sum/README.md). A reconciliation tool receives amounts such as `[3,3]` and asks for two distinct positions totaling 6. Write `(0,1)` before choosing the implementation, then explain why a single `[3]` cannot reuse its own position.

Repeat that method through the progression below: concrete result first, state and invariant next, then code and a changed requirement. This page is a route through exercises, not another algorithm you need to implement.

> “I will give you a concrete input and a required output. Explain the contract,
> show a simple correct approach, then improve it and respond when a constraint
> changes.” That is the skill this route practices.

Start with one individual problem. Write the expected answer for its small
example before opening the solution. Python is used for algorithms; TypeScript
is used where browser state and asynchronous APIs are the problem.

## 42 individual problems

- [Foundations: maps, windows, ordered data, pointers, and trees](problems/foundations-index.md).
- [Advanced structures and reasoning: graphs, caches, parsing, DP, streams, and synchronization](problems/advanced-index.md).

Each page supplies its contract, worked reasoning, visual traces and changed
requirements, reference implementation, and meaningful tests. Build your own
solution first; passing the reference tests alone does not assess you. The short
concept lessons below are prerequisite refreshers, not the full question bank.


Follow the stages in order until you can explain and implement the prerequisite.
Later stages broaden the bank; they are not a claim that every role asks every topic.

| Stage | Problems | What the next stage relies on |
|---|---|---|
| 1. Scan and remember | 01–08: maps, windows, prefixes, arrays | State an invariant; separate input size from retained state |
| 2. Order and boundaries | 09–13: intervals, binary and answer search | Choose closed/half-open semantics and prove each boundary update |
| 3. Identity and recursion | 14–20: lists and trees | Preserve links; distinguish a returned value from accumulated results |
| 4. Graphs and retained state | 21–30: scheduling, paths, heaps, caches, trie | Discovery/finality rules; bounded state; operation sequences |
| 5. Search and recurrence | 31–36: backtracking and four DP exercises | Define a subproblem, dependencies, base cases and proof |
| 6. Advanced follow-ups | 37–42: monotonic structures, parser, event time, median, queue | Derive changed invariants; choose by role and interview format |

After stages 1–3, add the [importer debugging lab](../../02-applications/04-testing/labs/importer/README.md).
After stage 4, add [TypeScript fan-out](../../02-applications/01-backend/labs/fan-out/README.md) and the
[runnable full-stack editor](../../02-applications/03-frontend/labs/bookmark-editor/README.md).
Infrastructure candidates should also implement the [bounded executor](../../02-applications/01-backend/labs/bounded-executor/README.md).
Alternate familiar practice with [unfamiliar assessed sessions](../../../practice/README.md).

To verify all supplied Python references without cross-importing their identically
named modules, run `python scripts/check_curriculum.py --coding-only` from the
repository root. Run `python scripts/check_curriculum.py` to include the local labs.
These checks verify reference code; record your own independent attempts separately.

## Concept refreshers

| Step | Learn → implement | You can move on when… |
|---|---|---|
| 1 | [Maps → Two Sum](lessons/01-maps.md) | You explain lookup-before-insert |
| 2 | [Windows → longest unique substring](lessons/02-windows.md) | You trace `abba` correctly |
| 3 | [Prefix sums → subarray sum K](lessons/03-prefix.md) | Zeros and negative values work |
| 4 | [Sorted data → binary search, intervals](lessons/04-order.md) | You defend both boundary updates |
| 5 | [Graphs → islands, prerequisite order](lessons/05-graphs.md) | You handle duplicate discovery and cycles |
| 6 | [Heaps → top K, Dijkstra](lessons/06-heaps.md) | You skip stale candidates and explain ordering |
| 7 | [Stack → next warmer day](lessons/07-stack.md) | You prove the nested loop is O(n) |
| 8 | [DP → minimum coins](lessons/08-dp.md) | You derive the recurrence before coding |
| 9 | [Search → word search, trie](lessons/09-search.md) | You undo state and mark complete words |
| 10 | [State → LRU cache](../../04-scale-and-evolution/01-data-at-scale/cache-order.md) | Reads, overwrites, and eviction preserve recency |
| 11 | [TypeScript → concurrency and stale responses](../../../indexes/practical-exercises.md) | You test rejected work and out-of-order completion |
| 12 | [Timed mock → feedback and repeat](../../../practice/coding-mock.md) | You solve, test, explain, and adapt without hints |

## Start today

Open [Two sum](problems/01-two-sum/README.md). Clarify → trace → code → test → explain. Reattempt a missed problem the next day before adding another topic.

**Junior:** correctness, tests, complexity. **Senior:** add changed constraints and practical integration. **Staff:** keep the same coding fluency; add API ownership, failure boundaries, and migration tradeoffs. These are practice targets, not company-wide leveling rules.

[Contracts and solutions](reference.md) · [Explain algorithm invariants and the changes that invalidate them](pattern-notes.md) · [Current interview evidence](../../../docs/research/interview-evidence.md) · [Interview home](../../../practice/interview-guide.md)
