# Act 2 · Senior — five projects

> Build a thing that survives · a weekend each · pick one
>
> Integrates sections [08](../../tiers/02-senior/08-system-design/) through
> [15](../../tiers/02-senior/15-ai-systems/). Each one assumes you have something
> from [Act 1](../act-1-junior/) — or any small system you already own.

Act 1 was about making a thing exist. Act 2 is about making it survive load, a
dependency dying, a bad deploy, and three in the morning. Nothing a user can see
gets added in any of these five, which is why they are the projects people skip
and the ones that separate a senior engineer from a fast junior one.

![What act two adds to an act one system: a queue absorbing bursts, a cache in front of the store, telemetry leaving to somewhere you can query, and a pipeline that puts the artefact out — with the outside call now bounded by a timeout and a breaker](../../assets/diagrams/act2-shape.svg)

**Where the difficulty sits, per project:**

| | project | the part that is actually hard |
|---|---|---|
| 1 | degrade, do not stop | deciding in advance what to give up |
| 2 | twenty deploys a day | making a deploy boring enough to do on a Friday |
| 3 | debuggable at 3am | shrinking the gap between broke and knew |
| 4 | the flood | bounding everything, including the things you forgot are unbounded |
| 5 | an AI feature you can defend | proving it is any good, which is four fifths of the work |

---

## 1. Degrade, do not stop

*When the thing you depend on goes away, your product gets worse rather than stopping.*

**Build**

Take the outside call from your Act 1 system — the page fetch, the vision model,
the mail sender — and make every failure mode of it a designed behaviour rather
than an accident. Then turn the dependency off and use the product.

**The thought process**

The decision that has to come first, and it is a product decision disguised as a
technical one: **what does the user get when the dependency is gone?** There are
only a few honest answers — the stale version, a placeholder, a queued promise,
or a clear refusal — and picking is your job, not the framework's.

Then the ordering that matters: you cannot decide timeouts until you have decided
degradation. A timeout is how long you are willing to wait *before doing the
fallback*, and without a fallback there is nothing to time out into, which is why
so many systems have timeouts measured in minutes.

Third, and this is the senior part: **classify your requests.** Not everything
deserves the same treatment when you are short of capacity. Somebody loading
their own list matters more than a background refresh. Rank them before you need
to, because you will not do it well during an incident.

**How to organise the prompts**

```
Here is my system and the one call it makes to a service I do not
control. List every way that call can fail — not just error and
timeout, but slow, partial, wrong, and succeeding with stale data.

For each, tell me what the user currently sees. Do not fix anything yet.
```

The current behaviour is the finding. Most of those rows will say "the page
hangs" or "a 500".

```
Now, for each failure, I will tell you the behaviour I want. Implement
the fallback path FIRST, before touching the timeout, and give me a way
to force each fallback on demand.
```

Forcing it on demand is the part that makes this real. A fallback you cannot
trigger deliberately is a fallback you have never seen.

```
Add a circuit breaker. Then show me the three states — closed, open,
half-open — actually happening in a test, with what the user sees in
each.
```

```
Classify requests into three priorities and shed the lowest first under
pressure. Show me the shedding happening, and tell me what a user in
each class experiences.
```

**On AWS**

The fallback usually needs somewhere to keep the last good answer:
**ElastiCache** (Valkey or Redis) if you want it in memory and shared,
**DynamoDB** with a TTL if you want it durable and cheap, and honestly a local
in-process cache if there is one instance. Choose by how bad a stale answer is,
not by which sounds more serious.

Where the choice genuinely matters: if the fallback is "queue it and do it
later", that is **SQS**, and the user-facing response changes from an answer to
an acknowledgement — a product change you should name out loud.

For the breaker, note what AWS gives you free: an **Application Load Balancer**
health check will take an unhealthy instance out of rotation, which is a coarse
breaker at the instance level, and **App Mesh** or a sidecar does it per
dependency. Neither replaces the in-process breaker around a third-party API,
because the thing failing is not yours.

**What productionising it means**

