# 13 · Data at scale

> Senior tier · feeds **P3 (it holds under load)**

## The one-liner

Load does not kill systems by filling the disk. It kills them at the connection
pool, in the shape of one query, under read pressure, and during the failover
nobody rehearsed. Every fix buys headroom and bills a new failure class, so the
skill is not "make it scale" — it is knowing the price list and climbing in the
cheap, reversible order.

## The failure it prevents

The reading list is humming: eighty thousand items, a few hundred users, the
group page cached with a sixty-second TTL because someone measured the query at
400ms and did the sensible thing.

Then a newsletter links to it. Traffic rises 40x, and for fifty-nine seconds
nothing happens, because the page is one cache hit. Then the key expires. Two
hundred requests miss at the same moment, and each one independently runs the
400ms query to repopulate the cache. The database gets two hundred copies of
its most expensive query at once. Its hundred connection slots — the PostgreSQL
default, which nobody chose — fill instantly. Now sign-in fails too, because
sign-in needs a connection and there are none.

The on-call restarts the app servers. That drops every warm key at once, and
the database meets the full read load cold.

None of this was volume; eighty thousand rows is nothing. The cache — added as
a performance fix — converted one slow query into a full outage, because a
cache without stampede protection is exactly that machine.

## The mental model

**What load hits first.** Four things, and raw volume is none of them.
*Connections*: a database connection is scarce and stateful — PostgreSQL's
default ceiling is typically 100 (checked 2026-09-21) — and every feature
competes for the same pool, which is why one busy page can take down sign-in.
The first purchase under load is rarely hardware; it is a pooler (PgBouncer is
the usual PostgreSQL example) and a written answer for what happens when the
pool is full. *Query shape*:
[the junior tier](../../01-junior/05-data-and-databases/) taught that a scan
grows with the table; concurrency is worse, because two hundred copies of one
slow query fight for the same pages, locks and pool slots. *Read pressure*:
most products read far more than they write, so reads saturate first — three of
the four rungs below are about reads. *Failover*: P1 taught that a dependency
being down is normal; at scale the database is the dependency, and the seconds
where nobody is primary are designed and rehearsed, not caught.

**The ladder, and what each rung bills.**

![The escalation ladder for data under load: index, then cache, then replicas, then shard last. Each rung buys headroom — fast reads, read headroom, read scale, write headroom — and bills a new failure class: write cost on every insert, staleness and stampedes, replication lag and failover itself, routing and rebalancing with no cross-shard transactions.](../../../assets/diagrams/scaling-order.svg)

Climb on a measured number, one rung at a time; each rung is cheaper and more
reversible than the one above.

1. **Index** — buys fast reads on one query shape. The bill — every write pays —
   was priced in the junior data section. Exhaust this rung first; it is the
   only one that adds no moving part.
2. **Cache** — buys read headroom by answering from a copy, and bills two
   failure classes. *Invalidation*: the copy can disagree with the truth, and
   enumerating every write that must refresh it is now your job. *The
   stampede*: when a hot key expires, every concurrent reader misses at once
   and recomputes — the story above. The protections are standard; name yours:
   a **single-flight lock** (one request recomputes, the rest wait or take the
   old value), **stale-while-revalidate** (serve the expired value, refresh in
   the background — old enough to be in HTTP itself: RFC 5861, 2010, checked
   2026-09-21), **TTL jitter** (randomised expiry, so keys born together do not
   expire together), **probabilistic early refresh** (each hit has a small
   chance, rising near expiry, of refreshing early). A cache with none of these
   is an outage on a timer.
3. **Replicas** — buy read scale and a standby. The bill is **staleness**:
   replication is asynchronous unless you pay for it not to be, so a replica is
   always a little behind, and under load "a little" has no upper bound.
   Failover is itself a new event that can fail: promote an async replica, and
   writes the old primary acknowledged but never shipped are gone.
4. **Shard** — splits the data across databases by a key; the only rung that
   buys **write** headroom. The bill is the largest: every query must know
   where to look (routing), growth means moving live data (rebalancing), and
   cross-shard transactions and joins stop being the database's job. PostgreSQL
   has no native sharding; it is an extension or your problem. Shard last — it
   is the one rung with no ladder down.

**Queues.** A queue buys two things: it absorbs bursts, letting arrivals exceed
processing for a while, and it decouples failure — the fetcher being down stops
fetching, not adding. It bills three: global ordering is gone, and per-key
order survives only if you arrange it; delivery becomes **at-least-once**,
because a consumer that crashes after doing the work but before acknowledging
it gets the same message again; and the backlog is invisible unless you
instrument it — the product looks healthy while work quietly ages.

