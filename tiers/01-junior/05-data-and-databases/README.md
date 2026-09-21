# 05 · Data and databases

> Junior tier · feeds **P1 (it works)**

## The one-liner

Code can be rewritten any afternoon. Data has to be carried, live and intact,
through every rewrite, which makes the schema the one decision in a young
system that is genuinely hard to take back — and a fact you never recorded
cannot be recovered at any price.

## The failure it prevents

You build the reading list. The screen shows one checkbox per item, so the
schema gets a `read` boolean on the `items` table. It demos perfectly.

Two weeks later the group is five people. Ana marks an article read and it
vanishes from everyone's unread view, because "read" was stored as a fact about
the item when it was always a fact about a person *and* an item. The code fix
is an afternoon: a new table, one row per person per item.

Then the real cost arrives. The new table should hold history — who had read
what before tonight — and that was never written down. There is nothing to
backfill from. Nothing crashed, every test stayed green, and a piece of the
past is simply gone.

Code bugs cost time. Schema bugs cost data, and they are committed on the
quietest day of the project, when someone models the checkbox on the screen
instead of the fact in the world.

## The mental model

**1. Data outlives code, so model the thing, not the screen.** A schema is a
set of claims about the world: *every item has one owner; one row here means
one time a person read an item.* Screens change weekly; the claims are enforced
on every row ever written. The test: say aloud what one row of each table
asserts. If the sentence describes a page rather than a thing, the screen is
leaking into the model.

**2. Normalisation, in plain words: store each fact once.** If a team's name
lives in forty rows, renaming it is forty updates, and a crash after twelve
leaves a database that disagrees with itself. Normalising gives each fact one
home and points at it from everywhere else. Denormalising — a deliberate copy,
like a cached count — is sometimes right when a *measured* read is too slow,
but keeping the copies true becomes your job. Do it late, on evidence.

**3. A join is a lookup you can reason about.** A foreign key is a value that
names a row in another table. A join says: for each row here, find the rows
there whose key matches. The whole cost lives in the word *find* — check every
row (a scan) or seek in something kept sorted (an index). Any join yields to
two questions: how many rows survive the filters on each side, and how are the
matches found. You never need the join-type vocabulary to answer either.

**4. Keys — and why their order is physical.** A natural key is a real-world
value (an email); a surrogate key is generated and meaningless. Natural keys
break when the world changes — people change emails — so rows usually get a
surrogate key, with the real value kept as a plain unique column. The primary
key lives in a B-tree, kept sorted. Fully random UUIDs land each new row on a
random page of it; once the index outgrows memory, a typical insert fetches a
cold page from disk and often splits it. Time-ordered ids land at the same
recent edge, on a few hot pages already in cache, and rows created together
stay stored together — what "latest items" queries want. UUIDv7 (RFC 9562,
2024) puts a millisecond timestamp in the first 48 bits for this reason;
PostgreSQL 18 (released 25 September 2025; checked 2026-09-21) ships it as
`uuidv7()`, at the price that an id now reveals its row's age. The function is
trivia; the idea — identifier order is physical — is not.

**5. An index is a purchase, and the planner holds the receipt.**

![One read uses a single sorted index to reach its row in a few page reads; one insert must also write the table and every index on it](../../../assets/diagrams/index-cost.svg)

An index is a sorted copy of chosen columns with pointers back to the rows.
Reads matching its shape get fast; in exchange, every insert and update writes
the table *and* every index, and the copies take disk. You also do not decide
whether an index is used — the query planner does, from statistics about your
actual data, and it can rightly choose differently at a thousand rows than at
a million. Arguments about query speed are settled by `EXPLAIN`, because
intuition does not execute queries and the planner does.

**6. "Atomic" means both writes or neither.** The classic bug: debit one
account, crash, never credit the other. No error anywhere — the money is simply
gone, because two writes that only make sense together happened separately. A
transaction is the database's promise that if the process dies between them,
the world looks as if nothing started. A migration is the same problem
stretched over days, with old code still running while the shape changes: add
first, then backfill, then switch, only then remove. Never a destructive change
in one step — there is no moment when nothing is reading.

**7. Where juniors reliably lose data: NULL, time zones, money.** NULL means
three different things — unknown, not applicable, not yet — and where nobody
wrote down which, sums, joins and comparisons quietly skip rows: default to
NOT NULL and comment every exception. A timestamp without a time zone is a time
nowhere: store instants in UTC (PostgreSQL's `timestamptz` stores the instant
and converts on display), keeping a zone only where wall-clock time *is* the
fact, like a calendar event. Binary floats cannot represent 0.10 exactly, so
money in a `float` drifts by rounding until an audit finds it: store integer
minor units or a decimal type.

## What good looks like

- You can say what one row asserts, for every table, in one sentence.
- Every relationship is a foreign key the database enforces, not a convention
  the application remembers.
- Columns are NOT NULL by default; every nullable column has a written meaning.
- Each fact lives in one place; every deliberate copy names what keeps it true.
- Timestamps are UTC instants; money is integer minor units or a decimal type.
- Each index exists because a measured plan asked for it.
- Every migration ran forwards and backwards on a copy of real data first.

Done badly, you see:

- Tables named after screens, reshaped at every redesign.
- `read` and `deleted` booleans where the fact belonged to a pair of things, or
  needed a *when* (`deleted_at`).
- NULL everywhere, meaning something different in every column.
- No foreign keys "for flexibility", and rows quietly pointing at rows that no
  longer exist.
- Prices in `float`, off by a cent, and a reconciliation spreadsheet nobody
  admits to owning.
- An index on every column just in case: writes crawl, the planner ignores half.
- A migration that adds the new column and drops the old in the same deploy,
  and a minute of errors while old code runs against the new schema.

