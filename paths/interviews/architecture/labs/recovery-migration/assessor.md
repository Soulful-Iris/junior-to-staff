# Assessor: recovery is part of the design

Give the brief first and hold these constructed follow-ups back. Score each
dimension 0 absent, 1 explained, 2 independently demonstrated by an injected
failure and preserved invariant. Tests establish reference behavior, not hiring
readiness.

| Dimension | Passing observable evidence | Unfamiliar changed assumption |
|---|---|---|
| Fencing | A epoch 1 cannot overwrite B epoch 2; enforcement lives at destination | Lock and destination are separate stores: how is authority synchronized? |
| External effect | Lost response stays uncertain; same provider key yields one effect | Provider key expires before DLQ replay; do not blindly retry |
| Atomic intent | Crash rolls back both business row and outbox | Publish succeeds, marking sent fails; consumer deduplicates |
| Migration | v2 beats old snapshot v1; delete tombstone survives; repair checks values | Transform is lossy: identify rollback point of no return |
| Recovery | Expired log checkpoint blocks resume; fresh snapshot plus position closes gap | Snapshot lasts longer than log retention; extend retention or throttle/reset |
| Rebalance | Reject stale route after fenced authority switch | Registry unavailable: state read/write availability policy |
| Region loss | Name acknowledged v9 missing from v8 survivor; choose RPO/availability | Old primary returns with divergent writes; reconcile before serving |

For the three-team memo, score 0–2 each for compatibility/authority, sequencing
and named owners, quantified capacity/budget, cutover/rollback gates, and
partial-versus-retirement benefits. Require a revision when the mobile deadline
moves another quarter. A lead-quality answer may narrow scope or pause; finishing
at any cost is not the criterion. This exercise is evidence of reasoning in a
simulation, not a claim of demonstrated multi-team delivery history.
