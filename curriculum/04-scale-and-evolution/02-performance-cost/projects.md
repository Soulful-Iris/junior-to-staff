# 14 · Performance and cost — five projects

> Senior tier · each one an afternoon · read [the section](README.md) first

Five projects that produce numbers instead of opinions: where the time actually
goes, four measurements around one change, the tail your load test was hiding
from you, what one request costs, and a bill cut in half without moving p99.

The section's argument is that performance and cost are the same skill pointed
at different units, and these projects are ordered so you feel that — the
profile in project 1 is the same instrument you use for money in project 5.

![Two load generators against the same one-second stall: the open-loop one sends five requests into it and reports a p99 of 940ms, the closed-loop one sends nothing during the stall and reports 210ms](../../../assets/diagrams/coordinated-omission.svg)

---

### 1. The profile that contradicts you

*You end up with a ranked list of where the time goes, and a written note of how wrong your guess was.*

**Build**

Before profiling anything, write down where you believe the time goes in one
request — the top three things, with percentages. Then profile the system under
load and rank what actually happens. Compare the two lists.

**The thought process**

The first move is the one that makes this project worth doing at all: **write
the guess down first.** Everybody knows where the slow part is, and everybody
is wrong often enough that the calibration matters more than the profile. Once
you have been wrong in writing you will profile before optimising for the rest
of your career; if you skip the guess, the profile just confirms whatever you
notice in it.

Second: **profile under load, not idle.** An idle profile shows you a different
system — caches are warm in ways they will not be, there is no lock contention,
the connection pool is not full, and the garbage collector has nothing to do. A
laptop profile is a hypothesis with a picture attached.

Third, the fact that makes most intuitions wrong: **most systems wait rather
than compute.** The profile of a normal web application is dominated by waiting
on the database, on a network call, on a lock, on the disk. Engineers reason
about algorithms because that is what code looks like, and the answer is
usually a query, a missing index, or a call being made ninety times that should
have been made once.

Fourth, the diagnostic that tells you which kind of problem you have: **if the
top item is under 5% of total, you do not have a hot spot.** You have a
distributed cost, which is a genuinely different and harder problem — there is
no single fix, and the honest answers are architectural or "leave it alone".
Recognising that early saves you from a month of small optimisations that add
up to nothing.

**How to organise the prompts**

```
Here is a profile (or a flame graph export). Tell me where the time
actually goes, ranked, as percentages of total.

Do not suggest optimisations yet, and do not reason from what the code
looks like — only from what the profile says. If it is dominated by
waiting rather than computing, say so and say what it is waiting on.
```

Forbidding reasoning from the source is the constraint doing the work. Handed
code, a model will generate plausible algorithmic optimisations indefinitely,
and they will all be about the wrong layer.

```
My guess was: <your three items with percentages>. The profile says:
<the ranked list>. Where was I wrong, and what kind of mistake is it —
did I overestimate compute, miss a wait, or miss a repetition?
```

Naming the *kind* of mistake is what makes it transfer to the next system.

```
Is the top item a hot spot or a distributed cost? If the top item is
under 5% of total, say so plainly and tell me what that means for how
I should approach this.
```

```
Now look for repetition specifically: is any single operation
happening far more times per request than I would expect? Count the
calls, not the time.
```

N+1 queries hide from time-ranked profiles when each call is fast. Counting
calls finds them immediately.

**On AWS**

For "where did the time go across services", **X-Ray** or
**CloudWatch Application Signals** is the right first instrument, because in a
distributed system most of the latency is in a hop rather than in a function.
The span-level view answers the question the flame graph cannot: which
dependency, and how many times.

For in-process profiling, the honest state of things is that AWS's own
first-party continuous profiler has been wound down, so the practical choices
are an eBPF-based profiler you run yourself (Parca, Grafana Pyroscope) or a
vendor agent. The property to look for is the one the section describes:
always-on, in production, at low single-digit CPU overhead, with a **diff flame
graph** between two versions. Measure that overhead on your own workload rather
than trusting the published figure — it is workload-dependent and the vendor's
workload is not yours.

For database time specifically, **RDS Performance Insights** is the highest-
yield tool in this whole project. Its database-load-by-wait-event view tells
you not just which query but what it was waiting *on* — CPU, lock, I/O, or a
client that was not reading fast enough — and those four have completely
different fixes. Pair it with `pg_stat_statements` for per-query totals, where
the column that finds N+1 problems is `calls`, not `total_time`.