**Delivery semantics, said once.** Exactly-once does not survive a system
boundary. Kafka — 4.0, released March 2025, the first major release to run
entirely without ZooKeeper (checked 2026-09-21) — can make read-process-write
exactly-once while everything stays inside Kafka; the moment your consumer
writes to PostgreSQL or sends an email, the crash-retry gap reopens, and no
broker setting closes it. The practice is at-least-once plus **idempotent
consumers**: give every message a key, put a unique constraint on it where the
effect lands, and let the database refuse the second delivery. On the producing
side, the **outbox pattern** closes the mirror-image gap: the business row and
the outgoing message are written in one transaction, and a relay publishes from
the outbox table, so "saved but never announced" cannot happen.

**Backpressure.** A queue with no bound is a memory leak with a scheduler: let
arrivals exceed service rate long enough and it eats memory or disk, then fails
at the worst moment, having hidden the problem until then. Every buffer needs a
bound and a policy for full — block the producer, shed the work, or degrade the
feature. Not choosing is choosing "crash later".

**What "eventually" costs.** Eventual consistency is a claim that the system
converges. The user who pressed save lives in the meantime: their write went to
the primary, their next read hit a replica that has not seen it, and the edit
is gone from the screen. So they save again — now there are two — or they stop
trusting the product. If reads go to replicas, **read-your-writes** is the
floor: route a user's reads to the primary for a window after they write, or
pin their session. It is cheap. The user's trust is not.

## What good looks like

- A pooler in front of the database, with a chosen size and a written answer
  for pool-full: wait how long, then fail how.
- Every cache key has a written invalidation story and a named stampede
  protection, and a test exists that expires a hot key under concurrency.
- Reads that must see the user's own write have a stated route to data that
  has it.
- Every queue and buffer has a bound and a full-policy, and the dashboard shows
  backlog **age**, not just length.
- Consumers are idempotent, proven by a test that delivers the same message
  twice.
- Each rung was climbed on a measurement, recorded next to the change.
- Failover has been rehearsed, and you can say what happens to writes in
  flight.

Done badly, you see:

- Round-number TTLs expiring together, and a deploy that clears every cache at
  once while the database finds out.
- A replica "for performance" while every read still goes to the primary — or
  reads on replicas and nobody has heard of lag.
- "Exactly-once delivery" written in a design document.
- A backlog discovered over ssh, during the incident.
- Sharding proposed in the first design review, before anyone has read a query
  plan.

## Ask Claude for this

**Request 1 — find the saturating resource before touching anything**

```
Under load, the group page slows down and sign-in starts failing too.

Do not propose a fix yet. First list what you would measure to find
which resource saturates first — connection pool, one query's plan,
locks, CPU, cache misses — and for each, the exact query or command
and what a bad number looks like.

Here is the data: [pool stats, EXPLAIN ANALYZE of the page query,
error rates]. Name the bottleneck. Then name the cheapest rung that
addresses it — index, cache, replica, shard — and say why each rung
below your choice is not enough.
```

*Why it is asked that way:* "do not propose a fix yet" does the work — a
model's reflex is to reach for a cache or a bigger instance before knowing what
is full. Arguing why the lower rungs are not enough enforces the escalation
order instead of the impressive answer.

*What you should get back:* the observation that sign-in failing alongside one
slow page points at a shared resource — almost always connections — not at the
page's own query. If the first suggestion is "add Redis" with no plan read, the
measuring step was skipped.

*Push back on:* replicas, shards or a queue anywhere in the first answer.
Nothing in the data has justified rung two yet.

**Request 2 — a cache that fails the way you chose**

```
Add caching for the group page. Requirements:

1. The invalidation story, written: every write path that must touch
   this key, enumerated. If they cannot all be enumerated, say so and
   fall back to a TTL, with its staleness cost stated.
2. Stampede protection: when a hot key expires under 200 concurrent
   readers, at most one recomputes. Name the mechanism you chose —
   single-flight lock, stale-while-revalidate, TTL jitter,
   probabilistic early refresh — and why. Then write the test: expire
   the key under concurrent load and count queries at the database.
3. Tell me what a user sees when the cache backend is down. The only
   acceptable answer is "the same page, slower."
```

*Why:* naming the four mechanisms stops the model from writing
get-set-with-a-TTL and calling it caching, and requirement 3 stops the cache
becoming load-bearing, which is how a performance fix turns into a new single
point of failure.

*What you should get back:* code plus a test whose assertion is a count of
database hits, not a latency. The count is the check that can go red.

*Push back on:* a recompute path with no guard, and any design where
cache-down means page-down.

**Request 3 — a consumer that survives what queues actually do**

```
Move the link-fetch onto the queue. Write the consumer, assuming
every message can arrive twice and out of order, because
at-least-once means it eventually will.

Design the idempotency: what is the message key, where is it stored,
and which database constraint turns a second delivery into a no-op
instead of a duplicate row? In-memory dedup does not count; the
process that remembers is the process that crashes.

State what bounds the queue and what the producer does when it is
full: block, shed, or degrade. "It will not fill" is not an answer.

Tests: deliver one message twice and assert the effect happened once.
Kill the consumer after the write but before the acknowledgement and
assert the message is redelivered.
```

