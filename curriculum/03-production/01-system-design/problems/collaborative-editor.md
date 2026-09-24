# Collaborative editor: two people edit the same sentence

## What you are building

> Build a shared incident document for up to 50 responders. Two browsers edit revision 12 at once, one laptop works offline, and a server restarts after acknowledging an operation. Start with a correct versioned editor before adding automatic merging.

**Working contract:** An acknowledged edit is durable and assigned a document revision. The first milestone accepts an edit only against its stated base revision; stale edits remain as local drafts with an explicit conflict. Presence and cursors are best-effort.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 10,000 active documents; 50 possible editors/document | Up to 500,000 connected editors; actual active edit rate must be measured separately. |
| Two edits/s from 10% of connected editors | 100,000 operations/s in this constructed active scenario, not a benchmark claim. |
| Snapshots every 1,000 accepted operations | Recovery replays a bounded tail; retain enough history for supported offline clients. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/collaborative_editor.py
```

[Open the starting code](../../../../examples/architecture-starts/collaborative_editor.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| documents | document_id,revision,snapshot_pointer | Current durable state and snapshot boundary. |
| operations | document_id,operation_id,base_revision,new_revision | Idempotent accepted changes in order. |
| presence | document_id,session_id,last_seen | Expiring cursor information; never durable edit truth. |

## AWS implementation

![Collaborative editor: two people edit the same sentence: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/collaborative-editor.svg)

The operation log is durable; presence is disposable. ECS exposes the stateful session and ordering problem clearly. A managed synchronization product can replace parts of this design, but its conflict and offline semantics must still match the product.

## Build it in this order

### 1. Build a versioned save protocol

Implement GET document and POST operation with base revision and operation identity. Commit accepted operation and new revision together. Keep the losing draft visible and support a manual merge against the latest revision. This is a useful working baseline, not a claim of conflict-free editing.

### 2. Add live operation delivery

Broadcast only committed operations. Clients track the last applied revision and fetch missing ranges on reconnect. Apply duplicate operation IDs once. Store snapshots with a proven last included revision so replay neither skips nor doubles an edit.

### 3. Choose an actual merge algorithm

For automatic concurrent editing, choose a maintained OT or CRDT implementation and document its operation identities, causal metadata and persistence format. Do not invent string-offset merging after the fact; deletion and insertion offsets change under concurrent edits.

### 4. Bound offline and presence state

Specify the supported offline duration and history/metadata retention required by the chosen algorithm. Expire presence independently. A user removed from the document cannot upload old offline edits without a current authorization check.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Document ownership | Route a document to one logical ordering authority; persist ownership/fencing if session owners can change. |
| Operation storage | Unique document/operation identity; bounded replay pages; snapshot publication after durable upload. |
| Connection limits | Cap sessions per document and reconnect replay rate; reject oversized operations before broadcasting. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Ana reaches revision 13; Ben keeps an explicit conflicting draft; Ana’s retry returns revision 13. |
| Restart after acknowledgement | The accepted edit reappears from the log. |
| Drop a live event | The client discovers the revision gap and replays durable operations. |

## The next design decision

Allow two offline users to delete and insert at the same position. Show the chosen algorithm’s actual operation data and convergence rule. A diagram labeled merge is not enough to define the result.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



**Your contract.** Start with plain text, 50 concurrent editors per document, 10,000 active documents, and a durable history. Presence may disappear temporarily; acknowledged edits may not. Agree on whether an offline edit must merge automatically or can require a visible conflict resolution. This is a constructed exercise, not a claimed company question.

| Situation | Submitted edits | What the reader should see |
|---|---|---|
| Uncontested | Ana adds “!” at version 4 | Version 5 contains “!”; reconnect replays it once |
| Concurrent | Ana and Ben both replace the word at version 4 | One defined merge rule or a visible conflict; neither edit silently vanishes |
| Lost acknowledgement | Server commits operation `a17`, then Ana retries `a17` | One committed edit and the same acknowledgement |
| Offline | Ben edits version 4; document advances to 7 | Rebase or conflict path is explicit; stale positions are not applied blindly |

## Work through the authority

Draw a single-document sequencer first. A connection carries an **operation ID, document ID, base version, and edit**. The authority verifies permissions, deduplicates by operation ID, assigns the next version, and commits the operation before broadcasting it. Presence can be best effort; it must not be confused with durable edits. The first version may reject a stale base with the latest version and ask the client to rebase. If automatic merges are required, explain the transform or CRDT rule and prove convergence on a concurrent insertion before committing to it.

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| API Gateway WebSocket | Hold live editor connections and route messages | ECS service with WebSockets for tighter connection control or custom protocols |
| ECS document owners | Serialize one document's decisions and broadcast results | Lambda with conditional DynamoDB writes if connection affinity and long-running merge logic are unnecessary |
| DynamoDB operation log | Persist `(document, version)` and operation IDs; conditional version advance | Aurora PostgreSQL transaction when relational collaboration queries matter more |
| S3 snapshots | Store periodic materialized documents to bound replay | Keep short documents in DynamoDB if snapshot size and cost stay small |

The ECS owner is an optimization, **not** the only protection: a restarted owner must still lose a conditional version race to the durable store. WebSocket delivery is not a commit acknowledgement. Be precise about the log, snapshot version, and replay cursor.

**Senior follow-up:** Split a document's readers across connection nodes. How does a node replay versions 5–7 after a dropped broadcast? Discuss presence expiration separately from document state.

**Staff follow-up:** A celebrity document attracts 10,000 readers; a Region fails while edits are in flight. Set explicit write locality, fanout budget, conflict policy, RPO, and client behavior during failover. Show which acknowledgement can survive the move.

**Practice artifact:** Draw the authority and three client states (current, stale, reconnecting). Walk the four rows above with version numbers. Spend 35 minutes designing and 10 minutes attacking an acknowledged but not broadcast edit.

**Source boundary:** This problem and capacities are original. Current [DynamoDB condition expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html) describe the AWS primitive; they do not provide automatic merge semantics.

</details>
