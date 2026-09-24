# Durable jobs: the queue drained, the work did not

## What you are building

> Build CSV exports for a billing dashboard. The API must return a status URL quickly, and a worker must finish the export after an API or worker restart. Two workers may process the same message; only the current owner may publish the download pointer.

**Working contract:** POST /exports with a tenant-scoped request ID returns 202 plus a stable job URL after durable acceptance. GET /exports/{id} returns accepted, running, succeeded, failed or cancelled. A download is available only through a committed result pointer.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 500 exports/min; 20 seconds mean service | 500 / 60 × 20 ≈ 167 busy worker slots at steady state, before spare capacity. |
| 50 worker slots | Capacity is 150/min; backlog grows 350/min under the stated ordinary load. |
| 40,000 requests in one minute | Admission must reject or defer beyond an explicit backlog budget; an unbounded queue is not extra processing capacity. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/durable_jobs.py
```

[Open the starting code](../../../../examples/architecture-starts/durable_jobs.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| jobs | tenant,request_id,job_id,state,epoch | Durable status and ownership authority. |
| attempt_objects | job_id/epoch/checksum | Immutable bytes; uploading is not publishing. |
| result_pointer | job_id → object_key,checksum,size | Updated only by the current ownership epoch. |

## AWS implementation

![Durable jobs: the queue drained, the work did not: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/durable-jobs.svg)

SQS can redeliver, so DynamoDB owns job state and the publication condition. ECS accommodates longer exports; short bounded jobs could run in Lambda. S3 stores complete bytes, while the conditional result pointer decides which bytes users receive.

## Build it in this order

### 1. Accept durably

Commit job identity and dispatch intent in one database transaction. A lost response followed by the same request ID returns the original job. Queue publication happens from the outbox; a queue message is a request to advance a job, not its authoritative status.

### 2. Claim and renew ownership

Store an incrementing epoch with lease expiry. Claim using a conditional update; renew only the matching epoch. SQS visibility reduces concurrent work but cannot prevent every duplicate. A worker must stop publishing if renewal or the conditional ownership check fails.

### 3. Publish an immutable result

Upload to an attempt-specific object key. Conditionally write succeeded and the object pointer under the current epoch. Acknowledge the queue message after that commit. If redelivered, read completed state and acknowledge without generating another visible result.

### 4. Operate a bounded service

Reject new work with Retry-After once admitted backlog exceeds the product’s wait budget. Add cancellation and tenant fairness. Garbage-collect unreferenced attempt objects only after active leases and retry windows; authorize current access when issuing a download.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| DynamoDB jobs | Conditional claims/publication; durable request identity; strongly consistent ownership reads where required. |
| SQS | Start visibility at 60 s for 20 s average work and renew for longer jobs. Set a finite redrive policy and a DLQ repair procedure. |
| ECS workers | Bound worker count by database and export-source capacity, not queue depth alone. Keep job deadlines below lease-renewal safety margins. |
| S3 | Private immutable attempt keys; result pointer stored separately; lifecycle only for proven orphan/expired output. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Epoch 5 publishes; the late epoch 4 attempt is rejected. |
| Kill the worker after upload | A retry may produce an orphan object, but users see one committed result. |
| Limit the pool to 50 workers | At 500 arrivals/min the oldest-job age grows; admission eventually closes at the declared bound. |

## The next design decision

Add data erasure while an export is running. Define how the worker discovers cancellation, how the current pointer is revoked, and how object cleanup is proven without assuming that queue cancellation stops an already running process.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



Assume 500 ordinary exports/minute, 20-second average processing time, and a 60-second API request timeout. The job should survive a worker crash; accepted means durably recorded, not completed.

| Input / state | Expected result |
|---|---|
| Client retries create after lost reply with same key | One logical job; stable status URL |
| Worker writes file, then crashes | Later worker checks committed output; does not send two invoices/files |
| Worker is stuck forever | Visibility expires; bounded retries and DLQ plus an operator repair path |
| 40,000 requests in 60 seconds | Admit within capacity or return an explicit overload outcome; backlog is measurable |

## Keep job truth separate from message delivery

Create a durable job record keyed by customer and request identity; record ACCEPTED, RUNNING, SUCCEEDED or FAILED with attempt/lease information. Queue messages ask workers to make progress; status comes from the job store. Write each attempt to an **immutable** object key such as `job/attempt-id/checksum`; never overwrite a shared `job/result.csv`. A delivery may repeat while an earlier worker is running. Publish `{object_key, checksum, size}` together with SUCCEEDED in a conditional job-store update requiring the current ownership generation. Readers follow only that committed pointer, not a guessed object name or listing. Reject stale pointer updates even when their object upload succeeded. If a side effect cannot be idempotent, reconcile it explicitly.

### Pause the old worker at the dangerous boundary

| Step | Authoritative result | Object state |
|---|---|---|
| A claims generation 4, then pauses | RUNNING, generation 4 | No published output |
| Lease expires; B claims generation 5 | RUNNING, generation 5 | B writes immutable object B |
| B publishes under generation 5 | SUCCEEDED → B, checksum B | B is reachable |
| A resumes and uploads object A | Still SUCCEEDED → B | A is an orphan; it cannot overwrite B |
| A tries generation-4 publication | Conditional update fails | Readers still obtain B’s bytes |

Crash after uploading but before publishing leaves a complete orphan, not a
partial result. A retry first reads current job truth; a duplicate completed
message is acknowledged without another effect. Garbage collection excludes
committed pointers and active attempts, and waits beyond the retry/lease window.
Recheck current read permission before issuing an output download.

The bars show a trend, not a measured forecast. At the stated steady rates the backlog grows by **350 jobs each minute**; after ten minutes that is 3,500 waiting jobs before cancellations, retries, or changes in service time. An overload policy must address admitted work before the oldest age runs away.

## Put the AWS names on the boxes

**Why these boxes, and what changes the choice:** SQS buffers accepted jobs but redelivers on a lost acknowledgement. DynamoDB stores stable job IDs and conditional status; S3 holds private immutable attempt objects; the job-store generation check publishes the winning pointer. Existence alone does not prove ownership or the right bytes. ECS can replace Lambda for jobs that exceed its duration or memory envelope.



**Senior follow-up:** At 500/min and 20 seconds per job, Little's-law concurrency estimate is roughly 167 occupied worker slots for zero queue growth at steady load. If the system can run only 50 tasks, derive the queue growth and make the wait visible. Apply per-tenant fairness and a bounded retention/expiry policy.

**Staff follow-up:** A customer requests data deletion while an export waits or runs. Decide which step authorizes the read, how to revoke or cancel the output, and what audit record survives deletion without retaining private data. Show the repair path after an entire Region disappears.

**Practice artifact:** State machine, duplicate timeline, backlog calculation, cancellation test, and operations panel with oldest-job age, retry count, completion lag, and DLQ volume.

**AWS translation:** SQS standard queues can redeliver and occasionally reorder; tune visibility timeout, DLQ policy, and worker concurrency. Store authoritative jobs in DynamoDB/RDS and outputs in private S3. Read [SQS standard delivery](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html) and [visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html).

**Source note:** Constructed exercise; service delivery facts come from AWS documentation.

</details>