Every fallback can be forced on demand, and you have forced each one at least
once. The breaker's state is visible in telemetry rather than inferred. Stale
answers are labelled as stale where a person can see it. And the priority
classes exist in code, not in a document.

**The learning**

Availability is not a property you add, it is a set of decisions about what to
give up and in what order. A system with no fallbacks has made all of those
decisions by default, and the default is always "stop".

**How you would know it is wrong**

- Block the dependency at the network level and use the product for five minutes. Write down what you experienced.
- Make the dependency slow rather than absent — that is the harder case and the commoner one.
- Force each fallback deliberately. Any you cannot force is untested.
- Check whether a stale answer is identifiable as stale, from outside.
- Shed load and confirm the *low* priority class is what suffered.

**Stage it**

1. The failure inventory, with what the user currently sees.
2. Fallbacks, each forceable on demand.
3. Timeouts and the breaker, with all three states demonstrated.
4. Priority classes and shedding, verified from the user's side.

---

## 2. Twenty deploys a day

*Shipping becomes so unremarkable you would do it on a Friday afternoon.*

**Build**

A pipeline where merging means deploying, the infrastructure is described in the
repository, releases are separate from deploys, and rolling back is one action
you have actually taken.

**The thought process**

The first decision is **what gates a merge**, and the temptation is everything.
Every gate costs time on every change, forever, and a slow pipeline is why
people batch up work — which is the thing that makes deploys dangerous. So the
question is not "what could we check" but "what has actually broken, and what is
the cheapest check that would have caught it".

Second: **deploy and release are different events.** Getting code onto machines
and turning a feature on for people are separate decisions, and separating them
is what makes rollback cheap — a flag flip is seconds where a deploy is minutes.

Third, the one that is easy to skip: **the pipeline is the most privileged thing
you own.** It holds credentials and runs code from pull requests. Before adding
capability to it, ask what somebody who controlled a pull request could do with
that capability.

**How to organise the prompts**

```
Write my deployment as stages, with what each stage can access.

For each stage, tell me what somebody who controlled the contents of a
pull request could do with that access. Rank by damage.
```

That second question reliably finds a step with more power than it needs.

```
Now the infrastructure as code. Everything the running system needs,
described in the repo. Then tell me what is currently in my account that
this description does NOT cover.
```

The gap list is the real output. There is always something created by hand.

```
Implement one feature behind a flag, deployed dark. Show me the deploy
happening with the feature off, then the release as a flag change with
no deploy.
```

```
Roll back. Not in theory — deploy, roll back, and show me the previous
version serving. Then tell me what in my system does NOT roll back.
```

**On AWS**

**GitHub Actions** with an **OIDC role** rather than stored access keys. That
one change is the single biggest security improvement available to a small
project: no long-lived cloud credential exists to leak. **CodeBuild** earns its
place when you need to be inside a VPC or want a bigger machine than a hosted
runner; **CodePipeline** when you want approval gates and a visual pipeline
across accounts.

Infrastructure as code: **Terraform** or **OpenTofu** if you want to be
portable, **CDK** if you are staying on AWS and would rather write a programming
language than a configuration one, **CloudFormation** underneath both. The real
decision is state — where the state file lives and who can write it — and an
**S3** bucket with versioning plus a lock is the minimum that stops two people
destroying each other's work.

Progressive delivery: **CodeDeploy** does canary and linear shifts for ECS and
Lambda without you building anything, which is the strongest argument for it.
Feature flags can be **AppConfig** (with its own gradual rollout and a
built-in rollback on a CloudWatch alarm) or a third-party service; the AppConfig
argument is that the rollout and the alarm live in the same place as your
metrics.

**What productionising it means**

Merging deploys, and nobody runs a command by hand. You destroyed the
infrastructure and rebuilt it from the repository at least once. Rollback has
been done, deliberately, and timed. No long-lived cloud credential exists in CI.
And every flag has an owner and a removal date, because a flag without one is a
permanent fork in your code.

**The learning**

