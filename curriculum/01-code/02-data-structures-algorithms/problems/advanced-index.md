# Advanced coding progression

[Curriculum](../../../README.md) · [Data structures and algorithms](../README.md)

These are constructed practice questions, with candidate briefs before hidden
worked solutions. Attempt each independently and record your invariant, tests,
complexity, and response to a changed requirement before viewing the reference.
Passing reference tests is implementation evidence, not an assessment of you.

Start with the [foundations progression](foundations-index.md). These exercises
then combine graph state, explicit structures, search, and runtime contracts.

| Order | Problem | Property to explain independently |
|---:|---|---|
| 21 | [Dependency order](21-dependency-order/README.md) | Readiness counts and cycle detection |
| 22 | [Word ladder](22-word-ladder/README.md) | Implicit graph and shortest discovery |
| 23 | [Disjoint-set connectivity](23-disjoint-set-connectivity/README.md) | Partition preservation under union/compression |
| 24 | [Grid shortest path](24-grid-shortest-path/README.md) | Movement contract and path reconstruction |
| 25 | [Weighted shortest path](25-weighted-shortest-path/README.md) | Finality, relaxation, and stale heap entries |
| 26 | [Top k stream](26-top-k-stream/README.md) | Exact retained multiset and lost history |
| 27 | [Merge k streams](27-merge-k-streams/README.md) | One frontier per source and lazy failure |
| 28 | [Manual LRU cache](../../../04-scale-and-evolution/01-data-at-scale/problems/28-manual-lru-cache/README.md) | Map/list identity and pointer invariants |
| 29 | [Expiring key-value store](../../../04-scale-and-evolution/01-data-at-scale/problems/29-expiring-key-value-store/README.md) | Strict expiry boundary and cleanup authority |
| 30 | [Trie autocomplete](30-trie-autocomplete/README.md) | Terminal markers, traversal order, and output cost |
| 31 | [Combination search](31-combination-search/README.md) | Canonical choices, termination, and output-sensitive work |
| 32 | [Word search](32-word-search/README.md) | Path-local visited state and restoration |
| 33 | [Coin change](33-coin-change/README.md) | Optimal substructure, witness, and pseudopolynomial cost |
| 34 | [Longest increasing subsequence](34-longest-increasing-subsequence/README.md) | Dominating tails and historical predecessors |
| 35 | [Edit distance](35-edit-distance/README.md) | Prefix states, recurrence, and rolling-row limits |
| 36 | [Decode ways](36-decode-ways/README.md) | Disjoint counting cases and exact-integer growth |
| 37 | [Daily temperatures](37-daily-temperatures/README.md) | Unresolved candidates and amortized nearestness |
| 38 | [Largest histogram rectangle](38-largest-histogram-rectangle/README.md) | First smaller boundary and inherited start |
| 39 | [Policy expression evaluator](39-policy-expression-evaluator/README.md) | Lexer/parser separation, precedence, and missing fields |
| 40 | [Event-time windows](../../../04-scale-and-evolution/01-data-at-scale/problems/40-event-time-windows/README.md) | Watermark authority, lateness, and finality |
| 41 | [Streaming median](41-streaming-median/README.md) | Ordered halves, balancing, and exact arithmetic |
| 42 | [Bounded blocking queue](../../../02-applications/01-backend/problems/42-bounded-blocking-queue/README.md) | Predicate loops, admission, deadlines, and shutdown |

Run a single reference from the repository root, substituting the chosen directory:

```bash
python -m unittest discover -s curriculum/04-scale-and-evolution/01-data-at-scale/problems/28-manual-lru-cache -p 'test_*.py'
```

Every directory supplies `solution.py` and `test_solution.py`; tests require only
Python's standard library. Use separate processes for different directories because
each intentionally imports its local module as `solution`.

For backend or infrastructure practice, spend extra time on dependency readiness,
stream consumption, manual LRU, and expiration. For product/search practice,
emphasize grid/word graph modeling, autocomplete, and policy parsing. The bounded
queue is an explicit backend/infrastructure extension. For DP transfer, solve
33–36 together and explain why one minimizes, one uses dominance, one aligns
prefixes, and one counts disjoint cases. Senior practice still requires
defending the underlying invariants; lead extensions change ownership, resource
budgets, and evolving contracts rather than replacing the coding floor.
