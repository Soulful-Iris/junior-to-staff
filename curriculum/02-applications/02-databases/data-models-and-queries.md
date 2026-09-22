# Data and databases

[Curriculum](../../README.md) · [Databases and transactions](README.md)

> Project connection · feeds **P1 (it works)**

> **Constructed candidate brief:** “Ana and Ben share a reading list. Ana marks
> article 7 read; Ben must still see it unread. Model that fact, then show how
> two concurrent requests preserve it. What would you clarify before writing SQL?”

| Input | Expected result | Boundary |
|---|---|---|
| Ana reads article 7 twice | One `(Ana, 7)` read-mark | A database unique constraint rejects duplicates |
| Ben lists unread articles | Article 7 remains unread | Missing per-person history cannot be invented |
| List 20 newest items for owner 2 | At most 20 rows ordered by time and ID | Performance must be measured with realistic selectivity |

Start by naming the fact, writing its key, and trying an illegal write. Then
measure one query, inspect its plan, and change the index only if the evidence
supports it. The [PostgreSQL lab](labs/postgresql/README.md)
provides schema, seed data, racing sessions, and a separate assessor guide.

## The one-liner

Code can be rewritten any afternoon. Data has to be carried, live and intact,
through every rewrite — which makes the schema the one decision in a young
system that is hard to take back. A fact you never recorded cannot be
recovered at any price.

## The failure it prevents

You build the reading list. The screen shows one checkbox per item, so the
schema gets a `read` boolean on `items`. It demos perfectly.

Two weeks later the group is five people. Ana marks an article read and it
vanishes from everyone's unread view, because "read" was stored on the item
when it was always a fact about a person *and* an item. The code fix is an
afternoon: a new table, one row per person per item.

Then the real cost arrives. The new table should hold history — who had read
what before tonight — and that was never written down. There is nothing to
backfill from. Nothing crashed, every test stayed green, and a piece of the
past is gone.

Code bugs cost time. Schema bugs cost data, and they are committed on the
quietest day, when someone models the checkbox instead of the fact.

## The mental model

**1. Data outlives code, so model the thing, not the screen.** A schema is a
set of claims about the world: *one row here means one person read one item.*
Screens change weekly; the claims are enforced on every row ever written. The
test: say what one row of each table asserts. If the sentence describes a page
rather than a thing, the screen is leaking in.

**2. Normalisation, in plain words: store each fact once.** If a team's name
lives in forty rows, a rename is forty updates, and a crash after twelve leaves
a database that disagrees with itself. Normalising gives each fact one home and
points at it from everywhere else. Denormalising — a deliberate copy, like a
cached count — is sometimes right when a *measured* read is too slow, but
keeping the copies true becomes your job. Do it late, on evidence.

**3. A join is a lookup you can reason about.** A foreign key is a value naming
a row in another table. A join says: for each row here, find the rows there
whose key matches. The whole cost lives in *find* — check every row (a scan) or
seek in something kept sorted (an index). Any join yields to two questions: how
many rows survive the filters on each side, and how are the matches found.

**4. Keys — and where their order matters.** A natural key is a real-world
value (an email); a surrogate key is generated and meaningless. Natural keys
break when the world changes — people change emails — so a surrogate can keep
references stable while a separate unique constraint protects the real value.
In PostgreSQL, a primary key normally has a B-tree index separate from the
**heap**, the pages containing row versions. Ordered identifiers can concentrate
inserts in recent **index** pages; random identifiers spread index access. The
cache, workload, and page occupancy determine the measured cost. Neither choice
keeps heap rows sorted by primary key. `CLUSTER` explicitly reorders a heap once;
later writes do not maintain that ordering. A newest-items query still needs an
index matching its owner filter and time ordering.

**5. An index is a purchase, and the planner holds the receipt.**

![One read uses a single sorted index to reach its row in a few page reads; one insert must also write the table and every index on it](../../../assets/diagrams/index-cost.svg)

An index is a sorted copy of chosen columns with pointers back to the rows.
Reads matching its shape can get faster; inserts maintain the table and its
applicable indexes, and the copies take disk. An update creates a new row
version, but PostgreSQL's heap-only tuple (HOT) optimization can avoid new
ordinary index entries when indexed columns are unchanged and the old page
has enough room; summarizing indexes have additional rules. Whether an index is used
is not your call either — the planner decides, from statistics about your
actual data, and can rightly decide differently at a thousand rows than a
million. Query-speed arguments are settled by `EXPLAIN`, because intuition does
not execute queries and the planner does.

