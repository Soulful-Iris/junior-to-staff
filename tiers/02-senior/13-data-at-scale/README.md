# 13 · Data at scale

> Senior tier · feeds **P3 (it holds under load)**

## The one-liner

Load does not kill systems by filling the disk. It kills them at the connection
pool, in the shape of one query, under read pressure, and during the failover
nobody rehearsed. Every fix buys headroom and bills a new failure class, so the
skill is knowing the price list and climbing in the cheap, reversible order.

## The failure it prevents

The reading list is humming: eighty thousand items, a few hundred users, the
group page cached with a sixty-second TTL because someone measured the query at
400ms and did the sensible thing.

Then a newsletter links to it. Traffic rises 40x and for fifty-nine seconds
nothing happens: the page is one cache hit. Then the key expires. Two hundred
requests miss at once, and each independently runs the 400ms query to
repopulate it. The database gets two hundred copies of its most expensive
query. Its hundred connection slots — the PostgreSQL default, which nobody
chose — fill instantly. Now sign-in fails too, because sign-in needs a
connection too. The on-call restarts the app servers — dropping
every warm key onto a cold database.

None of this was volume; eighty thousand rows is nothing. The cache — added as
a performance fix — converted one slow query into a full outage, because a
cache without stampede protection is exactly that machine.

## The mental model

**What load hits first.** Four things, and raw volume is none of them.
*Connections*: a database connection is scarce and stateful — PostgreSQL's
default ceiling is typically 100 (checked 2026-09-21) — and every feature
competes for the same pool. The first purchase is rarely hardware: a pooler
(PgBouncer, say) and a pool-full decision. *Query shape*:
[the junior tier](../../01-junior/05-data-and-databases/) taught that a scan
grows with the table; concurrency is worse: two hundred copies of one slow
query fight for the same pages, locks and pool slots. *Read pressure*: most
products read far more than they write, so reads saturate first. *Failover*: at
scale the database is the dependency that dies; the seconds where nobody is
primary are designed, not caught.

**The ladder, and what each rung bills.**

![The escalation ladder — index, cache, replicas, shard last — each rung labelled with what it buys and the new failure class it bills.](../../../assets/diagrams/scaling-order.svg)

Climb on a measured number; every rung above is dearer and harder to reverse.

1. **Index** — buys fast reads on one query shape; the bill — every write pays —
   was priced in the junior data section. Exhaust it first; it adds no moving
   part.
2. **Cache** — buys read headroom from a copy, and bills two failure classes.
   *Invalidation*: the copy can disagree with the truth, and enumerating every
   write that must refresh it is now your job. *The stampede*: when a hot key
   expires, every concurrent reader misses at once and recomputes. The
   protections are standard: a **single-flight lock** (one recompute; the rest
   wait or take stale), **stale-while-revalidate** (serve stale now, refresh
   behind — in HTTP itself since RFC 5861, 2010; checked 2026-09-21), **TTL
   jitter** (randomised expiry, so keys born together do not die together),
   **probabilistic early refresh** (a chance of refreshing early, rising near
   expiry). A cache with none of these is an outage on a timer.
3. **Replicas** — buy read scale and a standby. The bill is **staleness**:
   replication is asynchronous by default, so a replica is always a little
   behind, and under load "a little" has no bound. Failover is itself an event
   that can fail: promote an async replica, and writes the old primary
   acknowledged but never shipped are gone.
4. **Shard** — splits data across databases by a key; the only rung that buys
   **write** headroom. The bill: every query must know where to look (routing),
   growth means moving live data (rebalancing), and cross-shard transactions
   and joins stop being the database's job. PostgreSQL has no native sharding —
   an extension or your problem. Shard last: it is the one rung with no ladder
   down.

**Queues.** A queue buys two things: it absorbs bursts, and it decouples
failure — the fetcher being down stops fetching, not adding. It bills three:
ordering (only per-key order survives, and only arranged); delivery
becomes **at-least-once**, because a consumer that crashes between the work and
the acknowledgement gets the message again; and the backlog is invisible until
you instrument it — the product looks healthy while work quietly ages.