Deploy frequency is a safety property, not a speed one. Small changes shipped
often are easier to judge, easier to revert and easier to attribute — and the
reason teams batch up work is almost always that their pipeline is slow, which
makes the pipeline a safety problem.

**How you would know it is wrong**

- Deploy a version that crashes on start. Something must catch it before it takes traffic.
- Destroy and rebuild from the repo in a scratch account or region.
- Revoke whatever credential CI uses. The deploy must fail, and then work again once rotated.
- Roll back and time it. That number is your worst-case recovery.
- Find your oldest feature flag and ask who owns it.

**Stage it**

1. Merge deploys, one environment, nothing by hand.
2. Infrastructure in code, with the gap list closed.
3. Deploy dark, release by flag, both demonstrated.
4. A rollback you have performed and timed.

---

## 3. Debuggable at three in the morning

*Somebody who did not build it can find out what happened.*

**Build**

Telemetry good enough that an unfamiliar person can answer "what happened to
this request?" without adding a log line and redeploying — plus an SLO, an alert
that fires once and usefully, and a measured detection time.

**The thought process**

Start with the question, not the tooling: **what will you want to ask at 3am?**
Usually "is it everyone or one person", "since when", "what changed", and "which
component". Instrument to answer those four, and you will have skipped the phase
where you collect a lot of data that answers none of them.

Then the trap that gets everybody: **cardinality**. A label with a user id in it
multiplies your time series by your user count, and the bill arrives before the
insight does. The rule worth internalising early is that high-cardinality
identifiers belong on traces and in logs, not on metrics.

Third: **the alert is a design problem, not a threshold.** An alert that fires
for every blip trains people to ignore it, and then a real one arrives inside
that noise. Decide what is worth waking somebody for, in advance, while calm.

**How to organise the prompts**

```
Here is my system. I want to answer four questions during an incident:
is it everyone or one person, since when, what changed, and which
component.

Tell me the minimum instrumentation that answers all four. Then tell me
what I would be collecting that answers none of them.
```

```
Add tracing so one request is followed end to end, including the
outbound call, with a correlation id that appears in every log line for
that request.

Show me a single trace that crosses every component.
```

```
Define one SLO for the thing users care about. Write the error-budget
policy as rules — what happens at 75% spent, what happens at 25% — and
tell me what would have to be true for me to actually honour it.
```

```
Now break it on purpose and time me. From the moment it broke to the
moment something told me: what is the number, and where did the time go?
```

That number is the deliverable. Everything else in this project exists to make
it smaller.

**On AWS**

Instrument with **OpenTelemetry** rather than a vendor SDK, then choose where it
goes. **AWS Distro for OpenTelemetry** as the collector, with
**CloudWatch** plus **X-Ray** as the destination if you want everything inside
AWS and billed in one place. The argument for a third-party backend is query
power; the argument for CloudWatch is that alarms, dashboards and logs are
already there and already integrated with the things that would act on them.

Watch the cost shape: CloudWatch bills custom metrics per metric per month, so
cardinality is money, not just performance. **CloudWatch Logs Insights** for
ad-hoc queries, with a retention policy set deliberately — the default of
"forever" is a slowly growing bill nobody notices.

For the alert itself: a **CloudWatch alarm** on the SLO's burn rate, into
**SNS**, into wherever you actually look. And alarm on **missing data**, not just
on breaching thresholds, because a component that stopped reporting looks
identical to one that is healthy.

**What productionising it means**

A person who did not build it can follow one request end to end. The SLO has a
written policy that somebody has agreed to. Alerts fire once per incident rather
than once per minute. The telemetry bill is known and bounded. And the detection
time has been measured, not estimated.

**The learning**

The gap between "it broke" and "we knew" is the number that decides how bad an
incident is, and it is the only part you can shrink before anything goes wrong.
Everything else in observability is in service of that one measurement.

**How you would know it is wrong**

- Break something and time the gap. Then do it again after your changes and compare.
- Hand the telemetry to somebody unfamiliar and ask them to explain a slow request. Watch without helping.
- Count your active time series. Then add a label and predict the new count before looking.
- Stop a component entirely. Something must notice the silence.
- Check one trace actually crosses a service boundary rather than stopping at the edge.

