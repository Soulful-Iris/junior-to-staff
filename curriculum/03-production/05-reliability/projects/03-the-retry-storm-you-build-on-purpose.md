# 3. The retry storm you build on purpose

## What you are building

> Investigate a save operation that explodes into dozens of dependency calls during an outage. The browser, API handler and SDK each retry independently. Reduce amplification while retaining a safe response to transient failures.

**Working contract:** One layer owns the retry budget for a logical operation. Count total attempts explicitly, preserve the original deadline and operation identity, and retry writes only under a verified idempotency/reconciliation contract.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Three layers × three total attempts each | Worst-case 3³ = 27 dependency attempts for one user action. |
| Three retries plus initial attempt at each layer | Four total attempts/layer gives 4³ = 64, not 27. |
| 1,000 clients with identical backoff | Even a bounded attempt count can create synchronized recovery bursts; spread timing with jitter. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/03_the_retry_storm_you_build_on_purpose.py
```

[Open the starting code](../../../../examples/architecture-starts/03_the_retry_storm_you_build_on_purpose.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| retry_policy | owner_layer,max_total_attempts,deadline | One bounded operation budget. |
| attempt_record | operation_id,attempt,reason,scheduled_delay | Explains amplification and exhaustion. |
| effect_identity | operation_id,payload_hash,provider_key | Deduplicates safe external writes or supports reconciliation. |

## AWS implementation

![3. The retry storm you build on purpose: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/03-the-retry-storm-you-build-on-purpose.svg)

The API and SDK are separate retry layers even when they run in one process. Explicit ownership makes the worst-case dependency load calculable.

## Build it in this order

### 1. Measure actual amplification

Attach one logical operation ID across browser, API and SDK. Count attempts at each layer and compare to user actions. Inspect SDK defaults rather than assuming the retry loop visible in application code is the only one.

### 2. Assign one retry owner

Disable or constrain nested retries so the total budget is explicit. Use a maximum total-attempt count, shared deadline and bounded exponential backoff with jitter. Stop when Retry-After exceeds remaining time; do not start work that cannot contribute to the response.

### 3. Preserve write identity

Reuse one provider idempotency key for an exact write intent and reject changed payload under that key. A timeout after a successful provider commit is unknown, not definitely failed. Reconcile before switching providers or creating another operation.

### 4. Observe recovery under load

Use a finite local fault window and compare request count, attempt timing, useful throughput and queue age. A circuit breaker can reduce doomed calls, but half-open probes must also be bounded so recovery does not release every waiting client at once.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| SDK settings | Set retry mode/count deliberately and document whether configuration means retries or total attempts. |
| Timeouts | Share the original deadline and cap queue/backoff time; cancel abandoned work where supported. |
| Provider state | Persist operation identity before the call and retain it for the required retry horizon. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The two configurations produce 27 and 64 attempts; a two-second Retry-After cannot fit 500 ms remaining. |
| Lose a successful write response | The retry uses the same intent identity and resolves the original effect. |
| Recover 1,000 clients together | Jitter and bounded probes spread attempts within the configured budget. |

## The next design decision

The provider’s idempotency retention expires before your retry horizon. Shorten the automatic retry window or add a provider lookup/reconciliation path; do not assume an old key remains deduplicated forever.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · Every client starts together

**Changed requirement:** A dependency recovers and 1,000 clients have identical backoff. Does the request count alone reveal the risk? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Plot attempt timestamps as well as counts. Full jitter spreads retries, while an admission limit bounds total downstream concurrency; jitter does not create extra capacity or serialize one key.

</details>

## Follow-up 2 · The first write succeeded

**Changed requirement:** The provider performed a write before the response disappeared. What determines retry safety? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

For local effects, atomically persist operation identity, payload and result with the effect. For a remote effect, use its idempotency/status protocol or reconcile an unknown outcome. Compare duplicate conflicting payloads before replay.

</details>

## Supplied mechanism practice

- [Runnable reliability arithmetic and incident lab](../labs/reliability/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
