# Keep bookmark saves usable when title lookup fails

## Application background

Alice saves a URL in a reading list. The URL itself is useful even if the app cannot immediately show the page's title. Normally the server gets that title from the linked website, but today the website takes eight seconds to respond.

The reading-list interface has a 500 ms response budget. It should return the saved URL promptly and explain the missing title. A previously stored title may help only if it belongs to the right content and is still recent enough.

### The supplied slow-dependency simulation

This is the `lookup_title()` function from the local starter. Its two modes make the same situation reproducible without an external website:

```python
def lookup_title(mode):
    """Replace this fixture with a bounded, SSRF-safe adapter in that exercise."""
    if mode == "timeout":
        time.sleep(0.5)
        return None, "timeout"
    return "Example documentation", "ready"
```

`None` means no title was obtained. The bookmark was saved before this function ran. Your extension must preserve that useful result while applying the real response budget and fallback policy.

Graceful degradation means keeping a useful part of the product working when an optional part fails. The assignment must say exactly which result remains usable.

## Your assignment

**Deliver:** Keep authorized bookmark reads and saves usable when title lookup is slow. Define which missing or previously stored title the interface may display, and show the degraded status.

**Required behavior:** Core list reads come from authorized local records. Optional titles can be pending or bounded-stale under an explicit policy. Every fallback preserves current authorization, and recovery probes use bounded concurrency.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope. The cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/degrade_do_not_stop.py
```

**Supplied file:** [`examples/architecture-starts/degrade_do_not_stop.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/degrade_do_not_stop.py). You can also [read or download the source here](../../../../examples/architecture-starts/degrade_do_not_stop.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only. It does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ. Compare the state transitions and outcomes.

```text
Provider unavailable; return local list: [{'url': 'https://example.invalid/a', 'title': 'Old title', 'title_status': 'stale'}]
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

Work in your own branch or copy `examples/reading-list-starter/` to `work/degrade-do-not-stop/`. `app.py` exists in that directory. Add the modules named below there as you separate HTTP, storage and background work. The server has demo membership, not production authentication.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| saved_links | owner,id,url,title,title_observed_at | Core local data and optional metadata age. |
| provider_health | state,failures,next_probe,probe_budget | Closed/open/half-open behavior. |
| list_response | link,display_title,title_status | Explicit useful degraded result. |

## Implement the assignment

### 1. Separate core and optional work

Implement list reads without a live title-provider dependency. Save URLs before enrichment and return title_status pending when no title exists. The browser renders useful links immediately and does not replace the whole page with a spinner for optional metadata.

### 2. Define safe stale serving

Scope cached records by owner/group and reauthorize before returning them. Check observed age against the title policy. Do not use the same stale allowance for permissions, payment state or other fields whose semantics require current truth.

### 3. Bound failure and recovery

Use a short provider deadline, bounded queue and circuit state to stop repeated doomed calls. In half-open state, allow a small controlled number of probes and gradually restore traffic. Cache refresh jobs remain idempotent and version-aware.

### 4. Expose the degraded experience

Show saved URL and stale/pending label without alarming the user with internal stack traces. Record fallback rate, age and core latency for operators. If critical demand itself exceeds capacity, apply explicit admission rather than pretending optional-work removal solves every overload.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Ana receives her link with stale title state. Ben’s cached content is excluded. |
| Make the provider take eight seconds | Core reads stay within their measured local budget. |
| Restore the provider | Only the bounded probe share runs before full traffic resumes. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target. The local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Eight-second provider time. 500 ms list deadline | The list cannot synchronously wait for the provider and still meet the contract. |
| One-hour cached-title freshness allowance assumption | Show stale/pending state. The value’s age is checked before fallback. |
| 1,000 simultaneous readers after recovery | Half-open probes need a small shared budget, not one probe per waiting request. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Keep bookmark saves usable when title lookup fails: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/degrade-do-not-stop.svg)

The queue isolates optional enrichment from core reads. The user-facing contract remains useful because the local record is sufficient to open the saved link.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local static/media delivery path | Amazon CloudFront: reading-list UI | Configure an origin, cache policy and private-content access. Distinguish cached bytes from current authorization. |
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: list API | Create routes and an integration. Translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: core list application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: saved-link authority | Design partition/sort keys and write a storage adapter with conditional updates or transactions. Python state and SQL are not uploaded as a database. |
| Local pending-work collection | Amazon SQS: deferred title refresh | Publish committed job intent, consume messages and persist deduplication/ownership state. Add visibility, retry and dead-letter handling. |
| Application or worker process | Amazon ECS: provider fetch workers | Build a container and task definition. Supply configuration, task roles and graceful shutdown behavior. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Core path | No synchronous dependency on remote title success. Deadline fits local work. |
| Worker pool | Independent concurrency and breaker probe budget. Failure cannot exhaust API connections. |
| Cache policy | Explicit age and ownership checks on every fallback, with visible pending/stale state. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement. It is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Add an optional AI summary. Give it its own latency/cost budget and source-version identity. A failed summary must not remove access to the saved article.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · The provider recovers

**Changed requirement:** The breaker opens, then probes recovery. How many requests probe at once? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use a bounded half-open probe set, not all waiting callers. Close only according to tested success criteria. A failed probe returns to the open state while the fallback remains usable.

</details>

## Follow-up 2 · Everything is high priority

**Changed requirement:** Critical arrivals exceed capacity even after optional work is disabled. What gives? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Bound interactive admission too. Choose finite queueing or fast overload response, reserve recovery capacity, and report denied critical work. Priority cannot guarantee service beyond capacity.

</details>

</details>