## Ask Claude for this

**Request 1 — the schema, before any code**

```
I am building a shared reading list: a group signs in, adds URLs, tags
them, and each person marks items read for themselves.

Propose the schema. For every table, give the sentence one row asserts
("one row = one ..."). For every column: can it be NULL, and what does
NULL mean there? List the rules the database itself will enforce —
unique, foreign key, NOT NULL — separately from the rules only the
application would enforce.

Then name the three decisions you are least sure of, and for each, the
future requirement that would prove it wrong. No code yet.
```

*Why:* the row-sentence forces tables to be nouns — a table you cannot say as a
sentence is usually a screen in disguise. The NULL question and the
enforced-versus-promised split surface the two places schemas rot first, and
the "least sure" list extracts the model's own uncertainty, which "is this
good?" never does.

*What you should get back:* nouns — people, items, tags, a person-item table
for read-state — with explicit NULL meanings. If "read" comes back as a boolean
on items, you are holding the failure story above in written form.

*Push back on:* any rule left to the application "for flexibility". The
application is only one of the things that will write to this database,
alongside the migration script, the console and next year's rewrite.

**Request 2 — reviewing a schema a model proposed**

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

*Why:* models writing schemas default to the same weaknesses — nullable
everything, floats for money, naive timestamps, undeclared uniqueness, flags
where a pair table or an `_at` timestamp belongs, tables shaped after your
prompt rather than the domain. The checklist points the review at exactly
those; a bare "review this schema" returns compliments and an index suggestion.

*What you should get back:* findings that cite specific columns, at least one
undeclared uniqueness (there is almost always one), and a closing ranked by
reversibility rather than effort.

*Push back on:* a review that finds nothing. Plant a `price float` column and
run it again; if the review misses the plant, it is not measuring anything.

**Request 3 — the migration that cannot be one step**

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
migrations, and the dies-halfway question forces each step to be safe on its
own.

*What you should get back:* three to five steps — add, backfill, switch, then
remove — and a plain admission that per-person history from before the change
does not exist.

*Push back on:* a backfill that invents facts. Marking each item read by
whoever added it looks plausible and is fiction; the honest version records
the assumption.

## How you would know it is wrong

1. **Run `EXPLAIN ANALYZE` on your main query and read it.** A sequential scan
   over the big table under a selective filter means the index is missing or
   unusable by that query. Then compare estimated row counts to actual ones in
   the same output: estimates off by orders of magnitude mean stale statistics,
   and plans chosen on fiction.
2. **Insert 100,000 rows and time the same query.** In PostgreSQL,
   `generate_series` makes seeding a one-liner. Everything is fast at 200 rows;
   if query time grows in step with table size you are scanning, because an
   indexed lookup should barely move.
3. **Kill the process mid-transaction.** Put a sleep between two writes that
   only make sense together, `kill -9` in the gap, restart, count. If half the
   change is visible, those writes were never in one transaction — and now you
   have seen the check go red, which is worth a week of green.
4. **Run every migration forwards and backwards on a copy.** Row counts and a
   spot-check query must survive the round trip. A down step that cannot
   restore what the up step removed is telling you the up step was destructive
   — a red result on the copy, where it is cheap.
5. **Attempt the illegal writes from `psql`, not the app.** An item owned by a
   user id that does not exist; a duplicate of something you believe unique;
   NULL into a mandatory column. The refusal must come from the database. If it
   accepts, your rules live only in application code — and the migration
   script, the console and next year's rewrite do not run application code.

> The standing rule: before believing a green result, say what broken would
> have looked like. A constraint you have never seen refuse anything has passed
> a test that cannot fail.

## Your slice of the project

On **P1**, add:

- The schema, as your first migration files: users, items, and your written
  answers to P1's tag and read-state decisions — every relationship an enforced
  foreign key, every column NOT NULL unless a comment says what NULL means.
- A seed script that inserts 100,000 items, so your numbers mean something.
- The `EXPLAIN ANALYZE` output of the group-list query at that size, saved with
  two sentences: what the planner chose, and either why that is fine or which
  index you added because it was not.
- One additive migration performed *after* seeding — add a `fetched_at` column
  with a backfill — run forwards and backwards on a copy first.

**Acceptance criteria you can check yourself:**

- From `psql`, the database refuses: an item with no owner, a duplicate
  read-mark for the same person and item, a NULL URL.
- "Who has read this item" and "what has this person read" are each one query,
  with no schema change between them.
- The main list query's time barely moves between 1,000 and 100,000 rows, and
  both timings are written down.
- Deleting a user is a decision — cascade or refuse — written down and proven
  by a test (see [06 · Testing](../06-testing/)).

## Words you now own

- **schema** — the shape of your data: tables, columns and the rules between them.
- **primary key** — the value that names a row uniquely, forever.
- **foreign key** — a column holding another row's key, enforced by the database.
- **surrogate key** — a generated identifier with no real-world meaning.
- **normalisation** — each fact stored once and referenced, so copies cannot disagree.
- **denormalisation** — a deliberate copy kept for read speed; keeping it true is now your job.
- **index** — a sorted copy of chosen columns, bought with write time and disk.
- **query planner** — decides how to run your query, from statistics rather than your intent.
- **EXPLAIN** — the planner showing its plan; with ANALYZE, what actually happened.
- **transaction** — writes that succeed together or leave no trace.
- **migration** — a versioned change to the schema and the data already under it.
- **backfill** — filling in values for rows that existed before the column did.

---

**Not covered here:** ORMs, deliberately — read tables and plans directly
first, so that when an ORM later writes queries for you, you can read what it
wrote. Document and key-value stores are real answers for data that is not
row-shaped and belong to the senior tier, as do isolation levels, locking,
replication and backups-you-have-actually-restored.
