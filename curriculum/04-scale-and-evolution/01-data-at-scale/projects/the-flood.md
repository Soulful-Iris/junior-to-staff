# 4. The flood

## What you are building

> Build bounded ingestion for a small event-processing application. A ten-second burst sends 100 events/s, workers complete only 20/s, and the in-memory waiting budget is 300 events. Producers need an explicit answer about accepted versus rejected work.

**Working contract:** Accepted means durably owned work under a finite backlog policy. Keep event identity across retries, expose queue age, and reject excess before pretending it was accepted. A restart cannot lose previously acknowledged work.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100 arrivals/s × ten seconds | 1,000 offered events. |
| 20 completions/s × ten seconds | At most 200 completed during the burst. |
| 300 waiting slots | With that bounded queue, the exercise ends with 200 completed, 300 queued and 500 rejected. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/the_flood.py
```

[Open the starting code](../../../../examples/architecture-starts/the_flood.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| ingestion_record | producer,event_id,payload_hash,state | Durable acceptance and retry identity. |
| work_queue | event_id,enqueued_at,attempt | Delivery and measurable waiting. |
| checkpoint | partition,last_applied | Replay-safe output progress. |

## AWS implementation

![4. The flood: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/the-flood.svg)

SQS can retain work, but the application must decide how much waiting it promises. The acceptance ledger makes overload and restart behavior observable to producers.

## Build it in this order

### 1. Make acceptance explicit

Validate an event envelope and stable producer/event ID. Commit accepted work before returning success. If capacity is exhausted, return a clear rejection with bounded retry guidance; an in-memory append is not durable acceptance.

### 2. Bound the actual queue

Track admitted unfinished work and enforce its limit atomically or through a defined admission authority. Keep oldest age and deadline/retention policy alongside depth. A larger queue buys waiting time, not processing capacity.

### 3. Consume with replay-safe effects

Store output identity/version before advancing progress or acknowledging delivery. Duplicate events cannot apply the effect twice. Poison events go to a visible quarantine/repair state rather than blocking unrelated work indefinitely.

### 4. Recover and reconcile counts

Stop arrivals, measure drain and reconcile offered = completed + queued + rejected under the exercise’s accounting model. Then restart a worker mid-batch and show that accepted identities remain traceable. Preserve late/failed outcomes rather than deleting them to improve throughput figures.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Admission | Enforce unfinished-work budget independently of SQS storage capacity. |
| Workers | Fixed initial concurrency tied to the measured 20/s dependency capacity; bounded retries. |
| Retention | Durable accepted-work horizon and a named repair path for expired or quarantined events. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The four totals are 1,000 offered, 200 completed, 300 queued and 500 rejected. |
| Restart a worker after output commit | Replay recognizes the existing effect. |
| Stop arrivals | The remaining 300 jobs drain at the measured useful rate. |

## The next design decision

An event costs ten times the average. Move from count-only admission toward estimated work units while retaining a hard memory/byte bound for the queue.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · A worker pauses past visibility

**Changed requirement:** A second worker completes before the first resumes. What stops the stale completion? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Condition writes on the current fencing generation and job state. The old process may still execute; only the destination boundary can reject its stale mutation.

</details>

## Follow-up 2 · The backlog must drain

**Changed requirement:** After the burst, arrivals return to 5/s with completion 20/s. How long to drain 300 jobs? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Ideal net drain is 15/s, giving 20 seconds plus actual overhead. Measure age and per-job costs; stop scale-out at the database budget instead of scaling blindly on depth.

</details>

## Supplied mechanism practice

- [Lease and provider recovery lab](../../04-migrations/labs/recovery-migration/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
