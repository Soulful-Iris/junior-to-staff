# Data erasure: one request, nine copies

## What you are building

> Build account erasure for a document product with primary records, exports, search indexes and backups. A user deletes their account while an export is running and an old data import is queued. Stop new access immediately, then show which deletion steps finished and which are legitimately retained.

**Working contract:** DELETE /account creates an erasure case and a durable deletion generation. New reads and writes are denied under that generation. GET /erasure/{case_id} exposes pending, completed and specifically retained categories without leaking erased content.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100 requests/day; 30-day exercise deadline | Up to 3,000 open cases if everything consumes the full window; size workflow metadata independently of data volume. |
| Six data stores per account | Track six acknowledgements with evidence, not one optimistic deleted flag. |
| Ten-minute export jobs | Cancellation must reach running work; removing only the queued message is insufficient. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/erasure_workflow.py
```

[Open the starting code](../../../../examples/architecture-starts/erasure_workflow.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| deletion_ledger | subject,generation,requested_at | Prevents stale jobs and restored data from resurrecting access. |
| erasure_steps | case_id,store,status,evidence_ref | One restartable task per affected store. |
| retention_exceptions | case_id,category,reason,expiry | Explicit product-approved exceptions; no broad hidden exemption. |

## AWS implementation

![Data erasure: one request, nine copies: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/erasure-workflow.svg)

Step Functions coordinates progress; it does not discover every copy automatically. A separate deletion ledger prevents old workers or backup restoration from reintroducing a deleted subject. Each store adapter must return evidence for its own boundary.

## Build it in this order

### 1. Deny access before cleanup

Commit the deletion generation and disable account access first. Every consumer that can recreate data must check the ledger before writing. Use non-sensitive identifiers in evidence and restrict ledger readers; a tombstone is not permission to keep the entire old profile.

### 2. Inventory and dispatch deletion

List primary tables, object versions, cache keys, search documents, analytics exports and processors. Store one idempotent step for each owner. A step records concrete evidence, such as affected version ranges or processor confirmation, before completion.

### 3. Handle backups and holds

Document when immutable backups expire and the procedure that reapplies the deletion ledger before a restore is served. Track a hold at the affected category rather than declaring the whole account exempt. The 30-day figure is a scenario assumption, not legal advice or a compliance guarantee.

### 4. Finish and explain the case

Expose pending steps, age and named escalation owner. Reconcile storage inventories and running jobs against completed cases. Mark complete only when the configured policy is satisfied and any retained categories are disclosed through the authorized case view.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Step Functions | Durable orchestration with bounded retries and explicit manual-repair states; avoid putting personal content in execution input/history. |
| DynamoDB ledger | Retain minimal generation and case identity; check on restore and import paths. |
| S3 versions and exports | Enumerate versions and replicas in scope; a delete marker alone does not remove historical object bytes. |
| Search and caches | Delete projections and invalidate access; authorization remains enforced while cleanup is delayed. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | A version-4 import is rejected by deletion generation 6. |
| Stop one store adapter | The case remains pending with that store and age visible. |
| Restore yesterday’s backup | Replay deletion generations before opening reads; the erased account stays unavailable. |

## The next design decision

A vendor says deletion is complete but cannot provide object-level evidence. Decide which assurance is sufficient for that processor, who accepts it and what the customer sees. Keep technical progress distinct from policy approval.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



**Your contract.** Invent a 30-day completion target for this exercise; actual legal deadlines depend on jurisdiction and counsel. Retention and legal holds can override ordinary deletion. Do not assert that one database DELETE removes backups or immutable archives.

| Condition | Expected state |
|---|---|
| Request submitted twice with the same ID | One erasure job, stable status and no accidental duplicate side effects |
| Main row gone but search hit remains | Job is **in progress**, and reads suppress the subject immediately |
| S3 version is under legal hold | Surface an exception with owner, scope, and reason; never report “fully erased” |
| A backup is restored after erasure | Deletion tombstone/ledger prevents re-exposure and triggers re-erasure |

## Treat erasure as a stateful distributed workflow

Record an authenticated request ID, subject scope and policy decision. Immediately deny reads via a retained tombstone while asynchronous workers enumerate stores and delete or render inaccessible each copy. Every subsystem reports an evidence record for an exact version/range; a coordinator marks complete only after required acknowledgements, or records a formal exception. Reconcile stale projections and backup restores against the ledger. Don't leak the user's identity in a broadly readable job dashboard. A legal-hold path needs explicit review, not a silent retry loop.

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| AWS Step Functions (workflow coordinator) | Track deletion steps, retries, and exception states | Application-owned orchestrator where dynamic inventories exceed workflow limits |
| Amazon DynamoDB (request ledger) | Hold idempotency keys, tombstones, and per-store evidence | Amazon RDS for complex relationships and transactional review workflow |
| Amazon S3 (object and backup storage) | Delete all applicable object versions or flag retention/hold exceptions | Other object stores under the same explicit inventory requirement |
| Amazon SQS (work queue) | Decouple slow deletion workers and bound retry rate | EventBridge for event routing, with separate stateful coordination |
| Amazon CloudWatch (audit telemetry) | Alert on overdue jobs, missing acknowledgements, restored copies | Existing observability with immutable investigation evidence elsewhere |

A DynamoDB TTL is eventual expiry, **not** a deadline or erasure proof. S3 Object Lock can prevent removal of retained object versions; the state machine must record this honestly. Enumerate data lineage before claiming coverage.

**Senior follow-up:** A search index is down for two days. Keep the subject suppressed from live reads; show how the worker resumes and verifies the index after recovery.

**Staff follow-up:** One team introduces a new feature store without registering it. Create an ownership and data-classification gate, rollout check, periodic scan, and a reporting rule that reveals missing coverage.

**Practice artifact:** Draw a copy inventory and state machine. For each row in the table, state what the user-facing status says and what evidence the operator can inspect.

**Source boundary:** Original exercise motivated by [Meta's June 2026 privacy infrastructure case study](https://engineering.fb.com/2026/06/25/security/privacy-aware-infrastructure-in-the-ai-native-era-an-asset-classification-case-study/). [DynamoDB TTL documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ttl-expired-items.html) and [S3 Object Lock documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) constrain the AWS design; this is not legal advice or a reported interview question.

</details>
