# Importer assessor key · open after the independent attempt

Use the [candidate brief](../../../../../practice/candidate/practical-debug.md). Record
what the candidate ran, what they predicted and which hypothesis a test disproved.
Timeboxes are training choices. Do not reveal every failure at minute zero.

| Stage / expected repair | Regression and exact observation | Why another explanation loses |
|---|---|---|
| 0: restore `store.advance` declaration colon | `PACKAGE=starter python -m unittest test_importer` first fails with `SyntaxError: expected ':'` | No HTTP or SQLite request has executed yet; retry tuning cannot fix an import failure |
| 1: integer money | `test_integer_money_dedup_and_completion`: `0.29 → 29`, `-1.10 → -110`, `0.00 → 0` | `int(float('0.29')*100)` truncates binary representation; changing sort order does not repair value loss |
| 2: persist then checkpoint; completed flag | `test_restart_after_persist_before_checkpoint` reopens SQLite, initially `(None,0)`, finally 3 rows | Server delivery was successful; progress ahead of durable effects is an integration failure, not eventual consistency |
| 3: reject seen cursors | `test_cycle_and_page_budget`: p2 points at itself, exactly 2 requests before failure; held-back pack adds longer cycle | A larger page budget postpones termination and can conceal the bad provider contract |
| 4: respect numeric retry timing | `test_retry_timing`: second request begins at 0.75; total-deadline case rejects 0.8 delay after 0.3 elapsed | Sleeping a fixed second ignores service advice; retries are not an unlimited separate budget |
| 5: retain validation and transactional conflict check | malformed page leaves only a/b; conflicting page's new ID is rolled back | `INSERT OR IGNORE` alone hides equal-ID/different-money corruption |
| 6: preserve attempts and finite budgets | 503 makes exactly 3 calls; 10-second transport request times out against 1 second | Catch-all retry turns permanent malformed/domain failures into load amplification |

The starter contains four deliberate repair areas after the syntax issue: amount
conversion, early checkpointing, cycle checks and ignored Retry-After. Validation,
transactional conflict checks and timeout mechanisms are existing code to understand
and preserve, not gratuitously rewrite. Each expected repair has a named regression.

Reference: [coordinator](reference/importer.py), [transport and fake clock](reference/transport.py),
[domain model](reference/model.py), [SQLite store](reference/store.py). Test injection
points are intentional seams. `after_persist` models process failure at the durable
boundary, while `FakeServer.elapsed` models time spent inside the transport. Fake
timeouts are a contract test; they do not establish a real HTTP library cancels sockets.

Withhold [additional fixtures](../../../../../practice/assessor/heldback_importer.py) until
the candidate has a baseline. Run them against the candidate's selected package.
Grade using [observable anchors](../../../../../practice/assessor/practical-debug.md).
Debrief through the [method](README.md#start-with-the-smallest-useful-trace), then
change currency representation or checkpoint schema on a later session.
