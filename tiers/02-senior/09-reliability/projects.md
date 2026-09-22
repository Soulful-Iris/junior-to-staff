# 09 · Reliability — five projects

> Senior tier · each one an afternoon or two · read [the section](README.md) first

Five projects that turn reliability from a wish into a set of numbers you have
chosen. Each one ends with something you can point at: a policy, an alert that
has fired correctly, an amplification factor, a shed request, a system that
recovered on its own.

They assume you have something running — the [Act 1](../../../acts/act-1-junior/)
system, or anything you own with an outbound call in it.

![Two alert windows watching the same error budget: a fast burn crossing both and firing, and a slow trickle crossing the long window only and staying quiet until it matters](../../../assets/diagrams/burn-rate.svg)

---

### 1. The SLO you would actually honour

*You end up with one number, a written policy, and an honest answer about whether you would keep to it.*

**Build**

Pick the single thing users care about most in your system — the list loading,
the item saving — and define an SLO for it: a metric, a target, and a window.
Then write the error-budget policy: what happens at 75% of the budget spent, and
what happens at 25% left.

**The thought process**

The first decision is **what to measure**, and the instinct is wrong. Engineers
reach for uptime of the process, which is a fact about your infrastructure.
Users experience whether their request succeeded quickly. So the metric is
almost always a ratio of good requests to total, measured at the edge, where
"good" is a definition you have to write down — and writing it down is most of
the work.

Second: **the target is a budget, not an aspiration.** 99.9% over thirty days is
about 43 minutes of failure you are *allowed*. Picking 99.99% because it sounds
better commits you to four minutes, and you will breach it in the first week and
then stop looking, which is worse than a target you keep.

Third, and this is where most SLOs quietly die: **the policy has to bind
somebody.** "When the budget is spent we will focus on reliability" is a
sentence. "When the budget is spent, feature work stops until it recovers" is a
policy — and the honest question is whether you, personally, would do that on a
week when something else is due. If the answer is no, pick a target you would
honour rather than one that sounds serious.

**How to organise the prompts**

```
Here is my system. Propose three candidate SLIs for the thing users care
about most, each as a precise ratio: what counts as good, what counts as
total, and where it is measured.

For each, tell me what it would MISS — a real user-visible failure that
this indicator would score as fine.
```

That last question is the one that matters. Every indicator has a blind spot,
and knowing it beforehand is the difference between a number you trust and one
you defend.

```
For the SLI I picked, implement it: a metric emitted at the edge, with
good and total counted separately so I can see both.

Do not compute the ratio in the application — emit the counts and let
the query do the arithmetic.
```

Why that constraint: a precomputed ratio cannot be re-sliced later. Counts can.

```
Write the error-budget policy as rules with thresholds and
consequences. Then tell me, for each consequence, what would have to be
true organisationally for it to actually happen.
```

**On AWS**

Emit the counts as **CloudWatch** metrics from the edge — if you are behind an
**Application Load Balancer** you already have `RequestCount` and
`HTTPCode_Target_5XX_Count`, which is an SLI for free and worth starting from
before you instrument anything yourself. That is the "why this service" answer:
it exists already and it is measured outside your process, so it keeps working
when your process does not.

**CloudWatch metric math** computes the ratio at query time from the two counts,
which is exactly the split above. For anything richer — per-endpoint, per-user-
class — use a **metric filter** on structured logs, or emit your own metrics with
**EMF** (embedded metric format), which lets you write one structured log line
and have CloudWatch extract metrics from it. EMF is the underrated one here: one
write, both signals, no separate metrics client.

Watch the cost shape: custom metrics bill per metric per month, so an SLI split
by a high-cardinality dimension is a bill rather than an insight. Start with two
counters.

**What productionising it means**

The SLI is measured where the user is, not inside the process. The target is a
number you would honour and have written down. The policy names consequences
somebody has agreed to. And the budget is visible somewhere you look weekly, not
somewhere you look during an incident.

**The learning**

An SLO is not a reliability target, it is a *permission to fail a specific
amount* — and that inversion is what makes it useful. Without a budget, every
failure is a crisis and reliability work never ends; with one, you know whether
you have room.

**How you would know it is wrong**

- Break the thing on purpose and check the SLI moved. An indicator that does not notice your deliberate failure is measuring something else.
- Find a real user-visible failure your SLI scores as fine. There is always one — name it.
- Compute the budget in minutes and say it out loud. If 43 minutes a month sounds absurdly generous or impossibly tight, your target is wrong.
- Ask yourself whether you would freeze feature work. Answer honestly, then adjust the target rather than the honesty.

