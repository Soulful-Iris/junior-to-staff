# P1 · it works

## What you are building

> Build the first usable version of a reading list for Alice and Bob’s study group. They can save links, browse shared notes and track their own reading. A failed title lookup must not lose the saved URL, and one member must not edit another member’s private fields.

**Working contract:** Complete one authenticated create→list→edit journey. Group membership controls visibility, ownership controls the chosen edit policy, and read state belongs to each user. Optional metadata failure remains visible without undoing the save.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../../curriculum/01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Two initial users; 200 group links | A single local relational database is sufficient for the first working application. |
| Two personal read markers per link | Up to 400 read-state rows; one shared is_read field cannot represent both users. |
| 500 ms list target assumption | Read stored data locally; remote title fetching is outside the critical list path. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/reading_list_it_works.py
```

[Open the starting code](../../../../examples/architecture-starts/reading_list_it_works.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| links | group_id,link_id,owner,url,note,version | Shared list records with explicit edit ownership. |
| read_state | user_id,link_id,read_at | Personal progress. |
| title_jobs | link_id,source_version,state | Optional enrichment separate from durable save. |

## AWS implementation

![P1 · it works: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/reading-list-it-works.svg)

The AWS option maps the same application boundaries onto managed services. The first deliverable remains a working local user journey, so infrastructure work does not hide an unfinished save/list contract.

## Build it in this order

### 1. Create the smallest application layout

Put HTTP routes in app.py, database operations in store.py and the browser page in web/. Add a migration for links, membership and personal read state. Start with a local database and two seeded users; production identity is a later adapter, not a client-supplied owner field.

### 2. Implement save and list end to end

POST a URL, commit it and return its ID/version. GET the group list under verified membership. Render the saved URL even if the title is missing. Show validation errors without clearing the form and use a stable request ID for a retried save.

### 3. Add personal state and conditional edits

Mark read/unread for the current user only. Require expected version for shared note edits and preserve a losing draft. Enforce the selected owner/editor policy in the database query, not just by hiding an edit button.

### 4. Make the first release inspectable

Provide one command to start the local app and a short create/list/edit walkthrough with expected responses. Capture a failed title lookup and show the row still exists. Record the first operating limits and the next stage’s persistence/recovery needs.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Local milestone | Complete the workflow with SQLite before substituting cloud adapters. |
| Cloud keys | Include group/owner scope and version conditions; separate personal read records. |
| Identity | Resolve trusted subjects and current membership; do not authorize from raw user IDs in request JSON. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Link 7 exists with no title, while Alice and Bob have different read states. |
| Fail title lookup after save | The URL remains visible with pending/unavailable metadata. |
| Edit with another user’s identity field | Server-side authority ignores the forged owner. |

## The next design decision

Continue to stage 2 with the same app and data model. Identify every acknowledged operation that would disappear if the process or disk failed now.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · The title never arrives

**Changed requirement:** A remote page hangs for sixty seconds. How does the save remain useful? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Give the synchronous fetch a small total deadline and save a visible title-failed/pending state. A later durable queue is an explicit next stage; do not leave untracked in-process background work.

</details>

## Follow-up 2 · Two people update their read state

**Changed requirement:** Alice and Bob mark item 7 read at the same time. Which rows change? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Upsert separate `(user_id,item_id)` read-state rows. Verify group membership at the server and test that reversing either user’s action does not change the other.

</details>

## Supplied mechanism practice

- [Runnable browser/API/store slice](../../../../curriculum/02-applications/03-frontend/labs/bookmark-editor/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