**6. "Atomic" means both writes or neither.** The classic bug: debit one
account, crash, never credit the other. No error anywhere — the money is gone,
because two writes that only make sense together happened separately. A
transaction is the database's promise that if the process dies between them,
the world looks as if nothing started. A migration is the same problem
stretched over days, old code still running while the shape changes: add first,
then backfill, then switch, only then remove. Never a destructive change in one
step — there is no moment when nothing is reading.

**7. Where juniors reliably lose data: NULL, time zones, money.** NULL means
three things — unknown, not applicable, not yet — and where nobody wrote down
which, sums, joins and comparisons quietly skip rows: default to NOT NULL,
comment every exception. A timestamp without a time zone is a time nowhere:
store instants in UTC (PostgreSQL's `timestamptz` stores the instant), keeping
a zone only where wall-clock time *is* the fact, like a calendar event. Binary
floats cannot represent 0.10 exactly, so money in a `float` drifts by rounding
until an audit finds it: store integer minor units or a decimal type.



## What good looks like

- You can say what one row asserts, for every table, in one sentence.
- Every relationship is a foreign key the database enforces, not a convention
  the application remembers.
- Columns are NOT NULL by default; every exception has a written meaning.
- Each fact lives in one place; every deliberate copy names what keeps it true.
- Timestamps are UTC instants; money is integer minor units or a decimal type.
- Each index exists because a measured plan asked for it, and every migration
  ran forwards and backwards on a copy first.

Done badly, you see:

- Tables named after screens.
- `read` and `deleted` booleans where the fact belonged to a pair, or needed a
  *when* (`deleted_at`).
- NULL everywhere, meaning something different in every column.
- No foreign keys "for flexibility", and rows pointing at rows that no longer
  exist.
- Prices in `float`, off by a cent somewhere nobody can find.
- A migration that adds the new column and drops the old in one deploy — a
  minute of errors while old code runs against the new schema.

## Ask Claude for this

(The design ask — model before code — already lives on P1's page. These two
judge what comes back.)

**Request 1 — reviewing a schema a model proposed**

```
Here is the schema you proposed. Review it as data, not as code.

For each table: what real-world change would force an ALTER? Which facts
are stored in more than one place? Which query the product must answer
at 100,000 rows has no index shaped for it?

Check specifically: every money column's type, every timestamp's time
zone, every nullable column's meaning, every uniqueness that is assumed
but not declared, and any primary key whose randomness scatters inserts
across the index.

Finish with the one change that is cheapest now and most expensive in
six months.
```

*Why:* models default to the same schema weaknesses — nullable
everything, floats for money, naive timestamps, undeclared uniqueness, flags
where a pair table or an `_at` timestamp belongs, tables shaped after your
prompt rather than the domain. The checklist points the review at those; a bare
"review this schema" returns compliments and an index suggestion.

*What you should get back:* findings that cite specific columns, at least one
undeclared uniqueness (there is almost always one), and a closing ranked by
reversibility.

*Push back on:* a review that finds nothing. Plant a `price float` column and
run it again; if the review misses the plant, it is not measuring anything.

**Request 2 — the migration that cannot be one step**

```
The live system stores read as a boolean on items. It must become
per-person. Old code keeps running while this changes.

Plan the migration as separate deploys. For each step: what the old code
sees, what the new code sees, and what happens if the process dies
halfway through it. Never create something and remove its predecessor in
the same step.

End by telling me what the new table cannot be backfilled with, and what
we should record about that.
```

*Why:* "old code keeps running" is the constraint that kills one-step
migrations, and the dies-halfway question forces each step to be safe alone.

*What you should get back:* three to five steps — add, backfill, switch, then
remove — and a plain admission that per-person history from before the change
does not exist.

*Push back on:* a backfill that invents facts. Marking each item read by
whoever added it looks plausible and is fiction; the honest version records
the assumption.

## How you would know it is wrong

1. **Run `EXPLAIN (ANALYZE, BUFFERS)` on your main query.** Compare estimated
   versus actual rows, heap/index pages, sort work, and time. A sequential scan
   may correctly beat scattered heap lookups for a broad filter or a tiny table.
   Large estimate errors invite checking statistics, skew, correlated columns,
   and parameters; stale statistics are one cause, not the only one.
2. **Insert 100,000 rows and time the same query.** In PostgreSQL,
   `generate_series` makes seeding a one-liner. Everything is fast at 200 rows;
   hold result size and selectivity explicit. An indexed query may still grow
   with the number of returned rows, heap reads, cache misses, or sorting.
3. **Kill the process mid-transaction.** Put a sleep between two writes that
   only make sense together, `kill -9` in the gap, restart, count. If half the
   change is visible, those writes were never in one transaction — and now you
   have seen the check go red.
4. **Run every migration forwards and backwards on a copy.** Row counts and a
   spot-check query must survive the round trip. A down step that cannot
   restore what the up step removed means the up step was destructive.
5. **Attempt the illegal writes from `psql`, not the app.** An item with no
   owner; a duplicate of something you believe unique; NULL into a mandatory
   column. The refusal must come from the database — the migration script, the
   console and next year's rewrite do not run application code.

> The standing rule: before believing a green result, say what broken would
> have looked like. A constraint you have never seen refuse anything has passed
> a test that cannot fail.

## Your slice of the project

On **P1**, add:

- The schema as your first migration files: users, items, and your answers to
  P1's tag and read-state decisions — every relationship an enforced
  foreign key, every column NOT NULL unless a comment says what NULL means.
- A seed script that inserts 100,000 items, so your numbers mean something.
- The `EXPLAIN ANALYZE` output of the group-list query at that size, saved with
  two sentences: what the planner chose, and why that is fine — or the index
  you added.
- One additive migration *after* seeding — a `fetched_at` column with a
  backfill — run forwards and backwards on a copy first.

**Acceptance criteria you can check yourself:**

- From `psql`, the database refuses: an item with no owner, a duplicate
  read-mark for the same person and item, a NULL URL.
- "Who has read this item" and "what has this person read" are each one query,
  with no schema change between them.
- Plans and timings at small, large, and skewed cardinalities are written down;
  explain rows visited and returned, rather than requiring a fixed speed ratio.
- Deleting a user is a decision — cascade or refuse — proven by a test
  (see [Testing](../04-testing/testing-strategy.md)).

## Words you now own

- **schema** — the shape of your data and the rules between its parts.
- **primary key** — the value that names a row, forever.
- **foreign key** — another row's key, enforced by the database.
- **surrogate key** — a generated id with no real-world meaning.
- **normalisation** — each fact stored once, referenced everywhere else.
- **denormalisation** — a deliberate copy; keeping it true is your job.
- **index** — a sorted copy bought with write time and disk.
- **query planner** — picks how to run a query from statistics, not intent.
- **EXPLAIN** — the plan; with ANALYZE, what actually happened.
- **transaction** — writes that succeed together or leave no trace.
- **migration** — a versioned change to schema and the data under it.
- **backfill** — filling values for rows older than the column.

---

**Not covered here:** ORMs, deliberately — learn to read tables and plans
first, so you can read what an ORM later writes for you. Document and key-value
stores and replication continue in [Data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md).
Isolation and locking have a [PostgreSQL lab in this chapter](labs/postgresql/README.md);
restore and recovery exercises continue in [Migrations and recovery](../../04-scale-and-evolution/04-migrations/README.md).

[Learning sequence](../../README.md) · [Independent practice](../../../practice/interview-guide.md)

## Draw it from memory · Model ownership before adding indexes

```mermaid
erDiagram
  USER ||--o{ MEMBERSHIP : joins
  GROUP ||--o{ MEMBERSHIP : contains
  GROUP ||--o{ BOOKMARK : owns
  USER ||--o{ BOOKMARK : creates
  BOOKMARK ||--o{ BOOKMARK_TAG : has
  TAG ||--o{ BOOKMARK_TAG : labels
  BOOKMARK {
    uuid id PK
    uuid group_id FK
    uuid created_by FK
    datetime created_at
    int version
  }
```

**Redraw challenge:** Point to the foreign key that bounds a group-scoped read. Then name the index for its ordering.

![Model ownership before adding indexes: mechanism in motion](../../../assets/learning/index-seek.svg)

[Static view](../../../assets/learning/index-seek-still.svg)

Predict the change before drawing: the baseline stores one global checkbox;
the corrected model makes the person part of the key.

```mermaid
flowchart TD
  Ana["Ana: mark read"] --> Item["Item 7: read=true"]
  Item --> Ben["Ben: article incorrectly hidden"]
```

```mermaid
flowchart TD
  Write["Ana: mark article 7 read"] --> Pair["Read mark: unique person + item"]
  Pair --> Heap["Heap: row versions"]
  Index["B-tree: person + item"] -->|"row location"| Heap
  Ben["Ben: owner-scoped unread query"] -->|"no Ben mark"| Visible["Article 7 visible"]
```

**Senior follow-up:** preserve stock and a two-row on-call invariant under racing
transactions in the lab. **Lead follow-up:** budget lock time and write overhead
while adding an index. An assessor should ask for the failed schedule before the
repair, the invariant after it, and an explanation of why a different planner
choice can be correct.

Technical sources: [PostgreSQL 18 CLUSTER](https://www.postgresql.org/docs/18/sql-cluster.html)
and [HOT](https://www.postgresql.org/docs/18/storage-hot.html). Live, undated
technical documentation; accessed 2026-09-22, not recent interview evidence.