For the load that makes the profile real, run the generator from **Fargate**
rather than your laptop, so the network path resembles production and you are
not measuring your own home connection.

**What productionising it means**

Profiling is always on rather than an event, so the question "what did this
release change about where time goes" is answerable. There is a recorded
profile attached to any performance claim. The load harness is repeatable and
runs from somewhere realistic. And the guess-then-measure habit is a written
step, because the value is in the comparison and the comparison evaporates if
you do it from memory.

**The learning**

Intuition about performance is systematically biased towards compute, because
compute is what the source code shows you, and real systems spend their time
waiting. The specific habit worth keeping is writing the guess down — not
because the guess is useful, but because being wrong on paper is the only thing
that reliably stops you optimising from memory next time.

**How you would know it is wrong**

- Compare your written guess to the profile. If they match exactly, check that you profiled under load rather than idle.
- Profile on your laptop and in production and compare the rankings. If they agree, you got lucky; they usually do not.
- Count calls as well as time. A fast query called ninety times is invisible in a time ranking.
- Check whether the top item is over 5%. Under that and there is no hot spot to find.
- Measure the profiler's own overhead on your workload before leaving it on.

---

### 2. Four numbers

*You end up with p50 and p99, before and after one change, measured the same way — and ideally with one of them having got worse.*

**Build**

Pick the change the profile pointed at. Record p50 and p99 under a fixed load
before making it. Make exactly one change. Re-measure both percentiles under
the same load. Write all four numbers down.

**The thought process**

The first rule, and the one that catches most people: **compare the same
percentile.** A p50 improvement quoted against a p99 baseline is not a
comparison, and it is the commonest way a performance claim turns out to be
empty. If you only have one number, you do not have a before-and-after.

Second, the trap this project is really built to expose: **optimisations
frequently improve p50 and worsen p99.** A cache does this routinely — a hit is
fast, but a miss now costs the lookup *plus* the cache round trip, so the
unlucky requests got slower while the average got better. A measurement that
watches only the average will call that a win, and the people having the worst
time will get a worse time.

Third: **prove the change applied.** A flag not set, a cache not warmed, a
config not deployed — all of them produce "no change", and so does a change
that genuinely did nothing. Assert the new code path actually ran, with a
counter or a log line, before you believe either result.

Fourth, and it is the one people skip because it feels like admitting defeat:
**exactly one change.** Two changes at once and you have learned nothing about
either. This is slow and it is the only way the numbers mean anything.

Fifth: **decide in advance what "no effect" looks like.** Run-to-run variance
on a p99 can be substantial, so a 5% improvement may be noise. Knowing the
noise floor before you start is what stops you shipping a rounding error with a
paragraph about it.

**How to organise the prompts**

```
I am about to change <X> for performance.

Write the measurement I should take BEFORE: which percentile, over
what window, under what load, and what number I should record.

Then tell me what result would mean the change did nothing, and what
result would mean it made things worse in a way this measurement would
hide.
```

The last clause is the whole prompt. It is where the p50-up-p99-down trap gets
named before you fall into it.

```
Before I trust either number: how do I prove the new code path
actually ran? Give me an assertion, not an argument.
```

```
Here are my four numbers: <p50/p99 before, p50/p99 after>. What do
they say, and what is the honest summary sentence — including if the
honest sentence is "this did not help".
```

Asking for the sentence including the null result is what keeps you honest when
you have already spent the afternoon.

```
Now the noise question. How many runs do I need for this p99 to be
stable enough that a <N>% difference means something?
```

**On AWS**

Percentiles are available and the default is not. **CloudWatch** supports
percentile statistics on metrics, and on an **Application Load Balancer**
`TargetResponseTime` you can graph `p50`, `p90`, `p99` directly — but the
dashboard you inherited is almost certainly showing `Average`, which is the
section's opening failure rendered as a default setting. Changing that one
dropdown is a real improvement to a real team.

The caveat worth knowing: CloudWatch percentiles are computed per period from
the raw values it has, and for custom metrics published as pre-aggregated
statistic sets it cannot compute percentiles at all. So if you want p99 on your
own metric, publish raw values or use **EMF** — which is
[10 · Observability](../../03-production/04-observability/README.md)'s point arriving here as a concrete
constraint.

