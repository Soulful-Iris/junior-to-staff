# P2 · it survives

## What you are building

> Extend the same reading-list application so accepted saves survive process restarts and recovery is honest about data loss. A backup taken at 12:00 contains link 100; link 101 is acknowledged at 12:03; the primary fails at 12:05.

**Working contract:** Durable acknowledgement, backup and restore are separate guarantees. Restore into an isolated location, inspect recovered data and state the observed recovery point/time. Do not claim zero loss when link 101 was never present in the restored backup.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../../curriculum/01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Backup 12:00; acknowledgement 12:03; failure 12:05 | Snapshot-only recovery may lose link 101; the latest backup is five minutes old. |
| 200 links at 1 KiB metadata assumption | Data volume is small enough to inspect directly; correctness of restore is the exercise. |
| Thirty-minute recovery target assumption | Measure start-to-usable time, including credentials, schema and object references. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/reading_list_it_survives.py
```

[Open the starting code](../../../../examples/architecture-starts/reading_list_it_survives.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| durable_store | committed link/request identity | What success promises across process restart. |
| backup_manifest | created_at,source_position,schema,objects | Exactly which data the backup contains. |
| restore_record | target,started,ready,recovered_position,missing_ids | Evidence of recovery and acknowledged loss. |

## AWS implementation

![P2 · it survives: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/reading-list-it-survives.svg)

A backup service coordinates retained recovery points, but the application’s loss and recovery claims come from inspecting a restored target. A successful backup job alone does not establish those claims.

## Build it in this order

### 1. Persist the application state

Move from disposable memory to a durable local file/database with an explicit commit boundary. Store request identities with creates so a lost response can be retried. Restart the process and show that acknowledged links and personal read state remain.

### 2. Create a restorable backup

Record schema version, database position/time and referenced object versions. Protect backup credentials and retention separately from the application’s ordinary write role. A copied database file is only a valid backup if the database’s supported snapshot procedure makes it consistent.

### 3. Restore away from the source

Use a new database/path and the documented startup command. Inspect link 100 and the acknowledged link 101 scenario. Record missing acknowledged operations rather than inferring completeness because the application starts successfully.

### 4. Close the recovery gap deliberately

Choose more frequent snapshots, log-based point-in-time recovery or another durability design based on the required loss bound. Rehearse the actual restore path and include access, schema migration and private object references in the measured recovery time.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Database recovery | Configure the selected service’s backup/PITR behavior and retain required logs; verify the actual recoverable window. |
| Restore target | Separate resource identity and credentials; never overwrite the only source while learning recovery. |
| Evidence | Record restored commit/time, schema and missing acknowledged IDs; encrypt/restrict backups containing private data. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The restored snapshot contains 100 and lacks acknowledged 101. |
| Restart only the app process | Durable committed state remains available. |
| Restore into a fresh environment | Record the actual ready time and recovered data boundary. |

## The next design decision

Continue to stage 3 with the recovery procedure intact. Add asynchronous work without weakening what an accepted job or a published result means.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · A deploy crashes

**Changed requirement:** A candidate version exits immediately. What keeps the previous version available? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Build once, route only to ready instances, preserve the previous artifact and compatible config, and prove rollback by observing served version. Data compatibility remains a separate gate.

</details>

## Follow-up 2 · The primary and its credentials are lost

**Changed requirement:** Can an unfamiliar engineer recover without depending on the failed primary? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use independently accessible backup, documented scoped recovery identity and a fresh target. Verify row contents and application behavior before routing traffic; retain evidence of missing acknowledged writes.

</details>

</details>