---

### 2. The alert that fires when it matters and not before

*You end up with an alert that caught a fast burn and stayed quiet through a slow one.*

**Build**

Replace a static threshold alert with a multi-window, multi-burn-rate alert on
the SLO from project 1, then prove it both ways: fire it with a fast burn, and
confirm it stays quiet through a trickle that does not threaten the budget.

**The thought process**

Start from what is wrong with thresholds. "Alert if error rate is above 1%"
fires on a thirty-second blip that costs you nothing, and stays quiet through a
0.9% error rate that eats your whole month's budget in a week. It is measuring
the wrong quantity: you care about **how fast the budget is being spent**, not
the instantaneous rate.

That gives you burn rate — spending at 14.4x the sustainable rate exhausts a
thirty-day budget in about two days. And then the second decision, which is the
clever part of the standard approach: **two windows.** A short one so you notice
quickly, a long one so a blip in the short window does not page anybody. Both
must be burning for it to fire, and both must recover for it to clear.

Third: **what severity, and who gets woken.** A fast burn is a page. A slow burn
is a ticket. Conflating them is how alerts become noise, and an alert people
have learned to ignore is worse than no alert because it occupies the space where
a real one would have been noticed.

**How to organise the prompts**

```
Here is my SLO: <target> over <window>. Explain burn rate for this
specific budget, with the arithmetic: at what multiple is the whole
budget gone in two days, and in one hour?

Then propose a two-window alert and tell me what each window is FOR.
```

Making it show the arithmetic for your own numbers is what turns a borrowed
recipe into something you can defend.

```
Implement it. Then simulate two scenarios against the implementation:
a sharp 30-minute outage, and a steady 0.9% error rate lasting a week.

For each, tell me whether it fires, when, and at what severity.
```

```
Now show me the case where this alert is WRONG — a real failure it would
miss, or a harmless event it would page for. I want the blind spot, not
reassurance.
```

**On AWS**

A **CloudWatch alarm** on a **metric math** expression over the good/total
counters, with two alarms — a short-window and a long-window — combined in a
**composite alarm** so the page only fires when both are in ALARM. That
composite alarm is the specific feature that makes this pattern easy on AWS and
is worth knowing by name; without it you end up with two noisy alarms and a
human doing the AND.

Route it through **SNS** to wherever you actually look. And the setting people
miss: **treat missing data as breaching** for at least your critical alarm,
because a component that stopped emitting looks identical to a healthy one, and
"no data" is the shape of the worst outages.

Why not a third-party alerting service: you may well want one eventually for
on-call rotation and escalation, and that is what they are for. The argument for
staying in CloudWatch while learning is that the alarm sits next to the metric it
watches, so there is one fewer system to keep in sync.

**What productionising it means**

The alert has fired on a real or simulated fast burn, and you have watched it
stay quiet through a slow one. Severities are split: page for fast, ticket for
slow. Missing data alarms. And the runbook link is in the alert body, because an
alert that says only "SLO burn rate high" at 3am is a puzzle rather than a page.

**The learning**

Alerting is a design problem, not a threshold. The question is never "what value
is bad" but "what pattern is worth a human being awake", and burn rate is the
first formulation of that which actually survives contact with a noisy system.

**How you would know it is wrong**

- Fire it deliberately with a sharp burst. Time how long until the alert arrives.
- Run a slow trickle that does not threaten the budget. It must stay quiet.
- Stop emitting the metric entirely. It must alarm on missing data.
- Read the alert body as somebody woken by it. Does it say what is burning, how fast, and where to look?

---

### 3. The retry storm you build on purpose

*You end up with a number: how many requests one user action produces when everything retries.*

**Build**

Stack three layers that each retry three times — client, API, data client — then
measure from the outside how many requests one user action actually generates.
Then fix it: retry at one layer only, with jitter and a token bucket, and measure
again.

**The thought process**

The first thing to understand is that **retries multiply, not add.** Three
layers at three attempts is twenty-seven requests from one click, and every
layer's author made a locally reasonable decision. Nobody chose twenty-seven.

Then the counterintuitive bit: **the retry makes the outage worse.** When a
dependency is struggling, the thing that pushes it from slow to dead is the
retry traffic from everyone politely trying again. This is why the discipline is
retry at *one* layer — usually the one closest to the failure, which knows
whether the operation is safe to repeat.

Third: **retries are only safe if the operation is idempotent**, which means
this project has a precondition. A retried POST that creates something creates it
twice, and the fix is an idempotency key rather than a cleverer retry policy.

