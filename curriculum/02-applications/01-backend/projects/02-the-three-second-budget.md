# Enforce a single deadline across API dependencies

## Application background

A bookmark API enriches a saved URL with a page title. Authentication, storage, remote lookup and response writing all consume the same caller-visible time budget.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** Add one request deadline, bounded dependency calls and a retry decision that cannot reset the caller's three-second budget.

Build a bookmark preview endpoint with a three-second response deadline. Authentication and the database use 300 ms, the response needs 100 ms, and the remote page sometimes times out. The service must decide whether a retry can still finish within the original deadline.

**Required behavior:** One request owns one three-second budget. Every attempt, backoff and queue wait consumes it. Return the saved bookmark with an explicit unavailable preview when optional fetching cannot finish in time.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope; the cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/02_the_three_second_budget.py
```

**Supplied file:** [`examples/architecture-starts/02_the_three_second_budget.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/02_the_three_second_budget.py). You can also [read or download the source here](../../../../examples/architecture-starts/02_the_three_second_budget.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
attempt 1 timeout 1200 ms
attempt 2 timeout 1200 ms
elapsed with response reserve: 3000 ms
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

Work in your own branch or copy `examples/reading-list-starter/` to `work/02-the-three-second-budget/`. `app.py` exists in that directory; add the modules named below there as you separate HTTP, storage and background work. The server has demo membership, not production authentication.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| deadline | monotonic_start,total_budget | Remaining time decreases across every phase. |
| fetch_attempt | request_id,attempt,timeout_ms,outcome | Distinct attempt evidence under one operation. |
| preview_result | available,title or reason | Optional failure does not erase committed bookmark state. |

## Implement the assignment

### 1. Pass a deadline through the call graph

Create it once at ingress using a monotonic clock. Helpers accept remaining time or a deadline object rather than independent default timeouts. Include semaphore/pool acquisition time; waiting for a socket is still request time.

### 2. Classify retryable outcomes

Retry a transient connect failure or selected 5xx only when the operation is safe and the remaining budget covers another useful attempt. Respect a bounded Retry-After. Do not repeat a non-idempotent effect because a response was lost.

### 3. Bound the outbound path

Set connect/read/total deadlines, response byte limit and a concurrency semaphore. Release resources on cancellation. If a timed-out task continues running in the background, its resource use still counts against the service.

### 4. Make the user-visible fallback explicit

Return the saved bookmark and preview_status unavailable with a reason safe for users. Record attempts and remaining budget for operators. Re-run with an extra 100 ms of queue waiting and show that the second attempt shrinks or disappears.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Two attempts plus backoff fit exactly inside 3,000 ms with the response reserve. |
| Add queue waiting | The later attempt loses time rather than extending the request deadline. |
| Make preview unavailable | The bookmark is still returned with a truthful preview state. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 3,000 ms total − 300 ms auth/database − 100 ms response | 2,600 ms remain for fetch attempts and backoff. |
| Two 1,200 ms attempts plus 200 ms backoff | Exactly 2,600 ms; any additional delay requires shortening or skipping the second attempt. |
| 100 concurrent requests × two possible attempts | Up to 200 calls over their lifetimes, but instantaneous outbound concurrency must remain bounded. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Enforce a single deadline across API dependencies: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/02-the-three-second-budget.svg)

The application owns the end-to-end budget. Gateway and runtime timeouts are outer limits, not a substitute for carrying remaining time into each dependency call.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: deadline entry point | Create routes and an integration; translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: preview application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: bookmark authority | Design partition/sort keys and write a storage adapter with conditional updates or transactions; Python state and SQL are not uploaded as a database. |
| Controlled title/page fixture | Public website: external title source | Implement an outbound HTTP adapter with address/redirect validation, bounded work and explicit observation outcomes. |
| Local counters, timestamps and diagnostic output | Amazon CloudWatch: attempt telemetry | Emit bounded metrics and logs, build the named operational view and configure retention and access. |
| Local versioned configuration | AWS AppConfig: fetch limits | Publish validated configuration versions and consume them with bounded caching and rollback behavior. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Timeouts | Configure infrastructure timeouts above the application’s three-second response contract; the app stops useful work earlier. |
| Outbound limits | Fixed concurrency and response-size cap; retries share the original admission budget. |
| Metrics | Count logical requests and attempts separately so a retry storm cannot masquerade as increased demand. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Add parallel metadata providers. Cancel losing requests, cap total fan-out and decide whether one successful provider is enough to finish the request.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · The response is lost

**Changed requirement:** The create committed but the connection broke. The same key is retried concurrently. What is atomic? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

The deduplication record and stored item/result must commit together. Replays return the recorded result; key reuse with different content returns conflict. A separate marker before an external side effect is not enough.

</details>

## Follow-up 2 · Several layers retry

**Changed requirement:** Client, API and SDK each permit three attempts. How many leaf calls can occur? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

The maximum is 3×3×3=27; three retries after the initial attempt would be 4×4×4=64. Disable redundant retry layers, then assert the actual dependency call count and remaining deadline.

</details>

</details>
