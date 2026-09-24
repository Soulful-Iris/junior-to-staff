# 5. The failure that will not recover

## What you are building

> Diagnose a service that stays slow after its original traffic spike ends. Expired requests keep retrying and occupy slots needed for new work. The incident response must stop the sustaining loop and demonstrate enough spare capacity to drain useful backlog.

**Working contract:** Recovery requires arrivals below safe useful completion capacity. Separate stale disposable work from business obligations that still need reconciliation. Measure backlog age and net drain, not only whether the original fault disappeared.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 600 useful queued jobs; 20 new jobs/s; 50 completions/s | Net drain is 30/s; ideal drain time is 20 seconds plus measured overhead. |
| 60 retry arrivals/s; 50 completions/s | Backlog still grows 10/s after the initial spike ends. |
| Cold cache: 1,000 reads/s; database capacity 100/s | Unbounded cache bypass preserves the outage by overloading the database. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/05_the_failure_that_will_not_recover.py
```

[Open the starting code](../../../../examples/architecture-starts/05_the_failure_that_will_not_recover.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| work_inventory | job_id,deadline,business_state,repair_required | Distinguishes stale response work from unresolved effects. |
| recovery_budget | arrivals,capacity,retry_share | Explicit net-drain calculation. |
| incident_timeline | trigger,feedback_loop,mitigation,recovered | Evidence that the sustaining mechanism stopped. |

## AWS implementation

![5. The failure that will not recover: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/05-the-failure-that-will-not-recover.svg)

Recovery is a capacity inequality plus correct work classification. Queue depth falling is useful evidence only if obligations are completed or explicitly resolved, rather than silently discarded.

## Build it in this order

### 1. Identify the sustaining loop

Plot original arrivals, retries, completions and queue age separately. Find whether retry traffic, cold-cache misses, connection exhaustion or another feedback path keeps load above capacity. Removing the initiating fault is only the first observation.

### 2. Stop useless amplification

Bound retry ownership and admission, cancel expired read work and reserve capacity for useful jobs. A timed-out payment is not disposable: move it to reconciliation using its stable operation identity. Do not delete obligations to make the queue graph look healthy.

### 3. Create and measure drain capacity

Reduce arrivals or optional work until safe completions exceed admitted useful arrivals. Estimate drain time from backlog divided by net capacity, then compare actual oldest-age decay. If the estimate fails, inspect variable job cost and dependency contention.

### 4. Reopen with limits

Warm caches through a bounded origin budget and gradually restore traffic. Keep recovery controls available independently of the failing path. Record the trigger and feedback loop separately so the permanent repair addresses both.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Recovery controls | Independent admission/retry knobs with known safe defaults and owner. |
| Queue handling | Preserve logical job identity and obligations; expire only work whose contract permits it. |
| Cache warmup | Fleet-wide origin limit and bounded stale serving where allowed; no unrestricted bypass. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The healthy recovery case drains in an ideal 20 seconds; the retry loop never drains at the stated rates. |
| Turn off only the original spike | Retry-driven backlog still grows. |
| Restore a cold cache | Origin load remains below the database budget. |

## The next design decision

Job cost varies by 100×. Replace a simple job-count estimate with remaining work units and identify the oldest expensive obligation rather than predicting recovery from queue count alone.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · The cache is cold

**Changed requirement:** Cache loss sends 1,000 reads/s to a database that can handle 100/s. Should every miss bypass? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

No. Bound refresh/bypass work, coalesce within an explicit scope, and serve authorized bounded-stale data or return 429/503. TTL jitter alone cannot protect a single expired hot key.

</details>

## Follow-up 2 · Expired work has business value

**Changed requirement:** A job expired by latency policy but represents a payment request. May the worker drop it? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Separate obsolete presentation work from durable obligations. Transition the payment to a visible timeout/unknown state with an owner and reconciliation; acknowledge/drop only according to the business contract.

</details>

## Supplied mechanism practice

- [Runnable reliability arithmetic and incident lab](../labs/reliability/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
