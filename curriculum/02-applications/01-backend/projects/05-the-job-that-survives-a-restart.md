# Move title lookup into restartable background jobs

## Application background

Saving a bookmark should return promptly even when fetching its title is slow. A separate worker enriches the record later, and users can see whether that work is pending, complete or needs attention.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** Commit job intent with the saved URL, then implement claim, retry and fenced completion in a separate worker process.

Move title fetching out of a bookmark request into a durable background job. The worker can die after fetching a title, two workers can overlap after a lease expires, and an old worker must not replace a newer result when it resumes.

**Required behavior:** Creating a bookmark commits a stable title job and dispatch intent. Jobs expose accepted, running, succeeded and failed states. A result is published only by the current ownership epoch; queue acknowledgement follows the durable outcome.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope; the cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/05_the_job_that_survives_a_restart.py
```

**Supplied file:** [`examples/architecture-starts/05_the_job_that_survives_a_restart.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/05_the_job_that_survives_a_restart.py). You can also [read or download the source here](../../../../examples/architecture-starts/05_the_job_that_survives_a_restart.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
saved
stale worker rejected
{'epoch': 2, 'state': 'succeeded', 'title': 'Current title'}
```

### Run the application you will extend

The [reading-list API setup guide](../../../../examples/reading-list-starter/README.md) gives you a real local HTTP server, SQLite database, save/list/edit requests and controlled title success/timeout behavior. Start it in one terminal and send the documented `curl` requests from another. Read that setup before following the implementation steps below. The demo above isolates this lesson's mechanism; the server is where you integrate it.

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

Expect **201 Created**, a bookmark `id` and `title_status: "timeout"`. The URL is persisted despite the title failure. This is the supplied baseline; the assignment adds the behavior described above. The lookup is a fixture, so no external website is contacted. For members Bob or Ben in a scenario, use the starter's second demo identity `bob`; Alice or Ana corresponds to `alice`.

Work in your own branch or copy `examples/reading-list-starter/` to `work/05-the-job-that-survives-a-restart/`. `app.py` exists in that directory; add the modules named below there as you separate HTTP, storage and background work. The server has demo membership, not production authentication.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| jobs | bookmark_id,request_id,state,epoch,lease_until | Logical identity and ownership. |
| attempts | job_id,epoch,started,outcome | Separate retries under one job. |
| bookmark_title | bookmark_id,title,title_version | Updated conditionally by the winning job/source version. |

## Implement the assignment

### 1. Create a durable job transaction

In store.py, save the bookmark and job/outbox record together. Return a stable status URL after commit. A duplicate create request reuses the job identity; it does not schedule another logical fetch.

### 2. Implement worker ownership

In worker.py, claim due work using a conditional epoch increment and lease timestamp. Store attempt evidence. A queue’s visibility period only limits delivery overlap; the job-store condition decides who may publish.

### 3. Publish and acknowledge in order

Recheck bookmark source version and worker epoch before writing the title and succeeded state. Acknowledge after commit. On redelivery, a completed job is recognized and acknowledged without another visible result. Handle deleted bookmarks as cancellation rather than recreating them.

### 4. Add an operator repair path

Show oldest accepted job, attempt count, last error and next retry. After bounded attempts, move to failed/DLQ and allow an authorized replay retaining logical identity. A replay is evidence, not deletion of the previous failure history.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Epoch 2 wins; epoch 1 cannot replace the title. |
| Restart after result commit but before acknowledgement | Redelivery observes succeeded and finishes without another result. |
| Delete the bookmark while work waits | The worker records cancellation and does not recreate it. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100 saves/minute; two-second mean fetch | About 3.3 occupied worker slots at steady state; start with a small bounded pool. |
| Thirty-second lease | Renew only while the same epoch owns the job; a paused worker can lose ownership before it notices. |
| Five delivery attempts | Exhaustion becomes a visible failed/repair state, not an endlessly hidden queue retry. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Move title lookup into restartable background jobs: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/05-the-job-that-survives-a-restart.svg)

The queue wakes workers; the job record owns lifecycle and publication. Keeping those roles separate makes duplicate delivery and restarts understandable.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: bookmark API | Create routes and an integration; translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: bookmark application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: job and result authority | Design partition/sort keys and write a storage adapter with conditional updates or transactions; Python state and SQL are not uploaded as a database. |
| Local pending-work collection | Amazon SQS: title job queue | Publish committed job intent, consume messages and persist deduplication/ownership state; add visibility, retry and dead-letter handling. |
| Python operation or worker function | AWS Lambda: title worker | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local counters, timestamps and diagnostic output | Amazon CloudWatch: job operations | Emit bounded metrics and logs, build the named operational view and configure retention and access. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| SQS | Visibility greater than ordinary work duration, bounded redrive and a documented repair action. |
| DynamoDB | Conditional claims and result writes; TTL cleanup never substitutes for lease/expiry checks. |
| Worker | Outbound URL policy, total deadline and reserved concurrency protecting source/database capacity. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Let users edit the URL while an old fetch runs. Add a source URL version to the job and reject results for an earlier source even if the worker still owns its lease.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · A expires during work

**Changed requirement:** A resumes after expiry but before B claims. May it still commit? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Under this exercise’s strict policy, no: the commit checks both generation and lease validity using authoritative time. A must reacquire a new generation. This closes the gap where “owner matches” alone accepts an expired owner.

</details>

## Follow-up 2 · The provider charges per operation

**Changed requirement:** Replace the read with a billable enrichment API that succeeds but loses its response. Can you safely repeat? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use a provider-supported idempotency key or status lookup tied to the same operation identity. Otherwise record outcome unknown and reconcile before retrying a non-idempotent effect. Local fencing protects your store, not an external provider.

</details>

## Supplied mechanism practice

- [Lease and provider recovery lab](../../../04-scale-and-evolution/04-migrations/labs/recovery-migration/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
