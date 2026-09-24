# Practice schema design, query plans, concurrent writes and restore

[Chapter](README.md)

A reading list stores shared bookmarks, their owners, optional tags, and each member’s read state. These exercises take one data responsibility at a time. The local reading-list starter supplies bookmarks and per-user read state. Tags, migrations, PostgreSQL adapters, and backup automation are work you add. Keep the teaching data separate from any real database.

## Choose your starting code

[Read the data-model lesson](data-models-and-queries.md) and [run the starter](../../../examples/reading-list-starter/README.md). Use the [PostgreSQL lab](labs/postgresql/README.md) when studying PostgreSQL plans or isolation. Do not assume its behavior is identical to SQLite.

![An index narrows the key range used by a query](../../../assets/learning/index-seek.svg)

<a id="1-the-schema-you-can-defend"></a>

## 1. Model shared bookmarks and per-person state

Ana and Ben share bookmark 42, but only Ana has read it. A single `bookmarks.is_read` field cannot represent both views.

**Your task.** Write the proposed tables, keys and foreign keys. Give each member/bookmark pair at most one read-state row. Define what happens when either referenced record is deleted. Add a tag relation only after defining tag identity and normalization.

**What to observe.** For bookmark 42, Ana reads `true` and Ben reads `false`. A second row for the same member/bookmark pair is refused or updates that pair according to your explicit contract.

**Changed requirement.** The list becomes shared by several groups. Add membership and decide which relationships enforce visibility without copying one user’s state to everyone.

[Worked mechanism and implementation context](data-models-and-queries.md)

<a id="2-the-migration-that-runs-both-ways"></a>

## 2. Migrate a shared flag into per-person records

An older version stored one read flag on each bookmark. There is no historical information identifying which members read it.

**Your task.** Choose and document a product policy for that missing history. Add the new relation, support mixed readers, backfill according to the policy, and move writers before retiring the old field. Never describe a guessed reconstruction as recovered data.

**What to observe.** Run an edit during backfill. The new value must survive the older snapshot. Record the exact point where rollback would require reverse capture or retained data.

**Changed requirement.** A mobile client keeps writing the old field for a month. Explain how the compatibility layer interprets those writes and when it can be removed.

[Worked mechanism and implementation context](../../04-scale-and-evolution/04-migrations/labs/recovery-migration/migration.md)

<a id="3-read-the-planner-not-the-code"></a>

## 3. Choose an index from a measured query plan

The group page lists recent bookmarks. One owner has 200 rows and another has 100,000. Their cheapest access paths may differ.

**Your task.** Use the PostgreSQL fixture to compare plans and returned values before and after a relevant index. Record row estimates, actual rows, buffers, and the query predicates. Explain which part of the index supports filtering and ordering.

**What to observe.** A faster plan must return the same owner-scoped rows in a stable order. Report observed times without demanding an invented speedup ratio.

**Changed requirement.** The application now searches a free-text substring. Explain why the recent-items index may not solve that access pattern and compare a separate search design.

[Worked mechanism and implementation context](labs/postgresql/README.md)

<a id="4-the-transaction-that-actually-holds"></a>

## 4. Protect a concurrent update at the write boundary

Two readers each fetch a counter value of 5 and both try to store 6. The final 6 hides one increment.

**Your task.** Drive a fixed interleaving using two sessions. Compare an atomic increment with an optimistic version check and retry. If two rows must change together, place both changes and their acceptance decision in the same transaction.

**What to observe.** Both logical increments produce 7, or a stated conflict makes one caller retry. Counting only successful SQL commands is not enough.

**Changed requirement.** The rule spans two rows, such as keeping one doctor on call. Work through the write-skew schedule instead of assuming a row-level repair solves it.

[Worked mechanism and implementation context](labs/postgresql/schedules.md)

<a id="5-the-data-you-can-restore"></a>

## 5. Restore data and measure the missing history

A deployment can be recreated from source, but bookmark rows cannot be recreated from application code. You need a separate recovery artifact.

**Your task.** Make a backup using the database’s supported mechanism. Restore into a new isolated database and compare IDs, values, relationships, and the newest included write. Record restore duration and the age of data missing from the backup.

**What to observe.** A row present at the backup boundary reappears correctly after restore. A later acknowledged write may be absent, and that loss is reported rather than hidden.

**Changed requirement.** The region containing the backup is unavailable. Decide what copy exists elsewhere and which application dependencies are also needed before the restored data can serve users.

[Worked mechanism and implementation context](../../03-production/01-system-design/problems/bookmark-service.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
