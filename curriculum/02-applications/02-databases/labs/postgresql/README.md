# Prevent overselling and write skew with the right transaction boundary

[Curriculum](../../../../README.md) · [Model data and enforce transactional rules](../../README.md)

## Application and assignment

A store has one unit left. Ana and Ben both press Reserve. The application must create one reservation and leave stock at zero. Seeing `stock=0` afterward is not enough, because two reservations could have been accepted for that one unit.

Use two database sessions to make the conflicting operations happen in a known order. Begin with the stock row, then handle the on-call rule spanning two rows. The supplied SQL and runner use a real local PostgreSQL database. They are separate from the reading-list starter’s SQLite database.

## Contract and starting evidence

**Constructed candidate brief:** “Ana and Ben each reserve the last unit. Both
read `available=1` before either writes. Show the exact SQL and expected rows.
Then protect a rule spanning two doctors: at least one must remain on call.
Finally, explain a query plan for a tiny owner and a dominant owner.”

Prerequisites: [keys, constraints, and row ownership](../../data-models-and-queries.md),
basic `SELECT/UPDATE`, and two independent database sessions. Attempt the
[candidate schedules](schedules.md) first. [Assessor notes](assessor.md) and
[the executable reference](run_schedules.py) are separate from the brief.

| Input | Baseline failure | Required fixed value |
|---|---|---|
| Stock 1; two buyers read 1 then write literal 0 | 2 reservations, stock 0 | 1 reservation, stock 0 |
| Two on-call doctors; each reads 2 and turns itself off | 0 on call at repeatable read | At least 1 after every successful commit |
| A locks row 1 then 2; B locks 2 then 1 | Deadlock abort, SQLSTATE `40P01` | Whole transaction retried; each logical increment happens once |
| 200 then 100,000 bookmark rows | Same plan may not remain cheapest | Correct values and an explained measured plan, no mandated timing ratio |

All sizes are synthetic. This lab targets PostgreSQL 18 semantics, not SQLite
isolation. `BEGIN` gives atomicity; isolation and write predicates decide whether
racing transactions can preserve the business rule.

## Baseline: correctness lives in the application gap

```mermaid
flowchart TD
  A["Ana transaction: read 1"] --> DecideA["Compute new stock 0"]
  B["Ben transaction: read 1"] --> DecideB["Compute new stock 0"]
  DecideA -->|"write literal 0, reserve Ana"| DB["Stock row + reservations"]
  DecideB -->|"write literal 0, reserve Ben"| DB
```

Name the invariant before fixing the statement: `available + reservations = 1`
for this reset fixture. A nonnegative check alone misses the oversell because
both stale writes store zero.

## Move the decision to the protected boundary

1. State what one row asserts and encode row-local constraints and foreign keys.
2. Interleave two sessions deliberately; label the snapshot each read observes.
3. For stock, atomically decrement only if `available > 0`, inspect `RETURNING`,
   and insert the reservation in the same transaction only when a row returned.
4. For a rule across rows, a lock on only the changed row is insufficient. Lock a
   shared guard row in a defined order, or use serializable transactions with a
   bounded whole-transaction retry. The reference uses serializable isolation.
5. On `40001` or `40P01`, roll back and rerun the full read/decide/write sequence.
   Retrying the final statement repeats a decision made from an invalid snapshot.
   Keep external effects outside the retry callback, using committed outbox intent.

```mermaid
flowchart TD
  Buyers["Ana and Ben"] --> Update["UPDATE available = available - 1 WHERE available > 0"]
  Update -->|"row lock + predicate recheck"| Stock["Database: stock authority"]
  Stock -->|"one row returned"| Reserve["Insert reservation in same transaction"]
  Stock -->|"zero rows"| SoldOut["No reservation; sold out"]
  Reserve --> Commit["Commit stock + reservation"]
```

## Local setup and commands

No AWS deployment is required. You need a disposable PostgreSQL 18 database,
`psql`, Python 3.11+, and `psycopg` 3. These commands reset only the
`interview_lab` schema **inside the database named by `LAB_PG_DSN`**. Do not point
them at an existing application database. The optional Docker command starts a
local server; using your own local installation is equally valid.

```bash
docker run --name interview-pg --rm -e POSTGRES_PASSWORD=lab-only -e POSTGRES_DB=interview_lab -p 127.0.0.1:55432:5432 -d postgres:18
export LAB_PG_DSN='postgresql://postgres:lab-only@127.0.0.1:55432/interview_lab'
docker exec interview-pg pg_isready -U postgres -d interview_lab
python -m venv /tmp/interview-pg-venv
/tmp/interview-pg-venv/bin/pip install 'psycopg[binary]>=3,<4'
/tmp/interview-pg-venv/bin/python curriculum/02-applications/02-databases/labs/postgresql/run_schedules.py
psql "$LAB_PG_DSN" -X -v ON_ERROR_STOP=1 -f curriculum/02-applications/02-databases/labs/postgresql/plans.sql > /tmp/interview-pg-plans.txt
```

