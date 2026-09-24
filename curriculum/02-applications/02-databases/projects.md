# 05 · Data and databases — five projects

> Junior tier · each one an afternoon · read [Model data and enforce transactional rules](README.md) first

Five projects, rising. Each one ends with an artefact you did not have before:
a written defence, a rehearsal log, two query plans, a race that can no longer
be lost, a restore timed in minutes.

The code in all five is disposable and the data is not — that asymmetry is the
whole section. What you are practising is making the decisions that are hard to
take back while they are still cheap, and getting an AI to prove its work with
checks that could actually have gone red.

![A schema change in four steps — add the new table, backfill it, switch the code, drop the old column — with a reversal rail underneath showing each step's down migration. The first three walk back cleanly; a dashed wall before the drop marks the point of no return, where the down step can re-create the column but not its contents, and an animated marker runs the migration up, back down, then up past the wall and does not come back](../../../assets/diagrams/migration-both-ways.svg)

---

### 1. The schema you can defend

*You end up with P1's schema as migration files, plus a written account of what
every choice makes hard — including the cost of a query you have not written
yet.*

**Build**

The reading list's tables — people, items, tags, per-person read state — as
your first migration, every rule enforced by the database itself. Next to it,
`DECISIONS.md`: one sentence per table saying what a row asserts, and for each
choice, the future change or query it makes expensive.

**The thought process**

The first decision is what the facts are, and it happens before any
`CREATE TABLE`. Say out loud what one row of each table will assert. "A person
read an item" is a fact about a pair, so it is a table, not a boolean on
`items`. A tag needs the same interrogation: if two people tag one item
differently, is that two facts or a conflict? The answer decides between a join
table and a column, and no syntax can decide it for you.

Second: which rules the database enforces and which the application merely
remembers. The migration script, the psql console and next year's rewrite do
not run your application code, so any rule that matters — ownership,
uniqueness, a URL that must exist — lives in the schema or it is a suggestion.

Third, the part almost nobody writes down: the queries you have not written
yet. Every schema makes some future question cheap and a different one
expensive. "Items nobody in the group has read yet" — what does that cost
against your shape? Pricing three such queries now, while you still remember
why you chose, is what makes the schema defensible later. A defensible schema
is not one without weaknesses; it is one whose weaknesses were priced before
they were discovered.

**How to organise the prompts**

**1. The model, before any SQL.**

```
Model a shared reading list: people, items with URLs and fetched titles,
tags, and per-person read state. Do not write SQL yet.

For each table: one sentence stating what a single row asserts about the
world; every uniqueness you are relying on; what NULL would mean in any
nullable column. Then name the three decisions here most likely to be
wrong.
```

Check the sentences before anything else. One that describes a page — "a row
is an entry in the group view" — means the screen leaked into the model.

**2. The review, with a plant in it.**

Before asking for the review, quietly damage the proposal in one known way —
make a timestamp zone-less, or move `read` back onto `items` — because a
review is only an instrument if you know what it must catch.

```
Review this schema as data, not code. For each table: what real-world
change would force an ALTER; which facts live in more than one place;
which query at 100,000 rows has no index shaped for it. Check every
timestamp's zone, every nullable column's meaning, every uniqueness
assumed but not declared. End with the one change that is cheapest now
and most expensive in six months.
```

If the review misses your plant, it is compliments, not measurement — tighten
it and rerun before trusting anything else it found.

**3. The DDL, and the refusals.**

```
Write the schema as migration files. Every relationship an enforced
foreign key; columns NOT NULL unless a comment says what NULL means.
Then give me, as psql commands, three INSERTs the database must refuse —
an item with no owner, a duplicate read-mark, a NULL URL — and one it
must accept.
```

Run all four by hand. The refusals must come from the database, with a
constraint name in the error, and the accept must accept.

**On AWS**

The same modelling question decides the service. **RDS for PostgreSQL** is the
default: managed Postgres, your schema and your plans identical to local.
**Aurora PostgreSQL** buys faster failover and read scaling — real money for a
problem a reading list does not have yet. **Aurora Serverless v2** is the
interesting neighbour for a side project: capacity follows load and, since
late 2024, can pause to zero when idle (checked 2026-09-22 — storage still
bills while paused, and the first request afterwards waits around fifteen
seconds for resume). **DynamoDB** is not "NoSQL instead of SQL" as fashion: it
trades away ad-hoc joins to buy fixed-cost key lookups at any scale, which
means knowing every query at design time — the opposite of the position you
are in.

Build the project itself against Postgres in a local container, which costs
nothing. Note the free tier changed shape on 15 July 2025 (checked
2026-09-22): accounts created since then get a credit pool rather than the old
twelve months of free micro-instance hours, so "there is a free RDS instance"
is only true on older accounts. DynamoDB keeps an always-free storage tier
either way.

**What productionising it means**

The schema exists only as migration files under version control — nothing
hand-created in a console — so any environment can be rebuilt identically.
`DECISIONS.md` lives next to them, because the second person on the project
should read the trade-offs, not re-derive them from the columns. And the
constraints are the production feature: a database that refuses a bad row at
3am is the one reviewer that never sleeps.

**The learning**

A schema is a set of claims about the world, enforced on every row ever
written, and the expensive mistakes are the commitments made silently. After
writing the defence once, you will not see a `read` boolean again without
asking whose.

**How you would know it is wrong**

- The three illegal INSERTs, from psql: every refusal must come from the database. An accepted duplicate read-mark means the uniqueness lives only in your head.
- Say each table's one-row sentence aloud. If it needs an "and also", two facts are sharing one table.
- The planted flaw: a review that missed it measured nothing, and its other findings are unproven.
- Ask for "who has read this item" and "what has this person read" as SQL. If either needs a schema change, you modelled the checkbox after all.

---

### 2. The migration that runs both ways

*You end up having run a real schema change forwards, backwards and forwards
again on a copy — and able to name the exact step where reversibility ends.*

**Build**

The change this section's failure story is about: `items.read` becomes a
per-person `reads` table while the system stays up. Separate up and down files
for each step, a log of the whole sequence run up, down and up again on a copy
of the database, and one paragraph naming the irreversible step and what you
kept because of it.

**The thought process**

The first decision is what a "step" even is, and the answer is a deploy, not a
statement — because old code keeps running while the shape changes. That one
constraint generates the order in the diagram above: add the table (nothing
reads it, harmless), backfill it (the old column stays canonical), switch the
code, and only then remove. Each step has to leave both the previous and the
next version of the code working, and has to be safe if the process dies in
the middle of it.

Second, the backfill honesty problem. The boolean says an item was read; it
never said by whom. Any backfill therefore invents the who. Attributing every
old mark to the item's owner is plausible-looking fiction; leaving history
empty is honest but loses the past openly. Either can be defended — what
cannot is a guessed row that looks identical to a true one in six months.
Record the assumption in the data itself, or you have laundered a guess into a
fact.

Third, the window between switch and remove: who keeps the old column true
now? If nobody, rolling back tomorrow silently discards a day of read-marks.
Deciding how long the old column stays maintained — and writing a date on the
remove step — is the difference between a rollback plan and a hope.

Last, the audit the project is named for: write the down step for every up
step and ask what it actually restores. Three of them restore the world. The
fourth re-creates a column and not its contents. That is the point of no
return, and everything you keep — the backup, the soak time — you keep because
of it.

**How to organise the prompts**

**1. The plan, judged by its shape.**

```
The live system stores read as a boolean on items. It must become a
per-person reads table while old code keeps running. Plan it as separate
deploys. For each: what the old code sees during it, what breaks if the
process dies halfway through it, and the exact down migration. Flag any
step that creates something and removes its predecessor in one deploy.
```

You are checking shape, not SQL: four or five steps, and nothing flagged. A
combined add-and-drop is the one-deploy migration wearing a costume.

**2. The files, with the assumption recorded.**

```
Write the up and down files. The backfill must be idempotent — running it
twice changes nothing the second time — and must mark the rows it
creates as backfilled, because attributing old read-marks to the item's
owner is an assumption, not a fact.
```

Prove idempotence immediately: run the backfill twice on the copy and diff the
counts. Identical or it goes back.

**3. The rehearsal, both directions.**

```
Here is a copy of the database. Run: all steps up, all steps down, all
steps up again. After each full pass, print per-table row counts and a
checksum of reads. Show me where the second up differs from the first,
and name the down step that cannot restore what its up step removed.
```

The named step must be the drop. If the second up differs anywhere else, some
down step is quietly leaving debris behind.

**On AWS**

The copy you rehearse on is the teaching moment. On RDS, restoring a backup
**creates a new instance** — a restore never overwrites the original (checked
2026-09-22) — so rehearsing a migration on a restored copy is the same motion
as recovering from a disaster, practised early. Locally, `pg_dump` into a
second container is the free version and is enough here.

**RDS Blue/Green deployments** is the managed neighbour: a synchronised green
copy of production that you change and then switch to, with guardrails. Know
why it is not this project's tool: it is built for engine upgrades and
maintenance, and DDL on the blue side degrades its replication (checked
2026-09-22) — the expand-and-contract dance stays yours. **AWS DMS** is the
heavy case: when a change is too large to run in place — a huge table
rewritten, an engine swapped — DMS copies data into the new shape while
change-data-capture keeps it current, and "switch" becomes moving traffic. For
a reading list that is a crane lifting a chair; the skill is knowing which
side of the line a migration sits on.

**What productionising it means**

Migrations run by the pipeline, never by hand, one step per deploy with real
time between them. The backfill is a job that can stop and resume, because
production tables are bigger than yours. And the remove step carries, in its
own commit message, the backup that precedes it and the date it is allowed to
run.

**The learning**

Reversibility is a property of each step, not of the migration — and the point
of no return is not where it feels dangerous. It is the shortest,
most innocent-looking line in the sequence, whose down step lies by restoring
shape without contents.

**How you would know it is wrong**

- Run the downs on a fresh copy after a full up. Any error means the downs were decoration that had never once executed.
- Kill the backfill halfway and run it again. Duplicate rows mean it was never idempotent, and production would have discovered that for you.
- After the switch step, run the previous version of the code against the copy. It must still work — that compatibility is the rollback plan.
- Count the backfilled rows marked as assumed. Zero means the guess got laundered into fact after all.

---

### 3. Read the planner, not the code

*You end up with two saved query plans — before and after one index — and a
written prediction the planner corrected.*

**Build**

A seed script that grows a copy of P1 to 100,000 items with realistic skew,
the group-list query explained before and after one index, and a short file:
your predicted plan, the two real plans, and timings at 1,000 and 100,000
rows.

**The thought process**

First decide which query earns the attention: the one the product runs on
every load — unread items for this group, newest first. An index chosen
without a query in hand is decoration you pay for on every write.

Then commit to a prediction before running anything. Which table is scanned
how, which index is used, roughly how many rows survive each step — written
down. The project is not "make the query fast"; it is calibrating your model
of the database against the planner's, and a guess you never committed to
cannot be wrong, so it cannot teach.

Seeding is where the honest version differs from the tutorial version.
Uniform random data lies: real lists have heavy users and popular tags, and
the planner chooses from statistics about the actual shape. Two traps here.
Seed server-side with `generate_series`, because a client-side loop of 100,000
INSERTs will spend your afternoon on network round trips. And run `ANALYZE`
after seeding, because statistics gathered at 200 rows describe a table that
no longer exists, and every plan chosen on them is fiction.

Then read the plan as evidence rather than a verdict: estimated rows against
actual rows (orders of magnitude apart means stale statistics), where the time
went, whether the sort came free. Only then shape the index — column order
following the query's filters, the sort it could inherit — and say what it
costs, because the section's rule holds: every index is one more copy that
every write must keep true.

**How to organise the prompts**

**1. The seed, with skew.**

```
Write a seed script for this schema using generate_series, server-side:
100,000 items across 50 users with a few heavy users, tags with a few
popular ones, read-marks on about a third of items, skewed recent.
Print per-table counts and the top-5 users and tags when done.
```

Check the skew is real — the top user should dwarf the median — then run
ANALYZE yourself. A script printing counts is not the database updating its
statistics.

**2. The prediction, then the plan.**

```
Here is the group-list query. Before executing anything, predict the
plan: which tables are scanned how, which indexes are used, how many
rows survive each step. Then run EXPLAIN (ANALYZE, BUFFERS) and list
every place the real plan disagrees with the prediction.
```

The disagreements are the product. Keep them — that is your calibration error,
written down.

**3. One index, priced.**

```
Propose exactly one index for this query. Justify the column order, state
what it costs every INSERT and UPDATE on the table, and predict the new
plan. Create it, re-run EXPLAIN (ANALYZE, BUFFERS), and give me timings
at 1,000 and at 100,000 rows.
```

If the planner ignores the index, do not add another — find out why
(selectivity, statistics, a shape mismatch) before spending more write time.

**On AWS**

The planner is PostgreSQL's, not AWS's — the same plans come out of a free
local container as out of a production instance, which is why this project
runs locally. What the managed service changes is the knobs and the
visibility. On **RDS** there is no `postgresql.conf` to edit;
planner-relevant settings like `work_mem` live in a **parameter group**, worth
touching once on a toy because it is how every future tuning change ships.
For visibility, **RDS Performance Insights** shows which queries actually hold
the database busy over time — the managed answer to "which query should I even
be explaining" — and **pg_stat_statements** is the same answer kept inside the
engine, portable to anywhere Postgres runs. **Aurora** changes storage,
failover and read scaling, not the planner; moving there expecting different
plans buys nothing.

**What productionising it means**

The plan file is committed next to the migration that adds the index, so the
reasoning survives the person. Staging stays seeded at production-like size,
because plans at 200 rows approve queries that die at a million. And once a
quarter someone reads `pg_stat_user_indexes` for indexes with zero scans —
each one is write tax with no product attached.

**The learning**

Intuition does not execute queries; the planner does, from statistics about
your actual data. The day query speed stops being a matter of opinion on your
team is the day arguments end with EXPLAIN output pasted into the thread.

**How you would know it is wrong**

- Estimated versus actual rows off by orders of magnitude: run ANALYZE and re-explain. If the plan changes, every conclusion before it stood on fiction.
- Timing that grows in step with table size between 1,000 and 100,000 rows means you are still scanning, whatever you believe the plan says.
- `BEGIN; DROP INDEX ...; EXPLAIN ANALYZE ...; ROLLBACK;` — the query must get slower without the index. If it does not, the index was never doing anything.
- An index on the raw read boolean should be ignored by the planner. If you believe it is used, prove it from `pg_stat_user_indexes`, not from hope.

---

### 4. The transaction that actually holds

*You end up with a lost update you built, watched happen, fixed two ways, and
can prove fixed with a test that races.*

**Build**

A read counter on items, implemented read-modify-write on purpose; a harness
that races two writers at the same row until the bug shows on every run; then
the fix, with the same harness green a hundred rounds in a row — and a second
experiment, `kill -9` between two writes that belong together.

**The thought process**

Use a barrier-controlled schedule for the naive read/compute/write version:
let both connections read 3, release both writers, and observe the final 4
instead of 5. A sleep may expose the race, but it does not establish ordering.
Test against the database and isolation level named by the exercise. A correct
post-hoc contract test remains useful; the deliberately broken version is an
additional sensitivity check.

Now the decision the folk cure skips: understanding why "wrap it in a
transaction" does not fix this. Under READ COMMITTED — the default — two
transactions can both read 3 and both write 4 without breaking any promise the
database made. Transactions promise atomicity: all of it or none of it. This
bug is about isolation: who sees what, when. It has a name — lost update — and
knowing the name is knowing which disease you are treating.

Then choose a fix by shape, and there are three honest ones. Send the
arithmetic to the database (`SET read_count = read_count + 1`) when the logic
fits in one statement. Lock the row (`SELECT ... FOR UPDATE`) when real logic
must happen between read and write. Or — the fix that dissolves this
particular case — notice that the `reads` table already holds the facts, and a
count derived from facts cannot lose an update. The cached counter was
denormalisation bought before anything was measured; the best concurrency fix
is often a design with nothing to race over.

The second experiment is the promise transactions do make: insert the
read-mark and bump the counter, kill the process between them, and count.
Without a transaction the two tables disagree, and no error anywhere says so.

**How to organise the prompts**

**1. The bug, made reliable.**

```
Use two database connections. In the naive version, gate both readers after
reading the same count, then release the writes. Assert the lost increment.
For the fixed version, start both operations together and assert both increments
commit. Do not wait for a second read while the first transaction holds the row lock.
```

Record the actual schedule. A test that never creates the intended overlap is
not evidence for this race; inspect the gates rather than increasing a sleep.

**2. The fix, twice, named.**

```
Keep the expected final count unchanged; adapt scheduling gates to avoid
deadlocking a correctly locked implementation. Fix it twice: once as a single atomic
UPDATE, once with SELECT ... FOR UPDATE. Name the anomaly, explain why
READ COMMITTED permits it, and say when each fix is the right one.
```

Both versions must preserve both increments. Review changed assertions separately
from necessary changes to test orchestration; never weaken the expected result.

**3. The other promise.**

```
Inserting the read-mark and updating the count belong together. Put a
sleep between them, kill -9 the process in the gap, restart, and show me
the two tables disagreeing. Then wrap the pair in one transaction and do
it again.
```

Before: a mark without a count, or a count without a mark. After: both or
neither, every time. Seeing the red version is the point.

**On AWS**

This is where **RDS Proxy** earns its explanation. Every concurrent Lambda
opens its own database connection, Postgres connections are whole processes,
and a burst of a few hundred invocations can flatten a small instance without
one query being slow. The proxy pools connections in front of the database —
a managed pgbouncer, with IAM auth and failover handling. When you do not need
it: one long-lived server with an in-process pool. Its caveat is worth the
word: session state — advisory locks, some settings — *pins* a connection to a
client and quietly turns the pooling off.

**DynamoDB** is the contrast worth thirty minutes: this exact counter bug does
not exist as written there, because an atomic ADD and conditional writes are
the native idiom — and its transactions mean something different from
Postgres's. "Transaction" is not one thing across engines; the promise you
lean on has to be the one your engine actually makes.

**What productionising it means**

The race harness joins the suite in a fast form — smaller sleep, more rounds —
because a refactor will reintroduce read-modify-write within the year and only
this test notices. If you chose stricter isolation anywhere, retries on
serialisation failures are now application code, not incident response. And
pool sizes are written down next to the instance size they were chosen for.

**The learning**

Transactions make grouped writes atomic; they do not stop two transactions
acting on the same stale read. Once you have watched a lost update happen on
demand, "just wrap it in a transaction" stops sounding like a fix and starts
sounding like a category error.

**How you would know it is wrong**

- The broken version must fail every round. Sometimes-red is not an instrument; widen the window until it is always-red.
- Prove the fix again with ten workers instead of two. Some fixes only narrowed the race.
- After the kill test with the transaction in place: both tables agree every time, including after a crash mid-run.
- Time two updates to different rows under the FOR UPDATE version. If they serialised anyway, you locked more than the bug required.

---

### 5. The data you can restore

*You end up with two numbers about your own system: minutes to restore, and
minutes of history a restore loses.*

**Build**

A backup script, a restore into a scratch database rebuilt from nothing each
run, a diff with a written definition of "same", and a log holding the two
numbers. P1's break-it table already asked whether you can restore a deleted
item; this is that row, done properly.

**The thought process**

The organising fact: a backup is a claim, a restore is the evidence. Backup
jobs fail silently in boring ways — an empty dump nobody opened, credentials
that rotated in March, a disk that filled — and every one looks like success
until the day it is needed. So the deliverable is the restore log, and the
backup script is merely its input.

Then define "restored correctly" before you diff, because a diff without a
definition always passes. Per-table row counts, a checksum per table, and one
human check — your own most recent item, present and intact. Decide the
scratch target too: a database dropped and re-created each run, because
restoring over a survivor can only hide what the backup is missing.

Then the two numbers, which have industry names you can now attach to
something real. How long the restore took: recovery time, RTO. How much
history the restore abandons — everything since the last backup: recovery
point, RPO. Nightly backups mean up to a day gone, and for a reading list that
may be fine; the skill is saying so in a file, before an incident decides for
you.

Last, where the backup lives. The same disk is not a backup; the same machine
barely is. And whatever encrypts it: a restore that needs a key must not keep
that key inside the thing being restored.

**How to organise the prompts**

**1. The pair of scripts.**

```
Write backup.sh — pg_dump, custom format, dated filename — and
restore_verify.sh: drop and re-create a scratch database, restore into
it, compare per-table row counts and per-table checksums against the
source, and print PASS or FAIL per table plus total restore time.
```

Run it against the untouched database first: all PASS, and a time. That time
is your first real number.

**2. The gap, measured.**

```
Delete one item and its read-marks, then restore into scratch. Show me
the deleted item back, and list exactly what the restore does not have:
every row written between the backup and now, per table, with times.
```

That list is your measured RPO — the gap turned into rows and minutes instead
of a feeling.

**3. The instrument test.**

```
Break the backup three ways — truncate the dump mid-file, back up the
wrong database, run it with the disk full — and show me what each looks
like when restore_verify.sh runs. All three must FAIL loudly.
```

A verifier that passes on a truncated dump is decoration. This step is what
turns the script into an instrument.

**On AWS**

The managed versions of these choices have names (all checked 2026-09-22).
**Automated backups** on RDS are a daily snapshot plus transaction logs
shipped about every five minutes, which is what buys **point-in-time
recovery** — restore to any second inside a retention window you set, one to
thirty-five days. **Manual snapshots** live until you delete them and can be
copied across regions and accounts — the answer to "what if the account itself
is compromised" — but restore only to their own moment. And the fact that
surprises everyone once: a restore never overwrites the instance; it creates a
new one, and repointing the application is your job — which is why the
rehearsal in this project is the same muscle, managed or not.

The dump-versus-snapshot distinction survives the move up: `pg_dump` is
logical — portable to a laptop, another version, another provider — and slow
at size; snapshots are physical — fast, exact, and bound to the engine. **AWS
Backup** centralises policy across many resources and is more machinery than
one database needs. Locally this whole project costs nothing, and locally is
where to run it.

**What productionising it means**

`restore_verify.sh` runs on a schedule and the two numbers are kept over time,
because a restore that took four minutes at 100,000 rows will not take four at
ten million, and the trend is the warning. The alarm is on the backup job
going *silent*, not only on it failing — a job that stopped looks exactly like
a job that is passing. And the runbook for the worst day is the script itself,
because 3am-you does not read prose.

**The learning**

Nobody needs backups; everybody needs restores. RTO and RPO stop being
interview vocabulary the day they are your own two numbers, measured on your
own system, with your own rows missing from the gap.

**How you would know it is wrong**

- Run `restore_verify.sh` on a machine that has never seen the source. A restore that only works next to its origin is a copy, not a recovery.
- The truncated dump must go red. If it passes, the verifier checks that a file exists, not that data survives.
- Stop the backup job for three days. If nothing notices, your real RPO is unbounded and the schedule is a wish.
- Compare the measured gap against the schedule's promise. "Nightly", with a log showing the last dump nine days old, is the commonest form of this failure.
