# File synchronization

## What you are building

> Build shared-folder synchronization for a small design team. Ana edits a file offline while Ben edits the same base version. Uploads may stop halfway, and a deleted file must not reappear when an old laptop reconnects.

**Working contract:** Upload immutable content, then conditionally publish a metadata version against the client’s base version. Conflicts preserve both users’ bytes for resolution. Deletions are versioned tombstones until supported offline clients can no longer replay older state.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100,000 daily users × 10 MB uploaded/day | About 1 TB/day of new upload traffic before deduplication and replicas. |
| 4 MiB chunk size assumption | A 100 MiB file has 25 chunks; resume transfers by missing chunk hash. |
| Thirty-day offline support assumption | Tombstone/change-log retention must cover that horizon or require a full resynchronization. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/file_synchronization.py
```

[Open the starting code](../../../../examples/architecture-starts/file_synchronization.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| chunks | content_hash,size,object_key | Immutable bytes with verified checksum. |
| file_versions | folder,file_id,version,manifest,deleted | Authoritative metadata and conflict boundary. |
| change_cursor | folder,sequence | Ordered metadata changes for reconnect replay. |

## AWS implementation

![File synchronization: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/file-synchronization.svg)

S3 holds immutable bytes; DynamoDB decides which manifest is current. That split allows interrupted uploads and conflicting edits without exposing partial files or overwriting the winner’s bytes.

## Build it in this order

### 1. Upload content independently

Split files into bounded chunks, hash them and resume only missing chunks. Verify size/checksum before accepting a chunk. Uploading content does not make it visible; orphan chunks can exist safely until metadata references them.

### 2. Publish metadata conditionally

Commit a file manifest only if the expected base version still matches. On conflict, preserve the losing local file and return current metadata. For binary documents, an explicit conflict copy is safer than pretending to merge arbitrary bytes.

### 3. Replay changes and deletions

Return bounded change pages after a folder cursor. Include rename and deletion tombstones with stable file identity; path strings alone are ambiguous under concurrent renames. Reject stale metadata publication after a deletion generation.

### 4. Collect storage safely

Trace committed manifests and active uploads before deleting unreferenced chunks. Wait beyond the upload/retry window and respect shared references. Authorize current folder membership before metadata reads or chunk downloads.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| S3 | Private objects, scoped upload/download authorization and checksum validation; no user-controlled unrestricted key access. |
| Metadata | Conditional version writes and durable cursor ordering; retention tied to offline support. |
| Cleanup | Separate role with narrowly scoped deletion rights; require reference checks and a safe age threshold. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Ana publishes; Ben keeps a conflict; the old laptop cannot overwrite a later deletion. |
| Stop after half the chunks | Resume only missing chunks; the old visible file stays intact. |
| Remove a folder member | New metadata reads and download authorizations are denied. |

## The next design decision

Add cross-folder moves with different permissions. Define the atomic metadata boundary and ensure old download authorization does not silently grant access under the destination’s policy.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>

[Curriculum](../../../README.md) · [Data at scale](../README.md)

All prompts here are constructed practice, without company attribution.

> **Candidate opening:** “Ana uploads a file from two devices, both based on
metadata version 3. Large uploads tie up API capacity, and one device misses a
week of changes. Preserve version authority and show how it recovers.”

| Input | Expected behavior | Scope |
|---|---|---|
| Two finalize requests expecting v3 | One becomes v4, one conflicts | Bytes uploaded does not imply metadata accepted |
| Abandoned upload | Never becomes a ready file; eventually cleaned | Cleanup has an owner and retention bound |
| Device cursor predates retained feed | Resnapshot plus new checkpoint | Cannot resume from a missing history gap |

Prerequisites: [object upload lab](../../../03-production/03-infrastructure/aws/lab-2-upload.md), transactions and
versions. This is a build brief: deliver server-owned upload sessions, verified
conditional finalization, then change-feed recovery. The upload script demonstrates
only bytes; it does not claim to implement this entire sync application.

First separate byte transport from metadata authority. Next put ownership and
expected version in the upload session, validate the object at finalization,
then make the change record durable with the metadata transition.

<details>
<summary>Worked approach and AWS mapping — open after your attempt</summary>

**Prompt:** upload files, list folders, download, and propagate edits across devices. Assume 100,000 daily uploaders × 10 MB/day = about 1 TB/day of new payload. Metadata operations and bytes are separate capacity dimensions. Start with versioned files; exclude collaborative character-level editing.

API issues an upload session containing object key, expected version, and short-lived upload capability. Browser uploads bytes directly to object storage. Finalization checks the object and conditionally updates metadata. Store file id, owner, parent id, object version/key, checksum, size, and metadata version. Upload completion and application visibility are separate transitions.

**AWS mapping:** S3 for bytes, API Gateway/Lambda for metadata, DynamoDB or RDS for ownership and versions, SQS for asynchronous processing, CloudFront for authorized downloads where justified. S3 events can be duplicated or arrive out of order; treat them as triggers to validate state, not unquestionable proof of the newest version.

**Before/after:** proxying large uploads through the API holds application capacity and adds a bandwidth hop. Direct upload reduces that pressure but introduces abandoned sessions, multipart cleanup, and capability security. Version conflicts need an explicit user-visible resolution policy.

**Implement:** AWS lab 2; two clients upload from the same metadata version. **Expected:** one finalize wins; the other gets a conflict, not silent overwrite. **Senior:** resume interrupted multipart uploads and recover missed change-feed updates. **Staff:** region/data residency, account deletion, retention, and compatibility for old clients.

</details>

## Follow-up: the device's history is gone

Use the [expired-history replay fixture](../../04-migrations/labs/recovery-migration/migration.md)
to prove the server refuses incomplete catch-up. **Senior:** preserve unsynced
local drafts during a resnapshot and prove one winner for concurrent finalization.
**Lead follow-up:** a region cannot store this tenant's bytes; route authority
according to residency and define deletion/retention across replicas and backups.
Assessor evidence distinguishes object versions, metadata versions, feed positions,
and local draft identity. A new cursor without a corresponding snapshot is not
recovery.


[Design route](../../../../indexes/system-designs.md) · [Practice rubric](../../../../practice/README.md)

</details>
