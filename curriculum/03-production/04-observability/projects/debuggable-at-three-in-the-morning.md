# 3. Debuggable at three in the morning

## What you are building

> Prepare a reading-list service for an unfamiliar on-call engineer at 03:00. Failures rise after a configuration change, but the responder needs to determine scope, the failing phase and the fastest reversible mitigation without redeploying instrumentation.

**Working contract:** Provide request/outcome metrics, correlated diagnostic events, selected traces and release/configuration identity. The runbook begins from user impact and links to evidence for scope, change and dependency behavior.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Impact starts 03:00:00; metric at 03:00:30; alert at 03:01:10 | Detection is 70 seconds: 30 seconds collection plus 40 seconds evaluation/delivery. |
| One affected user among 100,000 | Global averages may hide impact; use targeted logs/traces and bounded cohort dimensions. |
| Async job after HTTP response | Preserve request→job→attempt identity; one HTTP span cannot cover the whole lifecycle honestly. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/debuggable_at_three_in_the_morning.py
```

[Open the starting code](../../../../examples/architecture-starts/debuggable_at_three_in_the_morning.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| service_overview | eligible,outcome,latency,queue_age | User impact and operating saturation. |
| release_context | commit,config_version,started_at | What changed around the incident. |
| request_story | request_id,job_id,attempt_id,phase | Correlated synchronous and asynchronous evidence. |

## AWS implementation

![3. Debuggable at three in the morning: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/debuggable-at-three-in-the-morning.svg)

Observability is useful when it answers a responder’s concrete decision. Collectors and dashboards transport/present evidence, while application instrumentation supplies the missing causal boundaries.

## Build it in this order

### 1. Instrument one real user journey

Record save/list outcomes and complete-request latency, then add dependency and pool/queue phases. Include deployed commit and applied configuration version in diagnostic context. Keep aggregate counters unsampled; traces explain selected requests.

### 2. Build an impact-first dashboard

Show request success, tail latency, queue age and saturation for bounded route/tier/region groups. Provide a query path from a user-supplied response ID to redacted logs and traces. Do not create a permanent metric label for every user or request.

### 3. Write an executable runbook

Start with confirm impact, identify scope, inspect recent changes, locate the constrained dependency and choose a reversible mitigation. Give exact dashboard/query/configuration links and the expected observation after each action. An instruction to check logs is not enough.

### 4. Keep telemetry failure visible

Track collector/export failures and last-observed data independently. Distinguish no eligible traffic from missing instrumentation. Preserve bounded local buffering and dropped-event counters so diagnostic outages do not exhaust application memory.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Telemetry access | Restrict diagnostic readers and redact tokens/content; preserve enough IDs for correlation. |
| Metric dimensions | Route, outcome, tier and region are bounded; user-specific investigation uses queries. |
| Recovery access | Keep configuration rollback and runbook access available when the normal app is failing. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Detection is 70 seconds, not 30; request r7 links to worker attempt 2. |
| Fail only one cohort | The responder can isolate it without adding a new metric label per user. |
| Stop telemetry export | Missing evidence is visible separately from healthy application traffic. |

## The next design decision

The mitigation lowers alert delay but leaves backlog drain unchanged. Report faster detection separately from recovery; do not claim the entire incident became shorter without measuring it.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · An async boundary appears

**Changed requirement:** The user request ends before the worker starts. Which trace relationship do you preserve? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Link the enqueue span to the job and each worker attempt. Show queue wait separately from execution; a retry must not overwrite the first attempt’s evidence.

</details>

## Follow-up 2 · Telemetry disappears

**Changed requirement:** The collector fails while the application continues. How does the responder distinguish healthy traffic from silence? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use an independently observed heartbeat and delivery/drop counters, and state what remains unknowable. Do not score undefined good/total as 100% availability.

</details>

</details>