**Stage it**

1. The four questions, and the minimum instrumentation that answers them.
2. One trace, end to end, with a correlation id in every log.
3. An SLO, a burn-rate alert, and a written budget policy.
4. A measured detection time, before and after.

---

## 4. The flood

*A burst of work ten times bigger than normal arrives, and the system bends.*

**Build**

Move the slow work off the request onto a bounded queue, make the work idempotent,
rate-limit the entrances, then flood it on purpose and record what broke first.

**The thought process**

The first decision: **what is the unit of work, and is it safe to do twice?**
Because it will be done twice. At-least-once delivery is what you get in
practice, so the handler has to be idempotent, and idempotency is a property of
the *data model* (a unique key, a state machine) far more than of the code.

Second: **every queue needs a bound.** An unbounded queue is not resilience, it
is a memory leak with a scheduler, and the failure it produces is the worst kind
— nothing appears wrong for hours, then everything is wrong at once and the
backlog takes a day to drain.

Third, the one people find counterintuitive: **rejecting work is a feature.**
A system that accepts everything and then collapses serves nobody. A system that
sheds the excess quickly, with an honest response, keeps working for the people
it did accept.

**How to organise the prompts**

```
I am moving this work onto a queue. List what can now go wrong that
could not go wrong before — including the silent ones: work lost, work
done twice, and a backlog growing with nobody noticing.

Do not write code yet.
```

```
Make the handler idempotent, and prove it: a test that delivers the same
message twice CONCURRENTLY and asserts the side effect happened exactly
once. Show me that test failing against the current handler first.
```

```
Bound the queue. Tell me what happens at the bound — reject, shed, or
block — and implement the one I choose. Then show me the bound being
hit.
```

```
Write a load generator that ramps until something fails, reports what
failed first and at what rate, and tells me from the DATA which
resource ran out rather than guessing from the architecture.
```

**On AWS**

**SQS** is the default and the right default: it is durable, it has retries and
a dead-letter queue, and it costs almost nothing at small volume. Why not
**EventBridge** — it routes events to targets and does not hold a backlog you
drain at your own pace, which is the property you actually want here. Why not
**Kinesis** — it is for ordered streams with multiple independent readers, and
it bills per shard-hour whether or not anything arrives.

Set two things deliberately: the **visibility timeout** longer than your
worst-case processing time (too short and the same message is handed to a second
worker while the first is still working, which is where duplicate side effects
come from), and a **dead-letter queue** with a redrive policy, so a message that
can never succeed stops being retried for ever.

Workers on **Fargate** with a service autoscaling on queue depth, or **Lambda**
with an SQS trigger and a **reserved concurrency** limit — that limit is the one
knob that stops a flood of messages becoming a flood of database connections.
That single sentence is why concurrency limits exist.

**What productionising it means**

The queue depth is a metric with an alarm, because an invisible backlog is the
whole failure mode. The dead-letter queue has something watching it. The handler
is idempotent and there is a concurrency test proving it. And you know the
breaking point, because you found it on purpose rather than in production.

**The learning**

A queue does not make work reliable, it makes work *deferred* — and it converts a
loud synchronous failure into a quiet asynchronous one. Everything you build
around it is there to make the quiet failure loud again.

**How you would know it is wrong**

- Deliver the same message twice, concurrently. The effect must happen once.
- Stop the worker and keep submitting. Does anything tell you the backlog is growing?
- Fill the queue past its bound. Confirm the behaviour is the one you chose.
- Count actual outbound requests during a retry storm, from the outside.
- Check the dead-letter queue has a consumer or an alarm. An unwatched DLQ is a folder of lost work.

**Stage it**

1. Work moved off the request, nothing bounded yet.
2. Idempotency, with the concurrent-duplicate test.
3. Bounds, rate limits and the chosen rejection behaviour.
4. A deliberate flood, with the breaking point and the first thing that broke written down.

---

## 5. An AI feature you can defend

