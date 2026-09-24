# Stage 1: Build the shared reading-list application

## Application background

Alice and Bob want a shared place to keep articles for their study group. Alice pastes a URL, saves it and adds a note about why it is useful. Bob opens the list, reads the article and marks it as read for himself. Alice should still see it as unread until she changes her own status.

The application has a browser interface and an API, the server endpoints the browser calls. The repository supplies the local API and SQLite storage. You will add the usable interface and the identity and permission behavior required for the finished stage.

### Example walkthrough

| Action | Expected behavior |
|---|---|
| Alice sends a save request with a URL | Store a bookmark and return its ID. |
| Bob asks for the list | Show the shared bookmark and Bob's own reading state. |
| Alice's title lookup is slow | Keep the URL saved and show that its title is not available yet. |

The title is the readable page name displayed beside a URL. Looking it up is optional extra work, so it must not determine whether the original URL can be saved.

## Your assignment

**Deliver:** Build a usable browser-to-API reading list from the supplied server. Complete saving, listing, editing and personal reading status, with persistent data and verified user permissions in the finished application.

**Required behavior:** Complete one authenticated create→list→edit journey. Group membership controls visibility, ownership controls the chosen edit policy, and read state belongs to each user. Optional metadata failure remains visible without undoing the save.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope. The cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/reading_list_it_works.py
```

**Supplied file:** [`examples/architecture-starts/reading_list_it_works.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/reading_list_it_works.py). You can also [read or download the source here](../../../../examples/architecture-starts/reading_list_it_works.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only. It does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ. Compare the state transitions and outcomes.

```text
Saved despite missing title: [(7, 'alice', 'https://example.invalid/guide', None)]
Personal progress: [('alice', 7, 1), ('bob', 7, 0)]
```

### Run the application you will extend

The [reading-list API setup guide](../../../../examples/reading-list-starter/README.md) gives you a real local HTTP server, SQLite database, save/list/edit requests and controlled title success/timeout behavior. Start it in one terminal and send the documented `curl` requests from another. Read that setup before following the implementation steps below. The demo above isolates this lesson's mechanism. The server is where you integrate it.

For a first run, start this in **terminal 1** from the repository root:

```bash
python3 examples/reading-list-starter/app.py --db /tmp/reading-list.sqlite3
```

In **terminal 2**, save one bookmark with a controlled title timeout:

```bash
curl -i http://127.0.0.1:8080/bookmarks \
  -H 'X-Demo-User: alice' -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/docs","title_mode":"timeout"}'
```

Expect **201 Created**, a bookmark `id` and `title_status: "timeout"`. The URL is persisted despite the title failure. This is the supplied baseline. The assignment adds the behavior described above. The lookup is a fixture, so no external website is contacted. For members Bob or Ben in a scenario, use the starter's second demo identity `bob`. Alice or Ana corresponds to `alice`.

Work in your own branch or copy `examples/reading-list-starter/` to `work/01-it-works/`. `app.py` exists in that directory. Add the modules named below there as you separate HTTP, storage and background work. The server has demo membership, not production authentication.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| links | group_id,link_id,owner,url,note,version | Shared list records with explicit edit ownership. |
| read_state | user_id,link_id,read_at | Personal progress. |
| title_jobs | link_id,source_version,state | Optional enrichment separate from durable save. |

## Implement the assignment

### 1. Create the smallest application layout

Put HTTP routes in app.py, database operations in store.py and the browser page in web/. Add a migration for links, membership and personal read state. Start with a local database and two seeded users. Production identity is a later adapter, not a client-supplied owner field.

### 2. Implement save and list end to end

POST a URL, commit it and return its ID/version. GET the group list under verified membership. Render the saved URL even if the title is missing. Show validation errors without clearing the form and use a stable request ID for a retried save.

### 3. Add personal state and conditional edits

Mark read/unread for the current user only. Require expected version for shared note edits and preserve a losing draft. Enforce the selected owner/editor policy in the database query, not just by hiding an edit button.

### 4. Make the first release inspectable

Provide one command to start the local app and a short create/list/edit walkthrough with expected responses. Capture a failed title lookup and show the row still exists. Record the first operating limits and the next stage’s persistence/recovery needs.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Link 7 exists with no title, while Alice and Bob have different read states. |
| Fail title lookup after save | The URL remains visible with pending/unavailable metadata. |
| Edit with another user’s identity field | Server-side authority ignores the forged owner. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target. The local demonstration does not establish that throughput. Use the [estimation constants](../../../../curriculum/01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Two initial users. 200 group links | A single local relational database is sufficient for the first working application. |
| Two personal read markers per link | Up to 400 read-state rows. One shared is_read field cannot represent both users. |
| 500 ms list target assumption | Read stored data locally. Remote title fetching is outside the critical list path. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Stage 1: Build the shared reading-list application: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/reading-list-it-works.svg)

The AWS option maps the same application boundaries onto managed services. The first deliverable remains a working local user journey, so infrastructure work does not hide an unfinished save/list contract.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local static/media delivery path | Amazon CloudFront: group web application | Configure an origin, cache policy and private-content access. Distinguish cached bytes from current authorization. |
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: reading-list API | Create routes and an integration. Translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: list application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: cloud storage option | Design partition/sort keys and write a storage adapter with conditional updates or transactions. Python state and SQL are not uploaded as a database. |
| Local fixture identity or caller supplied to the operation | Amazon Cognito: production identity option | Configure an identity provider and validate tokens. Retain resource ownership checks in application code. |
| Local file, object fixture or exported payload | Amazon S3: static web assets | Implement upload/download and metadata adapters, scoped access, object naming, retention and incomplete-upload cleanup. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Local milestone | Complete the workflow with SQLite before substituting cloud adapters. |
| Cloud keys | Include group/owner scope and version conditions. Separate personal read records. |
| Identity | Resolve trusted subjects and current membership. Do not authorize from raw user IDs in request JSON. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement. It is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Continue to stage 2 with the same app and data model. Identify every acknowledged operation that would disappear if the process or disk failed now.

<details>
<summary>Follow-up scenarios and worked designs</summary>

## Follow-up 1 · The title never arrives

**Changed requirement:** A remote page hangs for sixty seconds. How does the save remain useful?

<details>
<summary>Worked design and implementation</summary>

Give the synchronous fetch a small total deadline and save a visible title-failed/pending state. A later durable queue is an explicit next stage. Do not leave untracked in-process background work.

**Keep stage one small and explicit.** The supplied save stores the bookmark before title enrichment. Add a total deadline to the real fetching adapter and return the stored URL even when no title is available. Show a user-facing state such as title unavailable rather than an endless spinner.

Use the local timeout fixture and display the saved row after the response. Do not launch an untracked background thread and call it durable processing. If the requirement changes to eventual title completion after restarts, move to the durable job architecture in stage three and add the missing state deliberately.

</details>

## Follow-up 2 · Two people update their read state

**Changed requirement:** Alice and Bob mark item 7 read at the same time. Which rows change?

<details>
<summary>Worked design and implementation</summary>

Upsert separate `(user_id,item_id)` read-state rows. Verify group membership at the server and test that reversing either user’s action does not change the other.

**Name the key that owns the action.** Read status belongs to the pair of member and bookmark. The shared bookmark row does not own a single global read flag. Store `(alice, 7, true)` and `(bob, 7, true)` independently after verifying current membership.

Mark both read, then let Alice mark hers unread. Show Alice seeing false and Bob still seeing true. Deliver the two database rows and both API responses. This is a schema ownership change, so a small state table explains it better than extra cloud boxes.

</details>

## Supplied mechanism practice

- [Runnable browser/API/store slice](../../../../curriculum/02-applications/03-frontend/labs/bookmark-editor/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries. Completing their reference tests does not implement or assess the full project.

</details>
