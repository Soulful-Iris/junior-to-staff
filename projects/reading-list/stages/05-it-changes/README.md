# P5 · it changes safely

## What you are building

> Evolve the completed reading list from text tags to stable tag IDs while users keep editing and deleting links. An old backfill row arrives after a live edit and deletion. The migration must include browsers, workers, exports and AI inputs, not just the database table.

**Working contract:** Versioned apply preserves the newest source state including deletion. One write authority exists at a time. Supported old contracts are adapted until retirement, and the irreversible rollback boundary is recorded before incompatible writes begin.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../../curriculum/01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Backfill version 4; live edit 5; deletion 6 | Applying 4 last must leave the version-6 tombstone intact. |
| Four active consumer families | Browser/API, title worker, export and AI-tagging paths all need compatibility decisions. |
| 10,000 links; 100 rows/s exercise backfill | About 100 seconds ideal copy time, plus live-change catch-up and reconciliation. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/reading_list_it_changes.py
```

[Open the starting code](../../../../examples/architecture-starts/reading_list_it_changes.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| migration_phase | phase,checkpoint,writer_epoch | Explicit authority and restart progress. |
| new_link_state | link_id,tag_ids,source_version,deleted | Conditional monotonic target apply. |
| compatibility_inventory | consumer,old_shape,new_shape,owner,retirement | Actual application-wide completion criteria. |

## AWS implementation

![P5 · it changes safely: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/reading-list-it-changes.svg)

This stage changes the same system built in the earlier stages. The migration succeeds when its consumers and operating procedures agree on the new state, not when a copy counter reaches 100%.

## Build it in this order

### 1. Inventory the entire working system

List browser request/response fields, store methods, queued payloads, exports, prompt inputs and model-output validators. Keep one canonical tag mapping and adapt old contracts deliberately. The previous stage’s optional model does not get an exception from schema compatibility.

### 2. Backfill with versions and tombstones

Capture a source boundary, apply live changes without a gap and checkpoint completed ranges. Use the same conditional apply function for snapshot rows and subsequent updates/deletes. Replaying an old range must not recreate deleted links.

### 3. Reconcile and switch authority

Compare canonical source/target state at an aligned watermark. Fence old writes, catch up the final change prefix and move the writer epoch/routing state. Keep authorized reads and personal read markers consistent through the transition.

### 4. Retire and hand over

Observe actual old-consumer usage, adapt or drain old queue messages and record the removal conditions. Demonstrate the supported rollback before the incompatible-write boundary and the forward-repair procedure after it. Finish with run commands, data/infra ownership and the measured limits from all five stages.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Authority | Enforce fencing at writes; configuration changes alone do not stop stale processes. |
| Compatibility | Keep old response/job adapters until recorded retirement conditions, then remove dead paths. |
| Recovery | Preserve the earlier backup/restore procedure and verify how the new representation changes it. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The version-6 deletion survives late version-4 backfill. |
| Replay an old title/tag job | It follows the adapter/source-version rule and cannot resurrect old data. |
| Inspect every consumer after cutover | The retirement inventory has an owner and evidence for each remaining old path. |

## The next design decision

Choose the next change from observed user demand or operating limits. Carry forward the same discipline: concrete scenario, measurable contract, explicit state authority, runnable path and honest recovery evidence.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · A delete is missed

**Changed requirement:** Counts match but item 7 is present in the target after deletion. What check was missing? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use tombstone/version/value-level reconciliation, not just counts. Replay the missing deletion idempotently and keep it beyond the maximum replay horizon; name gaps in the source log and resnapshot if history expired.

</details>

## Follow-up 2 · Rollback after target-only writes

**Changed requirement:** New writers now create fields the old path cannot read. Can routing alone restore service? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

No. Require reverse projection/compatibility before cutover or define a stop-and-fix-forward boundary. DNS changes also wait for resolver caches and existing connections; distinguish route admission from data readiness.

</details>

## Supplied mechanism practice

- [Live migration and rollback fixture](../../../../curriculum/04-scale-and-evolution/04-migrations/labs/recovery-migration/migration.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
