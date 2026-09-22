# 29 · Expiring key-value store

> “A single-process service caches temporary verification results. Each write has
> a time to live. Reads must never return an expired result, including at the exact
> expiry instant. Tests must run instantly and deterministically. How would you
> make time an explicit dependency?”

Constructed practice question. Prerequisites: [maps](../../lessons/01-maps.md) and
[LRU contracts](../../lessons/10-lru.md). TTL is a duration; a deadline is the clock
reading at write plus TTL. A monotonic clock advances without wall-clock corrections.

| Contract | Required behavior |
|---|---|
| Input | Hashable key, arbitrary value, finite nonnegative TTL; injected monotonic clock |
| Output | `get` returns live value or raises `KeyError`; delete reports live removal |
| Expiration | Live exactly while `now < deadline`; TTL=0 immediately removes key |
| Cleanup | `purge()` removes all entries expired at one sampled instant and returns count |
| Failure/scope | Invalid TTL raises `ValueError` without overwriting; no persistence/concurrency |

At clock 100, `set(a,'ok',5)` yields `'ok'` at 104.999 and `KeyError` at 105.
Overwrite a at 103 with TTL 10 and it remains live at 105 until deadline 113.
Storing `None` remains distinguishable from absence. Clarify whether reads extend
expiry (they do not) and whether deletion of an expired key returns true (false).

```mermaid
stateDiagram-v2
  [*] --> Absent
  Absent --> Live: set at 100 with TTL 5
  Live --> Live: get at 104.999 returns value
  Live --> Expired: clock reaches 105
  Expired --> Absent: get or purge removes storage
```

Implement without sleeping. Write the exact-boundary test before deciding whether
to use `<` or `<=` in the liveness check.

<details>
<summary>Solution, logical expiry, and follow-ups</summary>

One timer per key is an attractive baseline but creates scheduling/resource costs,
and a timer callback may run after the deadline. A read that trusts “the timer has
not fired yet” can return stale data. Periodically deleting expired keys also cannot
replace checking expiry on the read path.

Store `(value,deadline)` in a dictionary. A get samples the injected clock and
checks `now >= deadline`; if true, remove that entry and raise `KeyError`.
An overwrite replaces both value and deadline. `purge` samples once, collects
expired keys, and deletes them after iteration to avoid modifying the dictionary
during traversal. TTL validation happens before changing existing state.

**Invariant:** a successful get returns only a value whose stored deadline is
strictly greater than that operation's clock sample. Logical absence at expiry
does not require physical deletion at that instant. This separation permits lazy
cleanup while preserving read correctness. It does *not* bound retained memory:
expired keys never accessed again remain until purge.

| Clock | Action | Stored deadline | Visible result |
|---:|---|---:|---|
| 100 | set a, TTL 5 | 105 | live |
| 103 | overwrite a, TTL 10 | 113 | new value |
| 105 | get a | 113 | new value survives old deadline |
| 113 | get a | removed | missing |

Get/set/delete cost expected O(1) time and O(1) auxiliary space. N stored entries
use O(N) state, counting expired entries awaiting cleanup. Purge costs O(N) time
and O(X) temporary keys for X expired entries. These are process-local operations;
clock advancement and caller scheduling are outside the data-structure cost.

**Follow-up 1 — background heap cleanup.** Predict the danger of an old expiry
record after overwrite. A heap item must carry a generation or match the current
deadline; otherwise the old timer deletes a newer value. Stale heap entries also
need a compaction policy to keep memory proportional to current keys.

```mermaid
sequenceDiagram
  participant W as Writer
  participant S as Store
  participant C as Cleaner
  W->>S: a generation 1 expires 105
  W->>S: a generation 2 expires 113
  C->>S: expire generation 1 at 105
  S-->>C: ignore, current generation is 2
```

**Follow-up 2 — persist across restarts.** A process monotonic deadline cannot be
serialized as a portable wall-clock expiry. Choose a persisted timestamp and
clock-skew policy, or expire everything on restart. Multiple replicas additionally
need a defined authority for writes and expiry decisions.

Senior depth tests equality, overwrite-before-expiry, invalid-write atomicity, and
cleanup with a fake clock. Lead depth explains retention and time authority rather
than promising that local TTL implies a distributed revocation guarantee.

Reference: [solution.py](solution.py); [test_solution.py](test_solution.py) supplies
the fake clock and never uses timing sleeps.

```bash
python -m unittest discover -s paths/interviews/coding/problems/29-expiring-key-value-store -p 'test_*.py'
```

</details>