For the change itself, the most AWS-specific version of this project is
**Lambda memory**, because on Lambda the memory setting controls CPU
proportionally, which means it is simultaneously a performance dial and a cost
dial pointing in opposite directions. **AWS Lambda Power Tuning** is a published
Step Functions state machine that runs your function at several memory settings
and plots cost against duration, so you can pick the point you actually want
rather than the default. It is the cleanest demonstration in the whole guide
that performance and cost are one instrument, and it takes about twenty
minutes.

Two other changes with measurable effects worth trying: moving to **Graviton**
instances or Lambda's arm64 architecture, which typically improves
price-performance and occasionally regresses for workloads with x86-specific
native dependencies; and **EBS gp3** over gp2, where you provision IOPS
independently of volume size and it is both cheaper and more predictable.

Use **CloudWatch Synthetics** as the before-and-after harness if the thing you
care about is a user journey rather than an endpoint, because it measures the
same path the same way each time, which is exactly what "measured the same way"
requires.

**What productionising it means**

Dashboards show percentiles rather than averages, and everyone knows the
p50/p99 gap for the main path. Performance claims come with four numbers and a
recorded profile. The new code path has an assertion proving it ran. And at
least one change has been reverted because the measurement said it did not help
— because a team that has never reverted an optimisation is a team that is not
measuring them.

**The learning**

A performance fix with no before-and-after at the same percentile is
indistinguishable from no fix at all, which means most performance work is
undocumented belief. The uncomfortable half is that improvements often move
cost around rather than removing it, and the average is the statistic most
likely to hide that.

**How you would know it is wrong**

- Check you compared the same percentile. This is wrong more often than any other step here.
- Look at p99 specifically after a caching change. If it got worse, you moved cost onto the unlucky.
- Assert the new path ran. "No change" and "did not deploy" produce identical graphs.
- Run the before measurement twice without changing anything. The difference between those two runs is your noise floor.
- Ask what you rejected. If every optimisation you measured was worth doing, you are only measuring the ones you already believed in.

---

### 3. The load generator that lied

*You end up with two different tail numbers from the same system and the same stall, and an understanding of which one your users live in.*

**Build**

Build a closed-loop load test — N threads, each sending the next request when
the last one returns. Introduce a one-second stall in the server. Record the
p99. Then rebuild the generator open-loop, at a fixed arrival rate, with the
same stall, and record the p99 again. Compare.

**The thought process**

The first thing to understand is the mechanism, because the name
**coordinated omission** does not explain itself. A closed-loop generator's
threads each wait for a reply before sending the next request. When the server
stalls, those threads are all blocked — so during the exact window when
requests would have been slowest, the generator sends none. The requests that
would have recorded the worst latencies were never made.

Second: **this is not a subtle bias, it is a large one.** A one-second stall
that should have produced dozens of slow requests produces four — one per
thread — and the rest of the window is simply absent from the data. The
reported p99 can be an order of magnitude better than the truth.

Third, and this is why it matters beyond load testing: **real users are
open-loop.** They arrive when they arrive. They do not politely wait for your
server to recover before deciding to click. So the open-loop number is the one
that describes the experience, and the closed-loop number describes a system
the test accidentally protected from load.

Fourth, the fix has two forms and both are worth knowing: send at a fixed
arrival rate regardless of responses, or keep the closed loop but *correct* the
recorded latencies by attributing the missing requests the time they would have
waited. Good load tools do one or the other; the point is knowing which yours
does, because the default in many is the biased one.

Fifth, the generalisation, which is the real prize: **this is the instruments
problem in its purest form.** The test was green because it could not see. Ask
of any measurement what it would have shown if the thing were broken — here,
the answer is "a healthy p99", which is the same as when it is fine, so it
proved nothing.

**How to organise the prompts**

```
Explain coordinated omission for my specific setup: <N> threads, each
sending the next request when the previous returns, against a server
that stalls for 1 second.

Work out how many requests my generator will FAIL to send during that
stall, and what that does to the reported p99. Show the arithmetic.
```

Making it do the arithmetic on your numbers is what turns a known phenomenon
into something you believe about your own test.

```
Write both generators: one closed-loop at <N> threads, one open-loop
at a fixed arrival rate of <R> per second. Same target, same duration.

Then give me a way to inject a 1-second stall on demand.
```

```
I ran both. Closed loop says p99 <A>, open loop says p99 <B>. Is that
gap consistent with the arithmetic above, or is something else going
on?
```

```
Now check the tool I actually use in CI: does it correct for
coordinated omission, and if so, how do I confirm that rather than
trust the documentation?
```

That last question is the one to actually act on. Most teams have a load test
already, and the useful outcome of this project is finding out whether it has
been lying to them.

