# Model shared data and enforce changes with database constraints

Alice and Bob use the same reading list. Both can see bookmark 7, but each has separate reading progress. Alice marking it read should not remove it from Bob's unread list. A single `is_read` field on the shared bookmark would represent the wrong fact.

You will model that fact, retrieve it with a query, and protect changes that arrive concurrently. Then you will inspect an index's effect on the query. Start with the meaning of a row before choosing database products or optimizing a screen.

## Give each fact a key

A key identifies the fact that one row represents. A bookmark ID identifies a shared item. Reading progress needs both a member and an item.

| Table | One row means | Key |
|---|---|---|
| `bookmarks` | This shared bookmark has this URL and title | Bookmark ID |
| `reading_state` | This member has this reading status for this bookmark | Member ID plus bookmark ID |
| `membership` | This member belongs to this group | Member ID plus group ID |

The [local reading-list API](../../../examples/reading-list-starter/README.md) implements bookmarks and per-member reading state. The membership table above illustrates an extension to real groups, not another table already supplied by that starter.

After Alice marks bookmark 7 read, the state can be:

| Member | Bookmark | Is read? |
|---|---:|---|
| Alice | 7 | True |
| Bob | 7 | False |

If no reading-state row exists, define whether that means unread. Missing data needs a declared meaning. Do not infer a person's past reading history from a shared flag that never recorded who acted.

## Use constraints to protect the model

This is an illustrative relational schema for the reading-state relationship. Adapt names and identity types to your application:

```sql
CREATE TABLE reading_state (
    member_id TEXT NOT NULL,
    bookmark_id INTEGER NOT NULL REFERENCES bookmarks(id),
    is_read BOOLEAN NOT NULL,
    PRIMARY KEY (member_id, bookmark_id)
);
```

The composite primary key prevents two rows describing the same member/bookmark pair. The foreign key requires the referenced bookmark to exist under the chosen database configuration. Membership and operation authorization still need enforcement. A foreign key does not decide whether Bob is allowed to act as Alice.

**Normalization** gives a fact one authoritative representation. Store a group's name on the group row rather than copying it into every bookmark. A deliberately copied count or search view is **denormalized** data. It can be useful, but it needs an update and repair rule.

## Read shared items with the current member's status

A left join keeps bookmarks even when the member has no status row:

```sql
SELECT b.id, b.title, COALESCE(r.is_read, FALSE) AS is_read
FROM bookmarks AS b
LEFT JOIN reading_state AS r
  ON r.bookmark_id = b.id
 AND r.member_id = :authenticated_member
ORDER BY b.created_at DESC, b.id DESC
LIMIT 20;
```

This teaching query omits group filtering to focus on the join. A multi-group application must also restrict bookmarks to verified membership. The placeholder is a bound driver parameter derived from trusted identity.

Putting the member filter inside the join condition preserves bookmarks with no matching status. Moving it carelessly into a `WHERE` clause can remove those rows and change the query's meaning. `COALESCE` applies the declared missing-row policy here. It should not hide an unavailable database or an unknown business value.

The `(created_at, id)` order uses ID to break timestamp ties. A cursor must retain both values to continue deterministically. It also needs a documented policy for concurrent edits and deletions.

## An index serves a particular access pattern

Suppose the real query is “list one owner's newest twenty bookmarks.” A candidate index is `(owner_id, created_at, id)` in an ordering appropriate to that query. Its value depends on filters, data distribution and the database's plan.

![A matching index narrows a read, while maintaining indexes adds work and storage to writes.](../../../assets/diagrams/index-cost.svg)

| Query characteristic | What to inspect |
|---|---|
| One owner out of many | How many rows survive the owner predicate |
| Newest twenty rows | Whether the index supplies useful ordering and early stopping |
| Many rows share a timestamp | Stable ID tie-breaker |
| Frequent updates | Added write and storage cost of the proposed index |

An index is not a guarantee that every query becomes fast. In PostgreSQL, a B-tree stores ordered keys separately from heap row versions. Choosing ordered IDs does not keep all heap rows physically sorted forever. Other index families serve different operators and access patterns.

Use the [PostgreSQL lab](labs/postgresql/README.md) for schema, sample data and actual query plans. Compare estimated and observed row counts, scans, sorting and buffer activity under representative data. A tiny table may reasonably use a sequential scan.

## Atomic changes and concurrent decisions are different concerns

A transaction can store related changes together or roll them back together. The transaction's isolation and write rules determine what concurrent callers may observe and change.

Two buyers both see one remaining unit. If both independently decide it is available and then write zero, each may think it succeeded. A conditional decrement makes the availability decision part of the write:

```sql
UPDATE stock
SET available = available - 1
WHERE product_id = :product_id
  AND available > 0;
```

Check the affected-row count. One means this decrement succeeded. Zero means no unit was claimed by that operation. If order creation must succeed with the decrement, place both in the same appropriate transaction. For more complex invariants, use the required locking or isolation protocol and handle retries.

| Concurrent action | Expected observation |
|---|---|
| Buyer A claims the final unit | One affected stock row |
| Buyer B also tries | Zero affected rows after A's committed claim |
| A's order insertion fails in the same transaction | Its stock decrement is rolled back |

The [two-session worksheet](labs/postgresql/schedules.md) makes the interleaving observable. Read the actual SQL and transaction boundaries rather than treating the word transaction as the entire proof.

## Make units, absence and time explicit

| Data | Representation decision |
|---|---|
| Money | Currency plus integer minor units or an appropriate decimal representation |
| An instant | A timezone-aware instant, with display conversion at the edge |
| A recurring local appointment | Local time and named timezone, plus daylight-saving policy |
| Unknown or not-yet value | Nullable only with a defined meaning |
| Stable object identity | An identifier that survives changes to display name or email |

USD 1999 minor units means USD 19.99 under that currency convention. JPY 500 is a different unit, so adding the integers without a conversion policy is meaningless. Likewise, storing a UTC instant alone does not fully describe “9 a.m. every Monday in London.”

A natural key comes from the domain, such as an email address. A surrogate key is an assigned identity. Use a separate uniqueness constraint where a domain value must remain unique, while allowing the stable internal identity to survive a legitimate value change.

## Change the model without inventing history

If the old schema used a shared read flag, adding a per-member table cannot reconstruct which person actually read each item. State that gap and choose an explicit migration policy, such as unknown historical status or a documented reset. Do not silently assign the shared value to everyone.

For a compatible schema change, add the new representation, copy recoverable data, keep live changes synchronized, reconcile and switch consumers before retiring the old path. The [migration lesson](../../04-scale-and-evolution/04-migrations/migration-method.md) follows newer writes and deletions arriving during the copy.

Your first deliverable is small: two members, one bookmark, two independent reading states and a query that returns the correct view for each. Then inspect one measured query plan and demonstrate one concurrent invariant. Those examples establish what your schema and index are actually doing.
