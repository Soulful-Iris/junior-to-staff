# 1. The migration you actually finish

## What you are building

> Migrate a live reading-list application from free-text tags to stable tag IDs. Old browsers and queued title jobs still use the previous shape. The migration is complete only when data, readers, writers, background workers and rollback/repair paths all agree on the new contract.

**Working contract:** One writer authority exists at each phase. Backfill and live changes carry source versions, including deletions. Old clients remain supported through an adapter until a documented retirement point; a progress percentage alone does not prove completion.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| One million links; 500 rows/s backfill assumption | About 33 minutes ideal copy time, excluding live changes, indexes and retries. |
| Live update version 5; deletion version 6; late backfill version 4 | Target must retain the version-6 tombstone. |
| Four consumer types | Browser, API, worker and AI/tagging input all belong in the compatibility inventory. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/the_migration_you_actually_finish.py
```

[Open the starting code](../../../../examples/architecture-starts/the_migration_you_actually_finish.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| migration_state | phase,checkpoint,writer_epoch | Resumable progress and authority. |
| link_tags_v2 | link_id,tag_ids,source_version,deleted | Target representation with monotonic apply. |
| consumer_inventory | owner,version,reads,writes,retirement | Evidence that old contracts can actually be removed. |

## AWS implementation

![1. The migration you actually finish: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/the-migration-you-actually-finish.svg)

The backfill worker transports and transforms data; source versions and writer fencing preserve correctness. Configuration routing is coordination metadata, not a substitute for rejecting stale writers.

## Build it in this order

### 1. Inventory before changing storage

List old/new API shapes, browser versions, worker payloads, exports and AI inputs. Name the owner of each reader/writer. Add a canonical tag mapping and compatibility serializer while the old path remains the write authority.

### 2. Implement resumable versioned backfill

Read a consistent source boundary and capture subsequent changes without a gap. Apply source versions conditionally, including tombstones. Persist checkpoints after durable target application so restarting a range is safe.

### 3. Reconcile and transfer authority

Compare canonical records at an aligned watermark, accounting for deletes and tag normalization. Fence old direct writers, apply the final change prefix, then move routing/epoch to the target. Shadow reads alone do not stop an old worker from writing stale data.

### 4. Finish retirement and repair

Observe supported-client usage, drain or adapt old queue payloads, update exports and remove old fields only after every required consumer is covered. Name the first target write that old code cannot interpret; after that point use a prepared reverse adapter or forward repair rather than a misleading rollback button.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Workers | Bound copy load so live requests retain capacity; checkpoints are durable and replay-safe. |
| Routing | Enforce writer authority at the write boundary, not only in cached client routing. |
| Completion | Record old consumer usage and schema compatibility; remove old resources only after the declared retirement conditions. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Version-4 backfill cannot resurrect the version-6 deletion. |
| Restart mid-range | The range replays safely and progress resumes. |
| Send an old worker payload after cutover | The adapter handles it or the old writer is explicitly rejected. |

## The next design decision

A previously unknown export tool still reads the old table. Add it to the inventory and decide whether to adapt or retire it; migration completion is about actual consumers, not only the services you remembered initially.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · The backfill meets live writes

**Changed requirement:** How do you combine snapshot v1 with live v2 and delete v3
without losing either? Predict the failure before opening the design.

<details>
<summary>Expected reasoning and diagram</summary>

Apply only increasing versions and retain tombstones for the replay horizon.
Track checkpoint coverage, source counts/checksums and semantic mismatches.
A counter at zero needs a blind-spot analysis, including dynamic consumers and
delayed/offline writers.

</details>

## Follow-up 2 · A team cannot cut over

**Changed requirement:** One team must keep old clients for a quarter; DNS caches
last 300 seconds. What can rollback promise?

<details>
<summary>Expected reasoning and diagram</summary>

Preserve old/new data compatibility and choose explicit cohorts. Load-balancer
admission, DNS propagation and existing connection drain have different timing.
Keep partial gains measurable, but retire duplicated maintenance only after
consumers and replay obligations are gone.

</details>

## Supplied mechanism practice

- [Live migration and rollback fixture](../labs/recovery-migration/migration.md) — its own commands, fixtures and validation limits.
- [Region loss and rebalancing exercise](../labs/recovery-migration/regions.md) — its own commands, fixtures and validation limits.

These verify specific boundaries; passing their reference tests does not implement
or assess the full project.

</details>