**On AWS**

The generator has to be able to sustain a fixed rate, which means it must not
be the bottleneck. Run it from **Fargate** with enough tasks that the
generator's own CPU is comfortable, and check that first — a saturated load
generator produces exactly the same shape of lie for a different reason.
**Distributed Load Testing on AWS** is the published solution if you want the
orchestration handled.

On the tooling: k6 has constant-arrival-rate executors, Gatling has open
injection profiles, and JMeter's default thread-group behaviour is the
closed-loop one. Which you use matters less than checking which mode you are
in.

For injecting the stall honestly, **AWS Fault Injection Service** can pause a
dependency or inject latency, with a **CloudWatch alarm** as the stop
condition. The cheaper version is a feature-flagged sleep in one endpoint, and
for this project that is genuinely fine — you are testing your measurement, not
your system.

For the comparison, measure at the **Application Load Balancer** as well as at
the generator. The ALB's `TargetResponseTime` p99 is measured server-side and
excludes queueing that happened before the request arrived, which is a third
number and a useful one: the gap between what the server thinks its p99 is and
what the client experiences is where connection queueing and DNS live.

**What productionising it means**

The load test in CI is open-loop or corrected, and somebody has verified which
rather than reading the documentation. The generator's own resource use is
monitored so a saturated generator cannot masquerade as a slow system. Results
record arrival rate, not just thread count, because thread count does not
describe a load. And the stall injection is repeatable, so the test can be
re-validated after a tooling upgrade.

**The learning**

A measurement can be wrong in the direction of comfort by omitting the data
that would have been inconvenient, without anybody doing anything dishonest.
Once you have seen a p99 improve by an order of magnitude purely by changing
how the requests were sent, you stop asking "what does the number say" and
start asking "what could this instrument not have seen".

**How you would know it is wrong**

- If the two generators produce the same p99, check that the stall actually happened during both runs.
- Watch your load generator's CPU. A saturated generator under-reports for a different reason and looks identical.
- Compare client-measured and ALB-measured p99. A large gap is queueing the server never saw.
- Read your CI load tool's configuration for its executor type. "It is fine" is not an answer you can check.
- Ask what your test would show if the server stalled for a full second tomorrow. If the answer is "probably nothing", that is the finding.

---

### 4. The unit cost, with the guesses marked

*You end up able to say what one request, user or job costs — and exactly which parts of that number you invented.*

**Build**

Compute the cost of one unit of the main thing your system does. Show the
arithmetic. Mark every figure you had to guess, and write down what you would
measure to replace each guess. Then tag your resources so that next quarter the
number comes from data.

**The thought process**

The first idea is the one the whole cost discipline rests on: **you cannot
manage a number you cannot break apart.** "The bill went up" is not actionable.
"The bill went up because the link-fetch job now runs four times as often" is.
Everything else in cost engineering is in service of being able to say the
second sentence.

Second, and this is what makes it engineering rather than accounting:
**attribution is a tagging problem, and tagging is a decision about what you
want to be able to ask.** By service, by environment, by team, by feature. You
cannot retroactively tag last quarter, so the cost of getting this wrong is
paid in time.

Third: **the unit cost is the number that makes decisions possible.** What does
one request cost? One user per month? One job? Almost nobody can answer, and
the teams that can make visibly different decisions — they know which features
are worth their compute, and they know when a 20% efficiency gain is worth an
engineer-week and when it is worth four dollars.

Fourth, the honesty requirement: **mark the guesses.** A unit-cost estimate
with its assumptions flagged is useful. One without them is a number that will
be quoted in a meeting for a year and gradually become a fact nobody can trace.

Fifth: **include the parts nobody counts.** Data transfer between Availability
Zones. NAT gateway processing. Log ingestion. The cost of the observability you
added in section 10. Those are routinely a third of a bill and are never in
anybody's mental model, because they are not attached to a service anyone chose.

**How to organise the prompts**

```
Here is my architecture and here is my bill (by service). Work out the
cost of one <request / user / job>, showing the arithmetic, and tell
me which component dominates it.

Then tell me which parts of that number you had to guess, and what I
would have to measure to replace each guess.
```

The second paragraph is the whole value of the prompt.

```
Now the costs that are not attached to a service anybody chose: data
transfer between Availability Zones, NAT gateway processing, log
ingestion, metrics storage, snapshots, idle resources.

Estimate each for my architecture and tell me which one is likely to
be bigger than I think.
```

