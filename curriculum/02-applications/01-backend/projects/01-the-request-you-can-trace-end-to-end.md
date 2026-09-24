# Trace requests through a bookmark API

## Application background

A research team saves documentation URLs in a shared reading list. The API first commits the URL, then tries to obtain a display title; a title timeout should not undo the save. Support needs to reconstruct one caller's request among concurrent requests.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** Instrument the supplied HTTP API and create a command that reconstructs one request from its response ID without logging secret URL values.

Add request tracing to a bookmark API used by a 50-person research team. At 10:00, Ana’s save succeeds but its title lookup times out while Ben’s request completes normally. Support has only Ana’s response ID and must reconstruct her request without seeing a secret-bearing URL.

**Required behavior:** Every response includes a trusted request ID. Structured events carry that ID through authentication, database work and title lookup. Durations use a monotonic clock; logs omit tokens and private URL values.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope; the cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/01_the_request_you_can_trace_end_to_end.py
```

**Supplied file:** [`examples/architecture-starts/01_the_request_you_can_trace_end_to_end.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/01_the_request_you_can_trace_end_to_end.py). You can also [read or download the source here](../../../../examples/architecture-starts/01_the_request_you_can_trace_end_to_end.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
{"request_id": "A", "event": "auth.ok"}
{"request_id": "B", "event": "auth.ok"}
{"request_id": "A", "event": "bookmark.saved"}
{"request_id": "B", "event": "bookmark.saved"}
… (more output follows)
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

Work in your own branch or copy `examples/reading-list-starter/` to `work/01-the-request-you-can-trace-end-to-end/`. `app.py` exists in that directory; add the modules named below there as you separate HTTP, storage and background work. The server has demo membership, not production authentication.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| request_context | request_id,subject,started_monotonic | Per-request scope, not a mutable global variable. |
| log_event | event,request_id,operation_id,duration_ms,outcome | Stable JSON schema with bounded safe fields. |
| trace_request.py | request_id plus JSONL input | Prints only the selected request and identifies missing completion evidence. |

## Implement the assignment

### 1. Instrument the actual request boundary

Start in `Handler.dispatch()` in the supplied `app.py`: create a UUID for this request and keep it in request-local context until the response finishes. Update `Handler.reply()` to return it as `X-Request-ID`. If you later accept an upstream ID, validate its length and origin at a trusted edge. Reject control characters. Put the same ID in the JSON error body; never use a process-global current_request variable.

### 2. Trace each operation

Emit events after the demo membership check, after the bookmark transaction commits, and after `lookup_title()` returns. Give each operation an ID and measure its elapsed time with `time.monotonic()`. Write one JSON object per line to a local log file; reserve stdout for a startup message if you need it. Store URL host or a controlled hash only if useful; omit path/query secrets. A saved bookmark and a failed title lookup are separate outcomes and should not become one misleading request-failed message.

### 3. Build the support command

Create `trace_request.py` beside your modified `app.py`. Make `python3 trace_request.py --request-id <id> --log <path>` filter JSONL by exact request ID and print phase, duration and outcome. The command is a deliverable you write, not a supplied command yet. If a completion event is missing, report unknown/incomplete evidence rather than inventing success. Run two concurrent requests and show each isolated story.

### 4. Optional extension: carry identity into jobs

When title lookup becomes asynchronous, commit job_id and parent_request_id with dispatch intent. Each retry gets a new attempt ID under the same job. Bound diagnostic buffering when the log destination fails, and count dropped events without recursive logging.

## Demonstrate the completed local result

After steps 1–3, repeat the `curl -i` request above and copy `X-Request-ID` from its response. Run your new support command with that ID. It should show membership accepted, bookmark committed, and title timed out for that one request. Send another request as `bob` with `title_mode: "ok"`; its events must have a different ID. A request without `X-Demo-User` should return 401 with its own traceable ID.

| Action | Expected visible result |
|---|---|
| Run the starting program | A and B interleave while every event retains its own request ID. |
| Send a newline-containing client ID | The trusted boundary replaces or rejects it; no forged log line appears. |
| Stop title lookup | The record remains saved and support sees the separate timeout. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 50 concurrent requests; three operations/request | At least 150 interleaved operation timelines; wall-clock sorting alone cannot assign causality. |
| 500 ms title-fetch deadline | Record a title.timeout event while keeping the saved bookmark outcome explicit. |
| 1 KiB/event × six events/request assumption | 6 KiB/request of diagnostics before sampling/retention decisions. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Trace requests through a bookmark API: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/01-the-request-you-can-trace-end-to-end.svg)

CloudWatch stores structured events, but correct attribution comes from request-local context and explicit propagation. The same schema works with local JSONL before any cloud deployment.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: trusted HTTP entry | Create routes and an integration; translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: bookmark request handler | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: bookmark and job state | Design partition/sort keys and write a storage adapter with conditional updates or transactions; Python state and SQL are not uploaded as a database. |
| Local pending-work collection | Amazon SQS: asynchronous title work | Publish committed job intent, consume messages and persist deduplication/ownership state; add visibility, retry and dead-letter handling. |
| Python operation or worker function | AWS Lambda: title lookup worker | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local diagnostic events | Amazon CloudWatch Logs: diagnostic event store | Emit structured JSON from the deployed runtime and configure log delivery, retention and query permissions. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Log groups | Explicit retention and scoped query access; no raw authorization headers or private URLs. |
| Runtime context | Reset request context after completion; queue messages carry identity as data. |
| Delivery | Diagnostic logging uses bounded buffering; durable audit evidence would require a different commit contract. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Join work across three services with imperfect clocks. Add parent/child span relationships and elapsed durations; do not infer cross-host causality from timestamps alone.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · The title becomes a queued job

**Changed requirement:** The response finishes before the worker starts. How do support and operations join the story? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Store job ID and parent request ID in the enqueue transaction and propagate them as data. The worker has its own attempt ID; retries are distinct attempts linked to one job.

</details>

## Follow-up 2 · Logging fails

**Changed requirement:** The log destination is temporarily unavailable. Should user work stop? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Choose bounded buffering/drop counters for ordinary diagnostics; handle audit events according to their stronger contract. Bound memory, alarm on lost evidence, and avoid recursive logging failures.

</details>

</details>
