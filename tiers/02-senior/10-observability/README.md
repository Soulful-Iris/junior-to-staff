# 10 · Observability

> Senior tier · feeds **P2 (it survives)**

## The one-liner

Monitoring answers the questions you thought of in advance: is it up, is it
slow, is the disk full. Observability is being able to answer the question you
did not think of — at 3am, from evidence the system already recorded, without
shipping new code first. The senior skill is choosing what to record, and at
what cost, so one failing request can be found and explained after the fact.

## The failure it prevents

A user writes in: "saving has failed for me all week." Every dashboard is
green. CPU is flat. The error-rate chart shows 0.4%, which is normal, because
it is an average over everyone and she is one person.

The logs contain `save failed` three thousand times, with no user id and no
request id, so you cannot say which are hers or what happened just before each
one. The save path calls another service; there is no trace, so that hop's time
is invisible inside the total.

Four hours of ssh and grep later you find it: her account is far larger than
most, one query flips to a bad plan past a certain row count, and only on one
replica. Nothing here was unknowable — the system knew which requests were
hers, how long each hop took, which replica answered. It never wrote any of it
down in a form that could be asked.

The same day with observability: search traces for her user id, open the
slowest, see one span holding nine of the ten seconds, read the query from its
attributes. Ten minutes, no ssh.

Dashboards answer questions someone asked in advance. Users generate new ones.

## The mental model

### Known questions and new ones

Monitoring is a fixed set of questions asked continuously, with alerts wired to
the answers. You need it; it is how you learn *that* something is wrong.
Observability is a property of what you record: whether it carries enough
detail to answer questions nobody anticipated — *why*, for whom, since when,
after which deploy. The test is one sentence: **can you explain the last weird
thing one user experienced without deploying new code to find out?** If every
incident starts with adding a log line, you have monitoring only.

### Three signals, and where each one lies

**Metrics** are numbers aggregated over time. Cheap to store, fast to query,
the right thing to alert on. They lie by aggregation: the mean hides the p99,
and pre-aggregation throws the individuals away at write time, so no metric can
ever tell you *which* request was slow.

**Logs** are events with arbitrary detail. They lie by omission and
disconnection: they contain only what someone thought to write, and without a
shared id a log line is a diary entry — true, timestamped, about somebody,
connectable to nothing. A log is only telemetry when it is structured (keys and
values, not prose) and carries the id of the request that caused it.

**Traces** follow one request across services: a tree of spans, each a timed
operation with attributes. The signal that answers "where did the time go" for
a single request. Traces lie by absence: sampling may have dropped the one you
need, and an uninstrumented hop shows as a gap that gets blamed on the caller.
A trace that stops at a service boundary because nobody propagated the context
is two traces, and says nothing about the boundary — where the problem usually
is.

### The substrate is a standard now

OpenTelemetry graduated from the CNCF in May 2026 (announced 21 May; checked on
opentelemetry.io, 2026-09-21): one API and wire format for traces, metrics and
logs, with the vendor plugged in at the exporter. Instrument against the
OpenTelemetry API, never a vendor SDK — instrumentation ends up in every file
of every service, and it is the part you cannot afford to rewrite when you
change vendors. A fourth signal, profiles, was in alpha as of the graduation
announcement; watch it, don't build on it yet.

### The cardinality trap

A metric is not one thing in storage. It is one **time series per combination
of label values**, and every new label multiplies every series that already
exists.

![One metric multiplying into time series as labels are added: no labels is one series, a method label with four values makes 4, a route label with twenty values makes 80, a status-class label with five values makes 400, and a customer id with ten thousand values makes 4,000,000 — drawn as a bar running off the chart](../../../assets/diagrams/cardinality-explosion.svg)

Storage — and most vendor bills — scale with active series, not with traffic,
which is how one deploy adding one label doubles a bill overnight. So: metric
labels are for **bounded** dimensions you would group by (method, route, status
class, region). Anything unbounded — user id, request id, raw URL — belongs on
spans and logs, which are events you sample and query, not series you multiply.

There is a serious counter-argument, usually called wide events or
"observability 2.0": emit one wide structured event per request, with dozens of
fields, into a columnar store, and derive metrics and traces at query time —
high cardinality stops being a trap and becomes the point. It is contested:
pre-aggregated metrics stay the cheapest thing to alert on continuously; wide
events keep the ability to ask about individuals; many teams run a hybrid. Not
contested: unbounded labels on a conventional metrics backend is a mistake with
an invoice attached.

### Sampling, and the part nobody teaches

