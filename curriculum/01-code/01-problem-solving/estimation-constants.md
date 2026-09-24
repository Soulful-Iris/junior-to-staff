# Estimate request rates, storage, latency and availability

[Curriculum](../../README.md) · [Specify, implement and review changes with AI](README.md)

> Project connection · feeds [Reading-list stage 3: measure the application under load](../../../projects/reading-list/stages/03-under-load/README.md)

## Start with the user action and the unit

A bookmark service stores a URL each time a member presses Save and reads several rows when a member opens a list. Those are different operations with different storage and traffic costs. Estimation turns a product description into quantities you can compare with a capacity or freshness requirement.

Your task here is arithmetic, not an AWS deployment. Work the example using rough figures, then identify which approximation could change the design. The twenty-million-user workload is hypothetical. A small application can use the same method with tens of users, and an ownership problem may need no capacity estimate at all.

## Convert a daily workload into rates

> "Design the bookmark service. Twenty million people use it daily. Each one
> saves about five links and opens their list about fifty times."

You cannot look anything up and you have about ninety seconds before the
conversation moves on. The question is not whether you can architect. It is
whether you can turn that sentence into numbers, because until it is numbers
there is nothing to design against.

Three constants do almost all of the work, and none of them needs a calculator.

## Three useful estimates and their limits

**A day is about 100,000 seconds.**

The exact figure is 86,400. Round it up to 10<sup>5</sup>. That rounded day length is roughly 16% high, so the resulting request-rate
estimate is about 14% below the exact rate. It is useful for an initial
order-of-magnitude calculation. Use 86,400 and more precise inputs when the
difference could change a capacity decision.

So **requests per day ÷ 100,000 = requests per second**, and because both sides
are powers of ten it collapses to a ladder worth memorising once:

| Per day | Per second |
|---|---|
| 1 M | 10 |
| 10 M | 100 |
| 100 M | 1,000 |
| 1 B | 10,000 |

Ten times the traffic per day is ten times the traffic per second. Nothing else
to remember.

**One caution the ladder hides, and it is yours to add:** that is an *average*
second. Real traffic has a daily shape. Use a stated peak factor or a specific burst scenario before sizing. A factor
of two or three can be a starting assumption in an exercise, but it is not a
rule for every product. A concert launch can be much more concentrated. An
interviewer who hears "three thousand a second at peak, not one thousand"
learns more about you than the estimate itself does.

**Storage and network latency differ by factors of a thousand.**

| Where the data is | Roughly | Relative to memory |
|---|---|---|
| Memory | 100 ns | 1× |
| Local SSD | 100 µs | ~1,000× slower |
| Round trip across the world | 150 ms | ~1,000,000× slower |

These are illustrative latency assumptions, not guaranteed device or network
measurements. The ratios change with the operation, hardware, distance and
load. Use the large differences to ask where time is spent, then measure the
relevant path. A remote request may dominate a small calculation, but these
single-operation latencies do not tell you a database or disk's maximum throughput.

**Each extra nine divides annual downtime by ten.**

| Availability | Downtime per year |
|---|---|
| 99.9% (three nines) | ~8.8 hours |
| 99.99% (four nines) | ~53 minutes |
| 99.999% (five nines) | ~5 minutes |

Start from three nines being most of a working day, and the rest is division.
This makes a time-based availability target concrete: five nines allows about
five minutes of counted downtime in a 365-day year. First define what counts
as unavailable. A request-based objective instead counts failed eligible
requests, so do not substitute minutes for requests without stating the model.

| Convert the interview input | Question it helps answer |
|---|---|
| Users × actions per user per day | How many reads and writes occur each day? |
| Daily operations ÷ 86,400, or ÷ 100,000 for a rough estimate | What is the average rate in requests per second (RPS)? |
| A stated peak factor or burst arrival rate | What load must the service handle during the busy period? |
| Record count × bytes per record | What raw storage is needed before indexes, copies and backups? |
| Arrival rate × mean time in the system, under stable conditions | Roughly how much work is in flight at once? |



## The same question, worked

Use twenty million daily users, five saves and fifty opens each. For this exercise, **assume a peak three times the approximate daily-average rate**. That factor is a workload assumption, not a general law.

- Writes: 20 M × 5 = **100 M per day** → 1,000 per second → call it **3,000 at
  peak**.
- Reads: 20 M × 50 = **1 B per day** → 10,000 per second → **30,000 at peak**.

Now use latency without confusing it with throughput. If each of 30,000 reads/s
waits 100 µs for an I/O operation, the accumulated waiting is
`30,000 × 0.0001 = 3 seconds` across all requests in each wall-clock second.
It is **not thirty seconds**, and it does not by itself prove that a disk is
saturated. Independent operations can overlap. Under stable conditions, the
same rate and mean time imply about three operations in flight on average.

To decide whether the storage can keep up, consider actual IOPS, access pattern,
queue depth, caching and the rest of the request path. A cache or read replica
may be useful, but choose it because the measured or justified capacity model
needs it. An in-memory system can also run out of CPU or network capacity.

That is the whole point of carrying these. **The constants do not design the
system. They expose assumptions you need to check**, in the first
two minutes, out loud, in front of someone.

## When to reach for this

Any time a problem hands you a population and asks for a structure. In this
curriculum that means:

- [Design services from requirements to failure behavior](../../03-production/01-system-design/README.md) — use
  the workload where it changes the design, after understanding the user
  action and required behavior.
- [Set reliability objectives and recover from failures](../../03-production/05-reliability/README.md)
  — the nines table is what turns an availability target into an error budget.
- [Measure capacity and control performance costs](../../04-scale-and-evolution/02-performance-cost/README.md)
  — the latency ladder tells you which layer is worth measuring first.
- [Process, search and store data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) —
  caching, replication and partitioning are all answers to "this does not fit or
  does not keep up", which is an arithmetic finding.

Start by understanding the product action. Then estimate the quantities that
change the decision. A small ownership bug may need two users and one record,
while a video platform needs a bandwidth model. Do not invent huge traffic
just to make a simple problem look like a large system.

## Where this came from

Bruno sent a short video by [@arjay_mccandless](https://www.tiktok.com/@arjay_mccandless)
laying out the same three groups of constants. The numbers are standard
engineering reference values. The worked example, the peak-traffic caution and
the curriculum links above are this guide's.