*Why:* "because at-least-once means it eventually will" turns duplicates from
an edge case into a premise, and models build differently from premises.
Putting the dedup in a database constraint, stated in the ask, closes the
version that most often survives review.

*What you should get back:* a consumer whose second delivery dies on a unique
constraint and moves on, an explicit bound, and both tests. If "exactly-once"
comes back as a client-library setting that solves it all, that is the boundary
error this section exists to remove.

## How you would know it is wrong

Each of these can go red, and each is cheap:

1. **Expire the hot key under load.** Hold 200 concurrent requests on the
   cached page, delete the key mid-run, and count queries at the database
   (`pg_stat_statements`, or a counter in the recompute path). One recompute is
   a pass. Two hundred is the failure story, rehearsed for free.
2. **Kill the consumer for ten minutes** under normal write load. Adding items
   must keep working, the backlog must be visible on a graph that existed
   before the test, and after restart you can say how long the drain took. If
   you learned the backlog size over ssh, "invisible" was the finding.
3. **Deliver the same message twice** and count the rows: the effect happened
   once, or it did not. Then the harder version: crash the consumer after its
   write but before its acknowledgement, let redelivery happen, count again.
4. **Write, then immediately read through the replica path**, in a loop, under
   load. The fraction of reads that miss the write is your staleness exposure.
   "We have never seen it" usually decodes to "we have never measured it."
5. **Fill the pool on purpose** — hold idle transactions open until it is
   exhausted — and watch the rest of the product. This is how you learn sign-in
   shares a fate with the busiest page, before a newsletter teaches you.
6. **Pull the primary in staging** and time the failover, then compare
   acknowledged writes before against rows present after. A difference is not
   a bug in the test; it is what asynchronous replication promised all along.

> The standing rule applies: before believing a green result, say what broken
> would have looked like. A stampede test that never actually expires the key
> under concurrency passes forever and proves nothing.

## Your slice of the project

On **P3**, the reading list meets load on purpose:

- A load harness — any tool that can hold N concurrent requests — and a written
  baseline: p50 and p99 for the group page at rest and at N, before you change
  anything.
- A pooler in front of PostgreSQL with a chosen size, and one sentence on what
  happens at exhaustion.
- The group page cached, with a named stampede protection and the
  expire-under-load test checked in, asserting on the database-hit count.
- The link-fetch on a bounded queue: full-policy stated, consumer idempotent,
  backlog age on a graph.
- An escalation record: each rung you climbed and the measurement that
  justified it.

**Acceptance criteria you can check yourself:**

- Disable the stampede protection and the expire-under-load test goes red with
  a hit count near your concurrency; enable it and the count returns to one.
- Ten minutes of dead consumer causes no user-visible failure to add items, and
  the drain time comes from a graph, not a guess.
- Drop the consumer's unique constraint on a copy and the deliver-twice test
  goes red.
- Shard appears nowhere in the escalation record, and you can say what number
  would have to be true before it did.

## Words you now own

- **connection pool** — the fixed set of database connections the whole product
  shares; the first resource load exhausts.
- **cache stampede** — every reader missing at once when a hot key expires,
  then recomputing in parallel. Also called thundering herd.
- **single-flight** — a lock so one request recomputes an expired value while
  the rest wait or take the stale one.
- **stale-while-revalidate** — serve the expired value now, refresh it in the
  background.
- **replication lag** — how far a replica is behind the primary. Unbounded
  under load, unless you watch it.
- **read-your-writes** — the guarantee that a user's reads see their own
  writes; the floor for reading from replicas.
- **failover** — promoting a replica when the primary dies. An event with its
  own failure modes, not a checkbox.
- **shard** — one slice of the data, split by a key so writes spread across
  databases. Buys writes, bills routing and rebalancing.
- **at-least-once** — deliveries can repeat, so the consumer must make repeats
  harmless.
- **idempotent consumer** — processing with the same effect once or twice,
  usually via a unique key the database enforces.
- **outbox pattern** — the business write and the outgoing message committed in
  one transaction, published afterwards by a relay.
- **backpressure** — pushing "slow down" upstream when a stage is full: block,
  shed or degrade, chosen rather than defaulted.

---

**Not covered here:** isolation levels and locking — what two transactions
touching the same rows do to each other; choosing a non-relational engine when
the data stops being row-shaped; search and analytics; and distributed
transactions beyond the outbox — sagas belong with the staff-tier migration
work. Timeouts, retries, load shedding and backups you have actually restored
live in [09 · Reliability](../09-reliability/); this section leans on them.