At volume you cannot keep every trace. **Head sampling** decides at the start —
cheap and stateless, but blind: it cannot keep all the errors and slow
requests, because they have not happened yet. **Tail sampling** decides once
the trace is complete — keep all errors, everything over the latency target, 1%
of the boring rest — which is the policy you actually want. Two consequences,
and the second quietly ruins dashboards:

1. Tail sampling is **stateful**. The decision needs the whole trace, so every
   span with the same trace id must arrive at the same collector instance or
   traces fragment. OpenTelemetry's guidance (checked 2026-09-21) is a
   two-layer topology: a stateless first layer that load-balances **by trace
   id**, then a layer that buffers complete traces and applies the policy. The
   policy without the routing layer looks fine right up until there is more
   than one collector.
2. **Span metrics must be computed before the sampling decision.** Tail
   sampling keeps all the errors and a sliver of the successes; any rate
   derived from the survivors inherits that bias — error rate reads far above
   truth, request rate reads low, latency histograms skew slow. Compute rate,
   error and duration metrics from the full span stream in the first layer, and
   let only the traces be dropped.

### Where to point it

In order: the **request** at the edge (rate, errors, duration); every
**dependency call**, where the timeouts, retries and mystery gaps live; the
**queue** — depth *and* age of the oldest item, because a queue of three items
looks healthy while its oldest has been stuck for forty minutes; and the thing
**users actually feel**, which is usually none of these — "link added until
title visible", end to end. Instrument the user's unit of work, not just your
process.

## What good looks like

- Every request gets an id at the edge, and it is on every log line, span and
  error report the request causes.
- One trace id survives the whole journey: edge, backend, across the queue,
  into the worker.
- Alert to offending traces to one request's logs in a few clicks. No ssh in
  the incident story.
- Application code imports only the OpenTelemetry API; the vendor is named in
  one config file.
- Someone can state the active-series count, and every custom metric's labels
  are enumerated with their value counts.
- The sampling policy is written down: what is always kept, what fraction of
  the rest, where the decision physically happens.
- The telemetry bill is a reviewed line item, and the top three costs can be
  attributed to named metrics or log streams.

Done badly, you see:

- Dashboards green during an outage users can feel.
- Logs as prose — "something went wrong in handler" — no ids, no fields.
- `user_id` as a metric label. The bill doubles overnight, or the vendor drops
  series at a limit and the charts develop quiet holes.
- Traces that end at every service boundary, so each downstream call is a
  mystery gap attributed to the wrong team.
- A sampling rate nobody can state: 100% in dev, some default in prod.
- Alerts on causes (CPU high) rather than symptoms (users waiting): the pager
  fires for what nobody feels and sleeps through what everybody does.

## Ask Claude for this

**Request 1 — instrument a service, portably, cardinality conversation forced**

```
Instrument this service with OpenTelemetry: traces, metrics, logs.

Rules:
- Application code imports the OpenTelemetry API only. No vendor
  SDK outside one exporter config file.
- Propagate trace context across every boundary: inbound HTTP,
  outbound HTTP, the database, and the queue in both directions.
- Every log line is structured and carries the trace id.
- List every metric you created with its labels, and for each label
  state the number of possible values. Flag anything unbounded.

Then show me one request's story end to end: its trace, its spans,
and the log lines sharing its trace id.
```

*Why it is asked that way:* the API-only rule keeps instrumentation portable,
and it is the rule generated code breaks first. Label enumeration forces the
cardinality conversation before the first deploy rather than on the first
invoice. "One request's story" is the acceptance test: the entire point is
following a single request, so the work must demonstrate that.

*What you should get back:* a service where the queue consumer's spans share or
explicitly link to the producer's trace id. That hop is the one automatic
instrumentation misses most, because the context must ride inside the message.

*Push back on:* any metric labelled `user_id`, `request_id` or raw URL — those
belong on spans; an error logged without an id; a hand-rolled "portability
wrapper" around a vendor SDK, which is the vendor SDK with extra steps.

**Request 2 — a tail-sampling design that must show its topology**

```
Design tail sampling for this system at <N> requests/second.

Policy: keep 100% of traces containing an error, 100% slower than
<threshold>, 1% of the rest.

Show the collector topology as configuration, not prose. The policy
needs every span of a trace in one place: show how spans reach the
same collector instance when there are three collectors, and what
happens to in-flight traces when one restarts.

State where request rate, error rate and latency metrics are
computed, and why the sampling decision cannot bias them.
```

*Why:* "configuration, not prose", because the failure lives in the topology
and prose happily describes a single collector as if it scaled. The restart
question surfaces the statefulness. The last paragraph is the span-metrics trap
made explicit.

