# 1. A shared reading list

## What you are building

> Build a reading list for a six-person study group. Members share saved links and notes, but each person tracks their own read state. Two people edit the same note on different devices, and an unsaved draft must survive a conflict.

**Working contract:** Group membership controls link visibility. Shared link metadata and per-user read state are separate. Conditional edits return a conflict without discarding the user’s draft; delayed responses cannot overwrite newer UI state.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Six members × 200 saved links | 1,200 potential personal read-state rows for 200 shared links; do not put one global read flag on the link. |
| 50 concurrent active readers exercise peak | Begin with paginated database reads; a cache is optional after measuring. |
| Two edits from revision 3 | Exactly one revision-3 conditional update can win; the second client keeps its draft. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/a_shared_reading_list.py
```

[Open the starting code](../../../../examples/architecture-starts/a_shared_reading_list.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| links | group,link_id,version,url,note | Shared metadata and conditional edit authority. |
| read_state | user,link_id,read_at | Personal state independent of other members. |
| editor_state | base_version,draft,server_value,request_generation | Explicit dirty/saving/conflict UI state. |

## AWS implementation

![1. A shared reading list: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/a-shared-reading-list.svg)

The UI needs its own explicit state model as much as the backend needs conditional writes. A successful conflict response is useful only if the browser preserves the work the user was trying to save.

## Build it in this order

### 1. Build the group list first

Implement membership, create/list and stable link IDs. Save the URL before optional title enrichment. Paginate by a stable key and show loading, empty and unavailable states without clearing previously loaded content unnecessarily.

### 2. Separate personal interaction state

Store read/unread by authenticated user and link. Marking a link read changes only that user’s view. Optimistic UI should roll back or display a retry state after a failed write rather than pretending the server accepted it.

### 3. Implement an explicit editor state machine

Keep base version and draft separately from the latest server record. Save with expected version; on 409 show current server text beside the preserved draft. Use request generations so an older save response cannot replace a newer draft.

### 4. Handle membership and accessibility

Reauthorize API reads and writes after revocation, including warm caches. Provide keyboard-accessible controls and clear save/conflict announcements. Keep a revoked member’s local draft from being silently submitted under another user’s session.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| API data | Include group scope in every key/query; conditional versions on shared edits. |
| Frontend delivery | Cache versioned static assets; keep private API responses out of shared caches. |
| Identity | Membership remains an application decision after token validation; revocation affects current reads/writes. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Ana saves; Ben retains a conflicting draft; their read states remain independent. |
| Deliver an older save response late | The newer local draft is not replaced. |
| Revoke membership | New list and save requests are denied even with cached group data. |

## The next design decision

Add offline editing. Queue operations with base versions and identities, then surface genuine conflicts on reconnect instead of replaying last-write-wins over other members’ work.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · Many groups

**Changed requirement:** Alice belongs to two groups; Bob belongs to one. Which rows can Bob list? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Filter by verified membership at the data access boundary; never trust a client-supplied group ID alone. Test list, detail, edit and title-job paths for cross-group leakage.

</details>

## Follow-up 2 · The title provider stalls

**Changed requirement:** Saving must return in 300 ms while the provider takes ten seconds. What moves? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Atomically save the item and durable title job, return pending, and let a guarded bounded worker complete the title. Retry execution may repeat fetching; conditional versions protect the current result.

</details>

</details>