Fourth, and this is where the AWS position is genuinely instructive: a **token
bucket** is preferable to a circuit breaker for limiting retries. A breaker is
modal — it is either open or closed, which makes it hard to test and slow to
recover — where a bucket degrades smoothly and self-heals as capacity returns.

**How to organise the prompts**

```
Here are the three layers of my call chain. Tell me, for each, what its
current retry behaviour is — including any retries I did not write,
which the HTTP client or SDK does by default.

Then compute the worst-case number of requests one user action produces.
```

The "retries I did not write" clause is the important one. Most SDKs retry by
default and most people do not know their own numbers.

```
Build the storm deliberately: make the bottom dependency fail, and count
the requests it actually receives from the OUTSIDE. I want the measured
number, not the computed one.
```

Measured from outside, because that is the only place amplification is visible.

```
Now fix it: retries at one layer only, full jitter on the backoff, and a
token bucket limiting the retry budget. Measure again from the outside.

Tell me both numbers.
```

```
Add idempotency keys so a retry of a write is safe. Then write a test
that sends the same keyed request twice CONCURRENTLY and asserts the
effect happened once.
```

**On AWS**

The AWS SDKs have retried with a token bucket for years, and the setting to know
is the **retry mode** — `standard` and `adaptive` (adaptive adds client-side rate
limiting) against the older `legacy` behaviour. Reading your own SDK's configured
retry mode is the two-minute version of this project's first prompt.

