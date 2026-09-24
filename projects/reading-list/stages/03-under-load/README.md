# P3 · it holds under load

## What you are building

> Add asynchronous title jobs and caching to the working reading list. Two workers overlap after a lease expiry, and ten application instances face 200 readers while the database can sustain only 100 reads/s under this exercise workload.

**Working contract:** Job acceptance is durable, result publication is fenced by current ownership epoch, and cache misses cannot exceed the database budget. A cache improves reads without becoming the authority for ownership, deletion or job completion.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../../curriculum/01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 200 readers issuing one request/s | 200 reads/s offered; a 100 reads/s origin cannot serve every miss directly. |
| Ten application instances | Per-process singleflight can still permit ten fills for one hot key; it is not a fleet-wide rate limit. |
| Worker epoch 1 pauses; epoch 2 finishes | The late epoch-1 result must be rejected, even if its network fetch succeeded. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/reading_list_under_load.py
```

[Open the starting code](../../../../examples/architecture-starts/reading_list_under_load.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| jobs | link_id,source_version,epoch,lease,state | Durable work and publication authority. |
| cache_entry | group,key,source_version,expires_at | Bounded acceleration with current access checks. |
| origin_budget | active_limit,rate_limit,wait_deadline | Fleet/dependency protection during cache loss. |

## AWS implementation

![P3 · it holds under load: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/reading-list-under-load.svg)

The added services separate optional work and hot reads, but the original database/version authority remains. Explicit resource budgets make the ten-instance design understandable during cache failure.

## Build it in this order

### 1. Move enrichment behind durable jobs

Commit job/outbox identity with the saved link. Add worker claims with lease and epoch, bounded retries and a visible failed/repair state. A queue message is delivery, while the job record is truth.

### 2. Fence publication and source versions

Before storing a title, require both current worker epoch and current link URL version. A completed old fetch cannot overwrite a new URL’s title. Acknowledge after result commit and recognize already completed jobs on redelivery.

### 3. Add cache-aside with bounded origin work

Key by group and source version, enforce authorization before response and coalesce hot misses. Add an explicit database concurrency/rate budget shared across the relevant fleet scope. Choose safe stale serving or rejection when the budget is exhausted.

### 4. Observe useful load and recovery

Record offered/completed/rejected requests, cache hit rate, origin reads, queue age and stale publication rejections. Stop a worker and clear the cache in a controlled local run; show bounded recovery instead of only a warm-cache latency number.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Worker configuration | Visibility/lease renewal and finite redrive policy; source-version checks survive retries. |
| Cache outage | Database budget applies even when every cache lookup misses. |
| Fleet capacity | Sum per-instance pools and limits; a local semaphore does not enforce a global maximum by itself. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The old worker cannot change the completed title. |
| Expire a hot key across all instances | Origin work remains within the configured dependency budget. |
| Restart after a completed job loses acknowledgement | Duplicate delivery observes the committed result. |

## The next design decision

Continue to stage 4 by adding optional AI tags without putting model latency or model guesses on the critical save/list path.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · The owner stops after fetching

**Changed requirement:** A crash occurs after the remote GET but before the durable record. How does retry recover? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Refetch is allowed. Record outcome only with the current generation in an atomic completion transaction. Match payload hashes; a duplicate ID with different content is a conflict, not a replay.

</details>

## Follow-up 2 · The cache disappears

**Changed requirement:** Traffic remains 1,000 reads/s but the database can handle only 100/s. What should users see? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Bound origin/bypass work and choose authorized bounded-stale responses or quick 429/503. If read-your-writes is required, use primary/session watermark/confirmed progress; a finite primary pin cannot cover unbounded replica lag.

</details>

## Supplied mechanism practice

- [Cache and replica boundary lab](../../../../curriculum/04-scale-and-evolution/01-data-at-scale/labs/cache-consistency/README.md) — includes its own run command, fixtures and validation limits.
- [Lease and provider recovery lab](../../../../curriculum/04-scale-and-evolution/04-migrations/labs/recovery-migration/README.md) — includes its own run command, fixtures and validation limits.
- [Reliability arithmetic and incident lab](../../../../curriculum/03-production/05-reliability/labs/reliability/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