```
Design the tagging so that next quarter this number comes from data
instead of arithmetic: which tags, on which resources, and what I will
be able to ask that I cannot ask today.

Tell me what will NOT be taggable and how I should apportion it.
```

Shared and untaggable costs are real and the apportionment rule should be a
decision, not a silence.

```
Given the unit cost, which of my features is not worth what it costs
to run? Be specific and tell me how confident you are.
```

**On AWS**

The mechanism is **cost allocation tags** activated in Billing, then
**Cost Explorer** grouped by tag — and the thing to know is that tags only
apply from activation forward, so this is a decision with a deadline. For
anything beyond Cost Explorer's granularity, the **Cost and Usage Report**
delivered to **S3** and queried with **Athena** is the real instrument: it is
line-item level, it includes the resource id, and it is where a unit cost
actually gets computed. **AWS Budgets** then makes the number arrive without
being asked.

The costs people miss, concretely, and all four are worth checking today:

**NAT Gateway** charges both an hourly rate and a per-gigabyte processing
charge, so a private subnet pulling container images or talking to S3 through
NAT can quietly be one of your largest line items. The fix is a **VPC gateway
endpoint** for S3 and DynamoDB, which costs nothing, and **interface endpoints**
for other services where the traffic justifies it. This is the single most
common surprise on an AWS bill and the fix is an afternoon.

**Cross-Availability-Zone data transfer** is charged in both directions, so a
chatty service spread across three AZs pays for its own resilience in a line
item that says "data transfer" and names nothing.

**CloudWatch Logs** bills mostly on ingestion, and log groups default to
never expiring. Retention policies and the **Infrequent Access** log class are
the levers; exporting cold logs to S3 for Athena is the structural fix.

**Idle and forgotten resources**: unattached EBS volumes, old snapshots, idle
load balancers, unused Elastic IPs, **ECR** repositories with no lifecycle
policy accumulating every image ever built. **Trusted Advisor** and
**Compute Optimizer** will list these, and Compute Optimizer will additionally
tell you which instances are over-provisioned with the measured evidence
attached.

**What productionising it means**

Cost allocation tags are enforced — ideally by a Service Control Policy or a
Config rule that flags untagged resources — because tagging that depends on
memory decays. The unit cost is recomputed quarterly and the trend is the thing
people look at. There is a named owner for the bill. And the guesses in the
original estimate have been replaced by measurements one at a time, so the
number gets more honest rather than more confident.

**The learning**

Cost is a performance metric with a currency, and the reason it feels like a
different discipline is only that it arrives on an invoice instead of in a
dashboard. The unit cost is the number that converts an argument about
efficiency into a decision, and the discipline that produces it is attribution —
which is a tagging decision you have to make before you need the answer.

**How you would know it is wrong**

- Ask a colleague for their unit-cost number. If nobody can produce one, cost is unattributed whatever the tagging policy says.
- Check whether your estimate includes data transfer, NAT processing and log ingestion. It usually does not, and they are usually large.
- Look at the share of your bill that is untagged. That share is the part you cannot manage.
- Recompute next quarter from data and compare to this quarter's arithmetic. The gap tells you which guesses were bad.
- Find one feature whose run cost exceeds its value. If there is none, either you are unusually disciplined or you have not looked.

---

### 5. Half the bill, same p99

*You end up with a measurably smaller bill and a p99 that did not move — and a written note of the saving you refused to take.*

**Build**

Take the three biggest attributable line items from project 4 and cut them,
with a hard constraint: p99 on the main path must not get worse. Measure before
and after, on both axes. Then find one available saving you deliberately did
not take, and write down why.

**The thought process**

The first thing that makes this a senior project rather than a cost-cutting
exercise is the constraint: **the p99 must hold.** Cost reduction without a
performance guardrail is trivially easy and usually a mistake — you can always
make something cheaper by making it worse. Holding the tail constant is what
forces the savings to come from waste rather than from quality.

Second, the ordering: **take the free ones first.** A surprising share of a
typical bill is not a trade at all — an endpoint that removes a data-processing
charge, a retention policy on logs nobody reads, a lifecycle rule on images
nobody pulls, an instance that has been idle since a migration in March. None
of those costs you anything, and doing them first means the hard decisions are
made against a smaller, truer number.

Third, the ones that are genuinely trades, and the axis each trades on: a
cheaper storage class trades retrieval latency; a smaller instance trades
headroom; Spot capacity trades interruption tolerance; a commitment trades
flexibility for a discount. Name the axis, as in
[08 · System design](../../03-production/01-system-design/README.md), and the decision becomes sayable.