*A model does something useful in your product, and you can prove it is any good.*

**Build**

One small AI feature — a summary, a suggestion, a classification — plus the
evaluation harness, the guardrails, and the cost and latency budget that make it
defensible. The feature is perhaps a fifth of the work.

**The thought process**

Start with the decision most people skip: **should this be a model at all?**
Stable rules, fixed formats and exact matching belong in code — microseconds,
free, testable. A model earns its place where there is genuine ambiguity or
judgment. Write the answer down, honestly, because "we used AI" is not a
feature.

Then the thing that makes it engineering rather than a demo: **error analysis
before metrics.** Read thirty real outputs by hand, group the failures into a
taxonomy you derive from what you see, and count. Failures cluster. You will
find that a handful of categories account for most of them, and fixing one moves
the number more than any prompt tinkering.

Third, and it is architectural rather than textual: **what can this reach?**
If the feature sees private data, reads content from outside, and can send
something outward, you have built an exfiltration path, and no instruction in
the prompt closes it. Cut one of the three for that session.

**How to organise the prompts**

```
Here are 30 real outputs with their inputs.

Do not score them. Read them and group the failures into categories you
derive from what you see, not from a list I gave you. Report counts and
two examples each.

Then tell me which single category, fixed, removes the most failures.
```

```
Turn that category into a binary pass/fail eval with an explicit rule.
Write three cases you expect to FAIL now, and show me them failing.

If everything passes, tell me the eval is too easy rather than
reporting success.
```

```
Here is what the feature can read and which tools it can call. Work out
whether all three legs of the trifecta are present — private data,
untrusted content, outbound capability. If they are, show me the
concrete path, and do not propose a filter as the fix.
```

```
Measure cost per task, not per call, on the worst case: longest input,
most retries. Then put a hard cap in code and show me it firing.
```

**On AWS**

**Bedrock** is the reason to do this on AWS: the model call happens inside your
account, with **IAM** controlling who can invoke which model, **CloudWatch**
logging invocations, and **Bedrock Guardrails** as a configurable policy layer
that sits outside your prompt. Calling a provider's public API directly is
simpler and entirely reasonable; the Bedrock argument is governance — one place
that says who may call what, and a log of it.

For retrieval, the honest ladder: start with **PostgreSQL** and `pgvector` on
**RDS**, because one datastore you already run beats a new one. **OpenSearch
Serverless** when you want hybrid keyword-and-vector search with a reranker and
your corpus has outgrown a table. **Kendra** when the value is connectors to
enterprise sources rather than the retrieval itself. Do not start at the top.

Cost control is the part people leave out: **Budgets** with an action, per-key
tagging so you can attribute spend to this feature, and **provisioned
throughput** only once traffic is steady enough to predict. A runaway agent loop
is not a probabilistic risk, so the cap belongs in code as well as in a budget
alert.

**What productionising it means**

There is an eval set built from real failures, and it does not pass 100% —
because a suite that always passes is not challenging the system. If a model
judges, you know its agreement rate with your own labels. Cost per task is
capped and you have tested the cap by hitting it. Turning the model off leaves
the product usable. And the trifecta analysis is written down with the leg you
cut named.

**The learning**

The model call is the easy part and the cheap part. The engineering is the
evaluation, the guardrail and the budget — and the reason most AI features are
undefendable is that all three were left until after launch.

**How you would know it is wrong**

- Replace the model with a stub returning a fixed string. Anything in your eval that still passes was measuring nothing.
- Put instructions in the untrusted content and see what happens. Then check whether the architecture, not the prompt, limits the damage.
- Measure judge-human agreement on a labelled set, or state plainly that you have no judge.
- Compute cost on the worst case and confirm the cap stops it.
- Turn the model off and use the product. That is your degradation path whether you designed it or not.

**Stage it**

1. The written answer to "should this be a model", and thirty outputs read by hand.
2. The failure taxonomy and an eval that can fail.
3. Guardrails and the trifecta analysis, with a capability removed.
4. Cost and latency budgets, capped in code and tested by hitting them.
