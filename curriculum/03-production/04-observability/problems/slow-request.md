# Slow request: the healthy average hid a timeout

## What you are building

> Diagnose an order API where most requests are fast but customers report intermittent two-second waits. The database query itself looks quick; four percent of requests wait for a connection before the query even begins.

**Working contract:** Instrument the complete request with queue, connection acquisition, query and downstream spans. Use all eligible request outcomes for latency/error metrics; sampled traces explain examples and do not supply the request denominator.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 8,000 requests/minute | About 133 requests/s average; bursts and concurrent occupancy matter for pool sizing. |
| 4% wait for a database connection | p95 can look healthy while p99 is poor; inspect tail latency and pool-wait duration. |
| Two-second end-to-end deadline | Every queue and downstream call consumes the same budget; independent two-second timeouts exceed it. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/slow_request.py
```

[Open the starting code](../../../../examples/architecture-starts/slow_request.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| request_metrics | route,outcome,duration_histogram | Complete eligible denominator and tail distribution. |
| trace_spans | trace_id,parent_id,phase,duration | Causal timeline for selected requests. |
| pool_state | active,idle,waiting,acquire_timeout | Evidence connecting latency to resource contention. |

## AWS implementation

![Slow request: the healthy average hid a timeout: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/slow-request.svg)

The collector transports evidence; it does not decide what counts as a request. Instrumenting pool acquisition exposes waiting that a query-duration-only dashboard misses.

## Build it in this order

### 1. Reproduce one slow request locally

Add a request ID and monotonic timestamps around admission, connection acquisition and SQL execution. Use a deliberately small pool and a long-lived transaction to create waiting. Capture a single request timeline before changing pool size.

### 2. Separate denominator from explanation

Record a histogram and outcome counter for every eligible request. Sample traces with an explicit policy and retain slow/error examples when possible. Never compute a service success rate by counting only the traces retained by sampling.

### 3. Fix the constraining resource

Inspect transaction duration, leaked connections and downstream concurrency. A larger pool can merely move waiting into the database and increase contention. Bound acquisition time and propagate the remaining request deadline so work stops when the response can no longer succeed.

### 4. Compare after the change

Repeat the same arrival pattern and report p50/p95/p99, pool wait, database active connections and completed throughput. Keep the slow trace as evidence of causality rather than presenting a dashboard screenshot without a workload description.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Application pool | Explicit maximum connections and acquisition deadline; total fleet pools must fit the database budget. |
| Telemetry | Bound label cardinality and scrub SQL parameters/tokens; do not sample away aggregate request counters. |
| Deadline | Use monotonic elapsed time locally and propagate a bounded remaining budget across service calls. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | p95 is 80 ms while p99 is 1,900 ms; most slow time is pool waiting. |
| Hold a database connection | The acquisition span grows even if the eventual SQL is fast. |
| Reduce leaked/long transactions | Tail latency improves without assuming an unlimited database pool. |

## The next design decision

Only one tenant produces the slow tail. Add bounded tenant-tier or targeted diagnostic analysis without turning every tenant and request ID into permanent metric labels.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



Constructed exercise. Assume 8,000 requests/minute, 4% of requests wait for a database connection, and a 2-second user-facing deadline. A distributed trace is a sample of a request, not a fleet-wide frequency estimate.

| Request | Observed path | Expected interpretation |
|---|---|---|
| A | queue 10 ms + DB 30 ms + provider 40 ms | Healthy baseline |
| B | queue 1.7 s + DB 30 ms + provider 40 ms | Wait dominates; provider average is irrelevant |
| C | provider 1.2 s + two retries of 1.2 s | User deadline exceeded; retry budget is misconfigured |
| D | no trace sampled, many clients fail | Metrics and logs still reveal scale of the incident |

## Partition elapsed time

At the ingress, record a trace ID and deadline. Propagate both through API, database calls, and provider requests. Use bounded metric labels such as route and status class. Spans may include a permitted pseudonymous tenant/user ID when diagnosis requires it; define indexing, sampling, retention and access controls. Never record secrets or raw sensitive URLs. Compare end-to-end latency histograms by endpoint and tenant class to selected exemplar traces. Distinguish pool wait, network, server time, retries, and time spent waiting in a queue. An average of 40 ms from a provider does not explain your 9-second P99 or exonerate your retry policy.

## Put the AWS names on the boxes

**Why these boxes, and what changes the choice:** CloudWatch holds fleet-level denominators and tail latency by route; X-Ray or an OpenTelemetry-compatible tracing stack identifies spans and queue wait. ALB timing is a separate boundary. A trace sample cannot substitute for complete request metrics.



**Senior follow-up:** Sampling drops the failing request. Which RED metrics (rate, errors, duration) and structured logs can still show the blast radius? Alert on an error-budget burn or bounded tail-latency objective with low-traffic safeguards; include the deploy marker.

**Staff follow-up:** Three teams own different spans. Define trace context/version compatibility and the on-call handoff. Show how you would tell a local pool exhaustion from a downstream outage before rolling back or scaling the wrong component.

**Practice artifact:** Annotated trace waterfall, before/after request path, alert query including numerator and denominator, and a five-minute incident decision memo.

**AWS translation:** OpenTelemetry or X-Ray-compatible trace context across services, CloudWatch metrics/logs for fleet denominators, and explicit pool/queue wait instrumentation. A successful sampled trace does not prove all users are healthy.

**Source note:** Constructed numbers. The exercise practices causal diagnosis after the chapter's logs, metrics, and traces lesson.

</details>