Wait for `pg_isready` to report accepting connections before the runner. The
server's deadlock detection interval must be shorter than the runner's six-second
lock timeout; the PostgreSQL default meets that assumption. A lock timeout
(`55P03`) is deliberately not silently relabeled a deadlock.

If you have no host `psql`, run the plan file through the container instead:

```bash
docker exec -i interview-pg psql -U postgres -d interview_lab -X -v ON_ERROR_STOP=1 < curriculum/02-applications/02-databases/labs/postgresql/plans.sql > /tmp/interview-pg-plans.txt
```

The runner prints three `FAILURE reproduced` and three `FIX passed` lines. A
failed assertion stops execution. PostgreSQL/Docker were unavailable in the
authoring environment: these database commands were **not runtime-verified
there**. The Python sources were syntax checked, and the standard-library retry
tests can run without PostgreSQL:

```bash
python -m unittest discover -s curriculum/02-applications/02-databases/labs/postgresql -p 'test_*.py' -v
```

## Follow-up: the rule spans rows

Predict whether repeatable read prevents two doctors from each observing two
on-call rows and updating different rows. Its stable snapshots do not themselves
prevent this write skew. Serializable mode may abort one transaction instead.

```mermaid
flowchart TD
  A["Doctor 1 reads count 2"] --> SA["Serializable transaction A"]
  B["Doctor 2 reads count 2"] --> SB["Serializable transaction B"]
  SA --> Check["Database detects nonserializable dependency"]
  SB --> Check
  Check --> Winner["One commit: count 1"]
  Check -->|"40001"| Retry["Rollback, reread count 1, stay on call"]
```

**Senior:** show the rejected SQLSTATE and a full retry that changes the decision.
**Lead:** choose a contention/retry budget, ownership of the cross-row invariant,
and a compatibility plan for old clients that do not follow the new rule.

## Follow-up: the index loses

An ordinary PostgreSQL B-tree stores ordered keys and row locations. Heap pages
hold MVCC row versions; primary-key ordering does not continuously cluster the
heap. Inserts maintain indexes; a HOT-eligible update can reuse ordinary index
entries when indexed values are unchanged and the old heap page has room.

```mermaid
flowchart TD
  Selective["Owner 2: 100 matching rows"] --> Index["B-tree: owner + time + ID"]
  Index -->|"row locations"| Heap["Heap pages: row versions"]
  Broad["Owner 1: 90,100 matching rows"] --> Scan["Sequential scan candidate"]
  Scan -->|"read heap pages in order"| Heap
  Heap --> Compare["Compare actual rows, buffers, sort and time"]
```

The plan script seeds 200 uniform rows, 100,000 uniform rows, then a skew where
owner 1 has 90,100 rows and owner 2 has 100. It compares the small query before
and after an index, a large query with and without it, selective and broad scans,
and an ordered `LIMIT 20`. On the broad query, a sequential scan can avoid many
scattered heap accesses. On the ordered limited query, the index can stop early.
Do not require a particular plan node across hardware, cache state, or planner
settings. Never use `enable_seqscan=off` as evidence that an index wins naturally.

For each plan record estimated/actual rows, returned rows, heap/index buffers,
sort method, execution time, and warm/cold-cache assumptions. Inspect stale
statistics, skew, correlations, and generic prepared plans when estimates differ.
An `EXPLAIN ANALYZE` executes the query; use care for modifying statements.
`CLUSTER` requires an exclusive lock and temporarily reorders the heap; it does
not maintain future writes in index order. This exercise observes HOT statistics
without asserting an exact count because page space and statistics timing vary.

**Senior acceptance:** reproduce all three failing schedules and fixed invariants;
explain measured small/large/skewed plans. **Lead:** budget index creation, locks,
vacuum/bloat, connection pressure, and migration compatibility. Supply the plan
output and server version as evidence; green Python-only retry tests cannot
substitute for database execution.

Cleanup the optional local container:

```bash
docker stop interview-pg
```

Technical references, undated live documentation accessed 2026-09-22:
[PostgreSQL 18 isolation](https://www.postgresql.org/docs/18/transaction-iso.html),
[explicit locking](https://www.postgresql.org/docs/18/explicit-locking.html),
[EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html),
[CLUSTER](https://www.postgresql.org/docs/18/sql-cluster.html),
[HOT](https://www.postgresql.org/docs/18/storage-hot.html). These support semantics,
not dated evidence that a company asks this constructed exercise.