For the operations themselves: **idempotency tokens** are a first-class concept
in several AWS APIs (EC2's `RunInstances` being the canonical example) and are
worth looking at as a design to copy rather than invent. **API Gateway** can be
configured to pass a client-supplied idempotency key through, and **DynamoDB**
conditional writes give you the storage-level "only once" guarantee cheaply — a
conditional put on the key is the whole implementation.

Where you can see amplification: the target-side metrics on an
**Application Load Balancer**, or **VPC Flow Logs** if the dependency is
internal. Both count what actually arrived, which is the number you want.

**What productionising it means**

Retries exist at exactly one layer and you can say which. Every backoff has
jitter, not just the retry — synchronised clients are a self-inflicted thundering
herd. The retry budget is bounded. Writes carry idempotency keys. And the
amplification factor is a number you measured rather than reasoned about.

**The learning**

Every layer retrying is a system that turns a small failure into a large one, and
the arithmetic is multiplicative and invisible from any single layer. This is
also the clearest example in the guide of a property that only exists in the
whole system — no component is wrong.

**How you would know it is wrong**

- Count requests at the dependency during a failure, from the dependency's side. Compare to your computed worst case.
- Check for retries you did not write: read the SDK and HTTP client defaults.
- Send the same keyed write twice, concurrently. The effect must happen once.
- Remove the jitter and watch the request timing cluster. That clustering is the herd.

---

### 4. Shedding the right thing

*You end up having refused work under pressure, on purpose, and confirmed the right class suffered.*

**Build**

Classify your requests into three priorities, then shed the lowest first when the
system is short of capacity. Load it until shedding starts, and verify from the
outside that the high-priority class kept working.

**The thought process**

The first decision is the product one: **what are the classes?** A person loading
their own list is not the same as a background refresh or a bulk export. Writing
that ranking down is a statement about who your system is for when it cannot
serve everybody, and it is much easier to make calmly in advance than during an
incident.

Then the mechanism question: **shed on what signal?** CPU, queue depth, latency,
or a concurrency limit. Each has a failure mode — CPU lags the actual problem,
latency is already-too-late, concurrency limits are crude but honest and
immediate. Picking is the engineering.

Third, and it is the part that makes shedding humane: **a shed request must get
an honest answer.** A 429 with a retry-after header tells a client what to do. A
hanging connection tells it nothing and holds a resource while doing so. Shedding
fast is what makes it work; shedding *politely* is what makes it usable.

**How to organise the prompts**

```
Here are the kinds of request my system serves. Propose three priority
classes and place each kind in one.

For each class, say what the user experiences when it is shed, and who
would complain first.
```

```
Implement shedding on <signal>. When shedding, the lowest class gets a
429 with retry-after; higher classes are unaffected.

Then show me the code path that decides, and tell me what it costs to
evaluate on every request.
```

That last clause matters: a classifier that costs a database lookup is a new
dependency in your hottest path.

```
Now load it past its capacity. Report, from the OUTSIDE: what each class
experienced, and whether any high-priority request was refused.

If any was, that is a bug — tell me where the classification failed.
```

**On AWS**

Several layers can shed and they are not equivalent. **API Gateway** has usage
plans and throttling per key, which is the cheapest place to stop a flood because
it happens before your compute runs. An **Application Load Balancer** does not
prioritise by class, but it does have a queue and will fail fast when targets are
saturated. **WAF** rate-based rules act earlier still and are the right answer to
abuse rather than to legitimate overload — that distinction is the one to be able
to make.

For priority *within* your own traffic, the honest answer is that you implement
it: a concurrency limiter in your handler with per-class budgets. On **Lambda**,
**reserved concurrency** per function gives you class isolation almost for free
if you split classes across functions — which is a genuine architectural reason
to split, and one of the better ones.

**What productionising it means**

The classes exist in code, not in a document. Shed responses carry retry-after
and are fast. There is a metric for shed-by-class, so you can see it happening.
And you have watched a real load test confirm the high class survived, because
classification bugs are invisible until exactly the moment they matter.

**The learning**

Capacity is finite and something will be refused. The only choice you have is
whether the refusal is chosen or arbitrary — and a system without a ranking
refuses whatever happens to arrive when the queue is full, which is usually the
person who cares most.

**How you would know it is wrong**

- Load past capacity and verify the *low* class is what suffered.
- Check the shed response: status, retry-after, and how fast it came back.
- Measure the classifier's own cost per request.
- Shed 100% and confirm the system stays up and recovers when load drops.

---

### 5. The failure that will not recover

*You end up having built a system that stays down after the cause is gone, and then fixed it.*

**Build**

Induce a metastable failure: overload the system, remove the overload, and watch
it stay broken. Then find the mechanism and fix it.

**The thought process**

This is the most valuable project in the section and the least known. A
**metastable failure** is one where the trigger has gone and the system remains
down, because the recovery itself requires capacity the system no longer has. A
queue full of work whose timeouts have all expired; a cache that emptied, so
every request now hits the database, so nothing ever repopulates the cache; a
retry backlog that saturates the very capacity needed to drain it.

The decision that makes this tractable is realising it is about **a sustaining
loop**, not about the trigger. So the question to ask of your own system is: is
there any state where the work required to recover exceeds the capacity
available? That question is answerable on paper, before you build the drill.

Then the fixes, which are all about breaking the loop: drop work that is already
too old to be useful, admit load gradually rather than all at once when
recovering, and keep enough capacity in reserve that recovery is possible.

**How to organise the prompts**

```
Here is my system. Is there a state where it would stay broken after the
cause was removed? Walk through the loop: what is consuming the capacity
that recovery needs.

If you think there is not, tell me what property prevents it.
```

That second sentence is the honest version — sometimes the answer is genuinely
no, and knowing why is as valuable as finding one.

```
Design a safe experiment that induces it in my environment, with a stop
condition so I can end it. Do not run anything yet.
```

```
Now the fixes. For each: drop stale work, gradual admission on recovery,
reserved capacity. Tell me what each costs when the system is HEALTHY,
because that is the price I pay every day for a rare event.
```

The everyday cost is the real decision. Most resilience mechanisms are a small
permanent tax against a rare catastrophe, and you should know the tax.

**On AWS**

Three concrete places this bites. **SQS** message age is the metric that reveals
it: a queue whose oldest message keeps getting older while the consumer runs flat
out is a metastable state, and the fix is often to drop messages past a useful
age — which you do by checking the timestamp in the handler, because SQS will not
do it for you.

**Auto Scaling** can be part of the loop rather than the cure: scaling out helps
only if the bottleneck is your compute, and if it is the database then more
instances make it worse. Knowing which is why you did project 4 first.

And **provisioned concurrency** on Lambda, or a warm pool on an ASG, is the
reserved-capacity answer — it costs money while idle, which is exactly the
everyday tax the third prompt asks you to price.

**What productionising it means**

Work has a maximum useful age and is dropped past it. Recovery admits load
gradually rather than opening the gates. Queue age is a monitored metric with an
alarm, because it is the early signal. And you have induced the failure once, in
daylight, so you recognise it — which is the only reason anybody diagnoses these
quickly.

**The learning**

Some failures are self-sustaining, and for those, removing the cause is not the
fix. Once you have seen one you will stop asking "what broke" first and start
asking "what is keeping it broken", which is a different and better question.

**How you would know it is wrong**

- Induce it, remove the trigger, and watch. If it recovers on its own, you did not build a metastable failure — find the real loop.
- After the fix, induce it again. Recovery should happen without intervention, and you should be able to time it.
- Check the everyday cost of each fix. If it is zero, you have probably not actually reserved anything.
- Look at queue age rather than queue depth. Depth can be flat while age climbs, and age is the one that tells you.
