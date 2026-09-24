# Review observed PostgreSQL schedules and transaction reasoning

Use this key after the [two-session PostgreSQL exercise](README.md). Compare the actual reservation, on-call and retry outcomes with the table below. Ask the learner to explain the statement order that produced each result before naming an isolation level.

The candidate should operate two independent sessions and narrate observed state,
not merely recite isolation names. The [runner](run_schedules.py) automates the
same schedules; its result is reference evidence, not the candidate's attempt.

| Boundary | Expected evidence | Reasoning that is insufficient |
|---|---|---|
| Lost update | Two reservations in baseline; one after conditional decrement | “Stock is nonnegative, therefore no oversell” |
| Write skew | Repeatable-read count 0; serializable 40001; whole retry count 1 | “BEGIN” or a row lock on only the doctor's own row |
| Deadlock | 40P01 victim rollback; survivor count 1; full retry counts 2 | Retrying only the blocked statement in an aborted transaction |
| Retry budget | Three total attempts; 40001/40P01 only; no external effect in callback | Retrying every integrity error or claiming every timeout is safe to repeat |
| Plans | Actual/estimated rows, buffers, ordering and limit explained | Index must always win; elapsed time alone proves heap layout |
| Physical model | Separate heap and B-tree; conditional HOT eligibility | Ordered primary key automatically clusters heap |

Score each 0 absent, 1 explained, 2 independently reproduced and defended. Senior
practice should show all boundaries without the answer file. For an unseen
follow-up, add a third doctor and a concurrent shift transfer, or make the owner
predicate broad but keep `LIMIT 20`; ask the candidate to adjust the invariant
or predicted plan before running it. Lead scope adds lock/retry budgets across
teams and a compatible old-writer rollout. Do not convert scores into a pass
probability. No PostgreSQL execution in the author's environment is claimed.