**Delivery semantics.** Exactly-once claims have a scope and a failure model.
Kafka transactions can coordinate consumed offsets with produced Kafka records.
An external database write or email does not automatically join that transaction.
After an external effect succeeds but before acknowledgement, a crash can cause
redelivery. Coordinate the effect and deduplication record atomically where
possible; otherwise use a destination-supported idempotency key or reconcile
uncertain outcomes. An outbox commits a business row and outgoing event together,
then relays the event. The relay may still publish duplicates, so consumers
still need deduplication. See [Kafka's design documentation](https://kafka.apache.org/41/design/design/)
for the transaction-boundary discussion.

**Backpressure.** A queue with no bound is a memory leak with a scheduler: when
arrivals outrun service long enough, it eats memory or disk and fails at
the worst moment. Every buffer needs a bound and a policy for full — block,
shed, or degrade. Not choosing is choosing "crash later".

**What "eventually" costs.** "Eventually consistent" is a claim about the
system converging. The user who pressed save lives in the meantime: the write
went to the primary, the next read hit a replica that has not seen it, and the
edit is gone from the screen. So they save again — now there are two — or stop
trusting the product. With replica reads, **read-your-writes** is the floor:
route a user's reads to the primary for a window after they write, or pin
their session.


![Cache requests without and with shared loading](../../../assets/learning/cache-coalescing.svg)


## What good looks like

- A pooler with a chosen size and a written pool-full answer: wait how long,
  then fail how.
- Every cache key has a written invalidation story and a named stampede
  protection, tested by expiring a hot key under concurrency.
- Reads that must see a user's own write have a stated route to it.
- Every queue and buffer has a bound and a full-policy; dashboards show backlog
  **age**, not length.
- Consumers are idempotent, proven by a test that delivers the same message
  twice.
- Each rung climbed on a measurement, recorded next to the change.
- Failover has been rehearsed, and writes in flight have a known fate.

Done badly, you see:

- Round-number TTLs expiring together; a deploy that clears every cache while
  the database finds out.
- A replica "for performance" while every read still hits the primary — or
  reads on replicas and nobody has heard of lag.
- "Exactly-once delivery" written in a design document.
- A backlog discovered over ssh, during the incident.
- Sharding proposed in the first design review, before anyone read a plan.

## Ask Claude for this

**Request 1 — find the saturating resource before touching anything**

```
Under load, the group page slows down and sign-in starts failing too.

Do not propose a fix yet. List what you would measure to find which
resource saturates first — connections, one query's plan, locks, CPU,
cache misses — and for each, the command and what a bad number looks
like.

Then, given [pool stats, EXPLAIN ANALYZE, error rates]: name the
bottleneck, the cheapest rung that addresses it — index, cache,
replica, shard — and why each rung below is not enough.
```

*Why it is asked that way:* "do not propose a fix yet" does the work — a
model's reflex is a cache or a bigger instance before knowing what is full.
Arguing why the lower rungs are not enough enforces the escalation order.

*What you should get back:* that sign-in failing beside one slow page points at
a shared resource — almost always connections. If the first suggestion is "add
Redis" with no plan read, measuring was skipped.

*Push back on:* replicas, shards or a queue anywhere in the first answer.
Nothing measured has justified rung two yet.

**Request 2 — a cache that fails the way you chose**

```
Add caching for the group page. Requirements:

1. The invalidation story: every write path that must touch this key,
   enumerated. If you cannot enumerate them, say so and fall back to a
   TTL with a stated staleness cost.
2. Stampede protection: when a hot key expires under 200 concurrent
   readers, at most one recomputes. Name the mechanism you chose —
   single-flight lock, stale-while-revalidate, TTL jitter,
   probabilistic early refresh — and why, then write the test: expire
   the key under concurrent load and count queries at the database.
3. Tell me what a user sees when the cache backend is down. The only
   acceptable answer is "the same page, slower."
```

*Why:* naming the four mechanisms stops get-set-with-a-TTL being sold as
caching, and requirement 3 stops the cache becoming load-bearing — a
performance fix turned single point of failure.

*What you should get back:* code plus a test asserting a count of database
hits, not a latency. The count is the check that can go red.

*Push back on:* a recompute path with no guard, and any design where
cache-down means page-down.

**Request 3 — a consumer that survives what queues actually do**

```
Move the link-fetch onto the queue. Write the consumer, assuming every
message can arrive twice and out of order, because at-least-once means
it eventually will.

Design the idempotency: what is the message key, where is it stored,
and which database constraint turns a second delivery into a no-op?
In-memory dedup does not count; the process that remembers is the
process that crashes.

State what bounds the queue and what the producer does when it is
full: block, shed, or degrade. "It will not fill" is not an answer.

Tests: deliver one message twice and assert the effect happened once.
Kill the consumer after the write but before the acknowledgement and
assert the message is redelivered.
```

*Why:* "because at-least-once means it eventually will" turns duplicates from
an edge case into a premise, and models build differently from premises.
Demanding the dedup live in a database constraint closes the version that
survives review most often.

*What you should get back:* a consumer whose second delivery dies on a unique
constraint, an explicit bound, and both tests. "Exactly-once" as a
client-library setting is the boundary error this section removes.

## How you would know it is wrong

Each of these can go red, cheaply:

1. **Expire the hot key under load.** Hold 200 concurrent requests on the page,
   delete the key mid-run, and count queries at the database
   (`pg_stat_statements`, or a counter in the recompute path). One recompute is
   a pass. Two hundred is the failure story, rehearsed.
2. **Kill the consumer for ten minutes** under write load. Adding items must
   keep working, the backlog must be visible on a graph that existed before the
   test, and you can time the drain after restart. If you learned
   the backlog size over ssh, "invisible" was the finding.
3. **Deliver the same message twice** and count the rows: the effect happened
   once, or it did not. Then harder: crash the consumer after its write but
   before its acknowledgement, let redelivery happen, count again.
4. **Pull the primary in staging** and time the failover, then compare
   acknowledged writes before against rows present after. A difference is not a
   test bug; it is what async replication promised.

> The standing rule: before believing a green result, say what broken would
> have looked like. A stampede test that never actually expires the key under
> concurrency passes forever and proves nothing.

## Your slice of the project

On **P3**, the reading list meets load on purpose:

- A load harness — anything that can hold N concurrent requests — and a written
  baseline: p50 and p99 for the group page at rest and at N.
- A pooler with a chosen size, and a sentence on what happens at exhaustion.
- The group page cached, stampede protection named, and the expire-under-load
  test checked in, asserting on database hits.
- The link-fetch on a bounded queue: full-policy stated, consumer idempotent,
  backlog age on a graph.
- An escalation record: each rung climbed and the measurement behind it.

**Acceptance criteria you can check yourself:**

- Disable the stampede protection and the expire-under-load test goes red with
  a hit count near your concurrency; enable it and the count returns to one.
- Ten minutes of dead consumer: adding items still works, and the drain time
  comes from a graph, not a guess.
- Drop the consumer's unique constraint on a copy and the deliver-twice test
  goes red.
- Shard appears nowhere in the record, and you can say what number would have
  to be true first.

## Words you now own

- **connection pool** — the fixed set of connections the whole product shares;
  the first thing load exhausts.
- **cache stampede** — every reader missing at once when a hot key expires,
  recomputing in parallel; also thundering herd.
- **single-flight** — one request recomputes an expired value; the rest wait or
  take stale.
- **stale-while-revalidate** — serve the expired value now, refresh it in the
  background.
- **replication lag** — how far a replica runs behind the primary; unbounded
  under load unless watched.
- **read-your-writes** — a user's reads see their own writes; the floor for
  reading from replicas.
- **shard** — one slice of the data, split by key so writes spread. Buys
  writes, bills routing and rebalancing.
- **at-least-once** — deliveries can repeat, so the consumer must make repeats
  harmless.
- **idempotent consumer** — processing with the same effect once or twice,
  usually via a unique key the database enforces.
- **outbox pattern** — business write and outgoing message committed together,
  published afterwards by a relay.
- **backpressure** — pushing "slow down" upstream when a stage is full: block,
  shed or degrade, chosen rather than defaulted.

---

**Not covered here:** isolation levels and locking (two transactions on the
same rows); choosing a non-relational engine when the data stops being
row-shaped; search and analytics; and distributed transactions beyond the
outbox — sagas sit with the staff-tier migration work. Timeouts, retries, load
shedding and backups you have actually restored live in
[09 · Reliability](../09-reliability/).

[Choose your learning path](../../../paths/README.md) · [Interview applications](../../../paths/interviews/README.md)