*What you should get back:* two layers — a stateless layer routing by trace id,
then the tail-sampling layer — with metrics computed before the sampler, and an
honest note that a restarting collector loses what it was buffering. If you get
one collector and "scale horizontally later": it cannot, not without the
routing layer. That is the wrong answer looking reasonable.

**Request 3 — the unanticipated-question drill**

```
Here are my instrumentation, dashboards and alert rules: <paste>.

Invent five questions a user or an engineer could plausibly ask
that none of my dashboards answer — about one specific user, one
request, or one hour. For each, say whether my recorded telemetry
could answer it, and exactly what is missing if not.
```

*Why:* observability is defined by unanticipated questions, so test it with
some. Requiring questions about individuals stops the model asking aggregate
questions your dashboards already handle.

*Push back on:* five questions that all turn out answerable. Either your
telemetry is genuinely good or the questions were soft — ask for five harder
ones and find out which.

## How you would know it is wrong

1. **Run the fire drill.** Have someone break one thing on purpose — hang a
   dependency, slow one query, poison one queue message — and time yourself
   finding it using only telemetry. No ssh, no grepping boxes. Ten minutes is a
   pass. If the answer came from anywhere but your instruments, they failed,
   whatever the dashboards say.
2. **Count your active time series.** If nobody knows the number, look it up —
   every backend exposes it. Then add one label to one metric, predict the new
   count, and check. Unable to predict means you do not control the bill; off
   by 10x means the label was not bounded.
3. **Follow one real request across the boundary.** Take a request id from the
   edge and confirm its trace reaches the worker on the far side of the queue,
   same trace id. A trace that stops at the boundary means propagation is
   broken and every cross-service question is currently unanswerable.
4. **Pull one error log at random** and try to reach the request that caused it
   — the trace, the user, the response they saw. If you cannot, the correlation
   id is missing or decorative.
5. **Check a dashboard rate against the unsampled truth.** Compare your
   dashboard's error rate with the raw pre-sampling error count for the same
   hour. Divergence means metrics are computed after the sampler, and every
   rate on that dashboard is a picture of your sampling policy.
6. **Attribute the bill.** Tie the top three telemetry costs to named metrics
   or log streams. If you cannot, that is not a budget, it is a leak with a
   monthly statement.

## Your slice of the project

On **P2**, the reading list from P1 gets instrumented. This is the "can you fix
it at 3am" half of that project's question.

- OpenTelemetry tracing on inbound requests, database calls, the outbound URL
  fetch, and the deferred title-fetch path in both directions.
- All logs structured, each carrying the trace id.
- Metrics for the request trio (rate, errors, duration, by route and status
  class), plus queue depth and the age of the oldest pending fetch.
- A written sampling policy. At your volume it may honestly be "keep
  everything" — write down why, and the number at which that stops being true.
- A series inventory: every custom metric, its labels, their value counts, the
  total.

**Acceptance criteria:**

- The fire drill passes: someone picks one of three planned failures (kill the
  database, hang the fetch, stall the queue) without telling you which, and you
  name it from telemetry alone in under ten minutes.
- Pick any failed fetch in the UI and produce its trace and logs by id, in one
  search.
- Break context propagation on purpose — drop the traceparent header on one hop
  — and watch the trace split in two. Proof you can tell propagation from
  coincidence.
- You can state your active series count, and what adding `tag` as a label to
  the request metric would do to it, before trying it.

## Words you now own

- **monitoring** — asking known questions continuously and alerting on the answers.
- **observability** — recording enough detail to answer questions you did not anticipate.
- **time series** — one stored stream of values per combination of metric name and label values.
- **cardinality** — how many distinct values a label has; the multiplier on series count and bill.
- **structured log** — an event as keys and values rather than prose, so it can be queried.
- **correlation id** — the id, usually the trace id, connecting everything one request caused.
- **span** — one timed operation with attributes; a trace is the tree of spans for one request.
- **context propagation** — carrying the trace id across every boundary, queues included.
- **head sampling** — deciding whether to keep a trace at its start. Cheap, blind to outcome.
- **tail sampling** — deciding once the trace is complete, so errors and slow traces are always kept. Stateful.
- **collector** — the pipeline process between services and backend, where sampling and routing live.
- **wide event** — one rich structured event per request, from which metrics and traces can be derived at query time.

---

**Not covered here:** what to do when the telemetry says something is wrong —
SLOs, error budgets, alerting policy, being on call — is the reliability
section's job; this one is about being able to see. Continuous profiling, the
fourth signal, is real but young. Front-end and real-user monitoring have their
own tooling. Audit logs are a security artifact with different retention rules,
not an observability signal.
