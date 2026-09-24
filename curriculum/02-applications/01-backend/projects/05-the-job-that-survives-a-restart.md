# 5. The job that survives a restart

## What you are building

> Move title fetching out of a bookmark request into a durable background job. The worker can die after fetching a title, two workers can overlap after a lease expires, and an old worker must not replace a newer result when it resumes.

**Working contract:** Creating a bookmark commits a stable title job and dispatch intent. Jobs expose accepted, running, succeeded and failed states. A result is published only by the current ownership epoch; queue acknowledgement follows the durable outcome.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100 saves/minute; two-second mean fetch | About 3.3 occupied worker slots at steady state; start with a small bounded pool. |
| Thirty-second lease | Renew only while the same epoch owns the job; a paused worker can lose ownership before it notices. |
| Five delivery attempts | Exhaustion becomes a visible failed/repair state, not an endlessly hidden queue retry. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/05_the_job_that_survives_a_restart.py
```

[Open the starting code](../../../../examples/architecture-starts/05_the_job_that_survives_a_restart.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| jobs | bookmark_id,request_id,state,epoch,lease_until | Logical identity and ownership. |
| attempts | job_id,epoch,started,outcome | Separate retries under one job. |
| bookmark_title | bookmark_id,title,title_version | Updated conditionally by the winning job/source version. |

## AWS implementation

![5. The job that survives a restart: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/05-the-job-that-survives-a-restart.svg)

The queue wakes workers; the job record owns lifecycle and publication. Keeping those roles separate makes duplicate delivery and restarts understandable.

## Build it in this order

### 1. Create a durable job transaction

In store.py, save the bookmark and job/outbox record together. Return a stable status URL after commit. A duplicate create request reuses the job identity; it does not schedule another logical fetch.

### 2. Implement worker ownership

In worker.py, claim due work using a conditional epoch increment and lease timestamp. Store attempt evidence. A queue’s visibility period only limits delivery overlap; the job-store condition decides who may publish.

### 3. Publish and acknowledge in order

Recheck bookmark source version and worker epoch before writing the title and succeeded state. Acknowledge after commit. On redelivery, a completed job is recognized and acknowledged without another visible result. Handle deleted bookmarks as cancellation rather than recreating them.

### 4. Add an operator repair path

Show oldest accepted job, attempt count, last error and next retry. After bounded attempts, move to failed/DLQ and allow an authorized replay retaining logical identity. A replay is evidence, not deletion of the previous failure history.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| SQS | Visibility greater than ordinary work duration, bounded redrive and a documented repair action. |
| DynamoDB | Conditional claims and result writes; TTL cleanup never substitutes for lease/expiry checks. |
| Worker | Outbound URL policy, total deadline and reserved concurrency protecting source/database capacity. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Epoch 2 wins; epoch 1 cannot replace the title. |
| Restart after result commit but before acknowledgement | Redelivery observes succeeded and finishes without another result. |
| Delete the bookmark while work waits | The worker records cancellation and does not recreate it. |

## The next design decision

Let users edit the URL while an old fetch runs. Add a source URL version to the job and reject results for an earlier source even if the worker still owns its lease.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · A expires during work

**Changed requirement:** A resumes after expiry but before B claims. May it still commit? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Under this exercise’s strict policy, no: the commit checks both generation and lease validity using authoritative time. A must reacquire a new generation. This closes the gap where “owner matches” alone accepts an expired owner.

</details>

## Follow-up 2 · The provider charges per operation

**Changed requirement:** Replace the read with a billable enrichment API that succeeds but loses its response. Can you safely repeat? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use a provider-supported idempotency key or status lookup tied to the same operation identity. Otherwise record outcome unknown and reconcile before retrying a non-idempotent effect. Local fencing protects your store, not an external provider.

</details>

## Supplied mechanism practice

- [Lease and provider recovery lab](../../../04-scale-and-evolution/04-migrations/labs/recovery-migration/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