Fourth, and this is where people get it wrong in a way that hurts later:
**a commitment is a bet on your own architecture.** A one-year commitment made
the month before you migrate to a different compute model is a discount on
something you are about to stop using. Take commitments on the part of your
usage you are confident is stable, and leave the volatile part on demand.

Fifth: **write down the saving you refused.** There is always one that would
work and that you should not take — usually because it trades against
reliability or against your ability to move later. Recording it, with the
reason, is what stops it being re-proposed every quarter and what proves you
were choosing rather than just cutting.

**How to organise the prompts**

```
Here are my top line items with their tags: <the data from project 4>.

For each, split the possible savings into two lists: (a) savings that
cost me nothing — waste, idle resources, missing configuration; and
(b) savings that are a real trade.

For list (b), name the axis each one trades on.
```

The split is the prompt. Without it you get a mixed list and you will take an
easy trade before an obvious waste.

```
For everything in list (a), give me the exact change and tell me how I
verify it worked — the metric and the expected direction.
```

```
I am holding p99 constant. For each item in list (b), tell me the
mechanism by which it could make p99 worse, and what I should watch
during the change.
```

Asking for the mechanism rather than the risk gets you something checkable.

```
Now the commitment question. Which portion of my usage is stable
enough to commit to, and what is my architecture likely to change in
the next year that would make a commitment a mistake?
```

```
Which of these savings should I NOT take, and why? I want the one
that is technically available and strategically wrong.
```

**On AWS**

The free ones first, because they are genuinely free: **VPC gateway endpoints**
for S3 and DynamoDB remove NAT data-processing charges at zero cost;
**CloudWatch Logs retention** and the Infrequent Access class; **ECR lifecycle
policies**; deleting unattached **EBS** volumes and stale snapshots; and
**S3 Intelligent-Tiering**, which moves objects between access tiers
automatically and is the right default when you genuinely do not know the
access pattern — which is most of the time.

The real trades, with their axes. **Savings Plans** and **Reserved Instances**
trade flexibility for a discount; Compute Savings Plans are the more flexible
of the two and cover Lambda and Fargate as well as EC2, which matters if your
architecture is still moving. **Spot** — including **Fargate Spot** — trades
interruption tolerance for a large discount and is correct for anything
retryable: batch, CI runners, queue consumers that can be killed. **Graviton**
is the unusual one because for most workloads it is not a trade at all, just
better price-performance; verify on your own workload because native
dependencies occasionally regress.

For right-sizing, **Compute Optimizer** gives you recommendations with the
measured utilisation behind them, which is what makes it arguable rather than a
guess; **Trusted Advisor** covers idle resources and the obvious waste.

For databases, the two big levers are **Aurora Serverless v2** when your load is
spiky enough that you are paying for a peak you rarely see, and **DynamoDB
on-demand versus provisioned** — on-demand is more expensive per request and
removes the risk of under-provisioning, so the decision is genuinely about
whether your traffic is predictable. Switching between them is possible but
rate-limited, which is worth knowing before you plan around it.

And the guardrail: keep the **CloudWatch** p99 dashboards from project 2 open
during every change, and set an alarm. A cost change that quietly moved the
tail is the failure mode of this whole project.

**What productionising it means**

The savings that cost nothing are applied by policy rather than by project —
lifecycle rules, retention defaults, a Config rule for untagged or idle
resources — so they do not come back. Commitments are sized to the stable
portion and have a review date. The p99 guardrail is an alarm, not a habit.
And the refused saving is written down with its reason, so the next person who
finds it does not have to rediscover the argument.

**The learning**

Most of a first big cost reduction is not a trade-off at all — it is waste,
defaults nobody changed, and resources nobody deleted. The senior part is what
comes after that: naming the axis each remaining saving trades on, and being
able to refuse one because the trade is bad, which requires having a number for
what you are protecting.

**How you would know it is wrong**

- Check p99 before and after each change, at the same percentile under the same load. If you did not, you do not know what the saving cost.
- Separate the free savings from the trades. If your list is all trades, you have not looked for waste.
- Look at your NAT gateway line and your log ingestion line specifically. Both are commonly large and both have cheap fixes.
- Re-read your commitment against your roadmap. A discount on something you are about to stop using is a cost.
- Name the saving you refused. If there is none, you were cutting rather than choosing.
