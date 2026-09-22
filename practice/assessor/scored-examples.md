# Fully scored calibration examples

These are **fictional constructed performances** for assessor calibration, not actual
candidate records or employer thresholds. Scores use all eight dimensions of the
[rubric](../README.md). Totals are deliberately omitted: an invariant failure cannot
be averaged away. Actual learners must collect their own independent evidence on more
than one occasion; these examples cannot fill their attempt records.

## Senior example · practical repair plus design defense

On hypothetical occasion A, Mina receives the unfamiliar importer starter. At minute 3
she identifies the syntax failure before blaming HTTP. At minute 12 she reproduces
`0.29 → 28`, repairs exact money and adds a long fractional-cent regression. At minute
24 she traces progress written before rows. Her crash/reopen test fails before the
repair and passes afterward. She completes held-back cycle/deadline tests without a
hint, explains a failed alternative, and marks real HTTP cancellation untested. In a
short export-design follow-up she draws durable acceptance and an ownership predicate.

On hypothetical occasion B a week later, another assessor gives an unseen inventory
consumer with conflict/atomic-batch requirements. Mina initially mutates a valid event
before a later conflict; her own late-conflict test catches it. She stages the batch,
runs the tests and explains O(n) retained identity state. No solution code is supplied.

| Dimension | A | B | Observable justification |
|---|---:|---:|---|
| Clarification | 2 | 2 | States identity, units, atomicity and excluded multi-process scope before implementing |
| Correctness | 3 | 2 | A derives long-precision and crash counterexamples; B repairs her own atomicity defect and passes stated/held-back cases |
| Architecture | 2 | 2 | Maps transport/domain/progress authority; B separates batch staging from committed state |
| Implementation | 3 | 2 | A safely adapts the supplied package; B delivers runnable independent code with relevant tests |
| Tradeoffs | 2 | 2 | Compares atomic checkpoint transaction versus idempotent replay; accounts for retained IDs |
| Operations/security | 2 | 2 | Bounds retries and names unverified real-client cancellation; validates records without retrying permanent errors |
| Communication | 3 | 2 | A predicts each trace before execution and rules out competing causes; B explains her correction clearly |
| Ownership/influence | 2 | 2 | Identifies her changes, asks finance to own conflicting-payload policy, and gives concrete remaining work |

**Assessment:** the illustrative senior curriculum floor is met on both occasions;
the candidate corrected a discovered defect independently. This does not establish a
hiring probability or leadership history. Next practice: cross-process checkpoint
compatibility and tenant fairness. A candidate who leaves B's partial mutation
unrepaired gets correctness 0–1 and does not meet the gate regardless of other scores.

## Lead example · export rollout plus executable infra mechanism

On hypothetical occasion A, Jules receives the export design and staffing constraint:
two teams, two engineers each, four weeks. He derives the 200-build steady-state
arithmetic, then budgets only the dependency-supported active concurrency and a bounded
waiting queue. He rejects exactly-once physical work, traces stale token 7 versus 8,
and writes/runs a conditional-completion test. API team owns old/new polling fields;
worker team owns claim tokens and orphan cleanup; he names a rollout stop condition
(any acknowledged job missing from status) and a retirement condition (no old-client
traffic for the agreed observation window plus owner sign-off). He cuts offline
exports and global active-active rather than assigning impossible scope.

On hypothetical occasion B, an independent assessor provides the byte-weighted
executor variant. Jules implements admission under a condition loop, tests a blocked
producer during shutdown and reproduces nested wait deadlock with barriers. He rejects
same-pool nested submission explicitly and explains why 20 replicas × 4 workers would
exceed a 40-operation dependency budget. He proposes tenant quotas and names the
remaining fairness test rather than claiming it is already solved.

| Dimension | A | B | Observable justification |
|---|---:|---:|---|
| Clarification | 3 | 2 | A resolves product revocation versus cached download constraints; B establishes task/byte budget and cancellation meaning |
| Correctness | 3 | 3 | A proves stale-owner rejection without claiming zero duplicate work; B preserves admission/terminal accounting through failures |
| Architecture | 3 | 3 | A connects durable acceptance/status/artifacts/recovery; B shows local limits composing across replicas |
| Implementation | 2 | 3 | A runs the critical conditional-completion mechanism; B delivers working independently tested executor under changed capacity units |
| Tradeoffs | 3 | 3 | Chooses constrained delivery scope and measurable capacity; compares fairness policies and reports unresolved evidence |
| Operations/security | 3 | 2 | A tests ownership/revocation boundaries and rollback; B accounts for still-running resources after timeout |
| Communication | 2 | 3 | A gives coherent decisions and ownership; B uses a short counterexample to reject “increase queue size” |
| Ownership/influence | 3 | 3 | A assigns contracts, sequence, stop/retirement owners; B assigns fleet budget coordination and explicit follow-up work |

**Assessment:** the illustrative lead curriculum floor is met with independent
technical implementation on both occasions, plus cross-team planning evidence. The
exercise assesses a plan and mechanisms; it cannot prove Jules has successfully led
real multi-team work. A real lead evaluation also needs truthful project-history
evidence, with “I” and “we” distinguished. Debrief through
[design recovery](design.md), [infra](infra.md) and [the attempt record](../attempt-record.md).
