# Drive conflicting transactions in two PostgreSQL sessions

[Curriculum](../../../../README.md) · [Model data and enforce transactional rules](../../README.md)

## Application and assignment

This worksheet makes concurrency visible one statement at a time. Session A represents one buyer or doctor, and session B represents another. Keeping a transaction open lets you choose exactly when the other session reads or tries to write.

Follow the numbered columns in order, record returned rows and waits, and reset the stated fixture between scenarios. The starting schema and complete lab setup are linked below. Running both columns in one connection would remove the conflict you are trying to study.

## Contract and starting evidence

Read the [problem contract and diagrams](README.md) first. This is a worksheet
for that lab, not an additional problem. Open two terminals with
`psql "$LAB_PG_DSN" -X`, then in **each** execute:

```sql
SET search_path=interview_lab;
\set VERBOSITY verbose
```

Initialize once from another terminal with
`psql "$LAB_PG_DSN" -X -v ON_ERROR_STOP=1 -f curriculum/02-applications/02-databases/labs/postgresql/schema.sql`.
Keep the sessions independent; do not paste both columns into one connection.
Record output after each step and draw the conflict before consulting the key.

## Lost update: exact failing schedule

| Step | Session A | Session B |
|---|---|---|
| 1 | `BEGIN; SELECT available FROM stock WHERE id=1;` → 1 | |
| 2 | | `BEGIN; SELECT available FROM stock WHERE id=1;` → 1 |
| 3 | `UPDATE stock SET available=0 WHERE id=1; INSERT INTO reservations VALUES ('a',1); COMMIT;` | |
| 4 | | `UPDATE stock SET available=0 WHERE id=1; INSERT INTO reservations VALUES ('b',1); COMMIT;` |
| 5 | `SELECT count(*) FROM reservations;` → 2 | |

Reset: `TRUNCATE reservations; UPDATE stock SET available=1;` outside a transaction.
Repair with this statement in both transactions:

```sql
UPDATE stock SET available=available-1
WHERE id=1 AND available>0 RETURNING id;
```

A executes first but holds its transaction open. B executes and waits. In A,
insert reservation `a` and commit. B resumes and returns zero rows: insert no
reservation and commit. Why does rechecking the predicate matter? Verify both
stock and reservation count; a nonnegative stock value alone was already green
in the failing schedule.

## Write skew: exact failing schedule

| Step | Session A | Session B |
|---|---|---|
| 1 | `BEGIN ISOLATION LEVEL REPEATABLE READ; SELECT count(*) FROM doctors WHERE on_call;` → 2 | |
| 2 | | Same begin/count → 2 |
| 3 | `UPDATE doctors SET on_call=false WHERE id=1;` | |
| 4 | | `UPDATE doctors SET on_call=false WHERE id=2;` |
| 5 | `COMMIT;` | `COMMIT;` after A |
| 6 | `SELECT count(*) FROM doctors WHERE on_call;` → 0 | |

Reset `UPDATE doctors SET on_call=true;`. Repeat with `SERIALIZABLE` instead of
`REPEATABLE READ`. One commit must abort with `40001`. Roll back that session,
start a new serializable transaction, reread the count, and update only if count
is greater than one. A retry now observes one and stays on call. Merely rerunning
the old `UPDATE` is the wrong retry unit.

## Deadlock: exact failing schedule

| Step | Session A | Session B |
|---|---|---|
| 1 | `BEGIN; UPDATE counters SET hits=hits+1 WHERE id=1;` | |
| 2 | | `BEGIN; UPDATE counters SET hits=hits+1 WHERE id=2;` |
| 3 | `UPDATE counters SET hits=hits+1 WHERE id=2;` → waits | |
| 4 | | `UPDATE counters SET hits=hits+1 WHERE id=1;` → cycle |
| 5 | One session reports `40P01`; `ROLLBACK;` there | Other statement resumes; `COMMIT;` there |

Which transaction loses is not contractual. Verify both counters equal 1.
Retry the aborted **whole** operation with `SELECT id FROM counters ORDER BY id
FOR UPDATE;` before the increment. Both counters must become 2. Then reset and
run two operations using the same sorted lock order; both finish without this
cycle. A bounded retry still handles other serializable/deadlock interactions.

Save the observed SQLSTATEs, queries, and invariant values with your attempt.
Use [the assessor guide](assessor.md) only after explaining your own fix.
