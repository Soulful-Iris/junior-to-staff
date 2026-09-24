# Evolve tag responses without breaking old clients

## Application background

A reading-list API supplies bookmarks and tags to independently released browser and mobile clients. Old clients understand string tags; a new interface wants stable tag IDs and colors.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** Define and implement compatible old/new response representations, a version-selection rule and a dated retirement plan.

Evolve a reading-list API whose mobile clients expect tags as strings. The new web UI needs tag IDs and display colors. Some mobile clients will not update for ninety days, so replacing tags with objects in place would break supported callers.

**Required behavior:** Keep tags as string[] for the supported old contract and add a separately named tagObjects field or explicit API version. Reject incompatible input clearly. Both representations derive from one canonical stored model.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope; the cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py
```

**Supplied file:** [`examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py). You can also [read or download the source here](../../../../examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
{'tags': ['databases'], 'tagObjects': [{'id': 't7', 'label': 'databases', 'color': 'blue'}]}
Old client: databases
New client: t7
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

Work in your own branch or copy `examples/reading-list-starter/` to `work/04-the-api-that-does-not-break-its-callers/`. `app.py` exists in that directory; add the modules named below there as you separate HTTP, storage and background work. The server has demo membership, not production authentication.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| canonical_tags | tag_id,label,color,version | Single source of tag meaning. |
| legacy_adapter | canonical tags → string[] | Preserves field type and legacy ordering. |
| current_adapter | canonical tags → tagObjects[] | Explicit richer representation without reusing the old field type. |

## Implement the assignment

### 1. Capture actual caller behavior

Write down request/response examples used by supported clients, including nulls, empty lists, unknown fields and error shapes. Do not assume every client ignores additional fields; use an explicit version if strict decoders require it.

### 2. Add a canonical model and adapters

Store tag IDs and metadata once. Build response serializers for the old and new contracts. Keep legacy tags as strings; do not overload the same field with mixed types. Decide how old clients create or rename tags without stable IDs.

### 3. Run both client paths

Use a small old-client script that joins tag strings and a new-client script that reads IDs. Send both through the same application state. Check a real error response too; compatible success bodies do not protect callers from changed error semantics.

### 4. Retire deliberately

Measure requests by explicit client/API version, publish the support window and keep an owner for the adapter. Remove it only after the agreed condition; database migration and API retirement are separate steps.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | The old string-joining client and new ID-reading client both work. |
| Send an old tag-create request | The canonical model is updated through a defined adapter. |
| Remove tagObjects from a legacy response | The old client remains unaffected; tags still has the same type. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 90-day old-client support window | Keep compatibility until observed usage and policy allow retirement, not merely until the new UI ships. |
| 10,000 active clients; 15% old-version assumption | 1,500 clients would be affected by an in-place type change. |
| Two response shapes, one stored tag identity | Avoid independently mutable parallel fields that drift. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Evolve tag responses without breaking old clients: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/04-the-api-that-does-not-break-its-callers.svg)

Compatibility belongs at the application boundary. A managed gateway can route versions, but it cannot infer the meaning of tags or repair a changed JSON type for old callers.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: versioned HTTP entry | Create routes and an integration; translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: compatibility application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: canonical tag records | Design partition/sort keys and write a storage adapter with conditional updates or transactions; Python state and SQL are not uploaded as a database. |
| Local static/media delivery path | Amazon CloudFront: current web client | Configure an origin, cache policy and private-content access; distinguish cached bytes from current authorization. |
| Local counters, timestamps and diagnostic output | Amazon CloudWatch: compatibility usage | Emit bounded metrics and logs, build the named operational view and configure retention and access. |
| Local versioned configuration | AWS AppConfig: adapter configuration | Publish validated configuration versions and consume them with bounded caching and rollback behavior. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Routing | Keep version selection explicit and observable; do not infer a contract from incidental user-agent text. |
| Data | One canonical tag representation; adapters cannot independently overwrite competing copies. |
| Retirement | Record supported versions and usage evidence; deployment remains independent of this curriculum exercise. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Change units from milliseconds to seconds. Use a new field name or version and explicit conversion; keeping a JSON number type does not preserve its semantic contract.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · Usage cannot be seen

**Changed requirement:** Both clients call the same URL, and the server cannot tell which JSON field they read. How do you measure retirement? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use explicit version/capability telemetry where feasible, client inventories and owner acknowledgments. Endpoint traffic alone cannot reveal field access; the removal decision must name uninstrumented and offline clients.

</details>

## Follow-up 2 · A team misses the sunset

**Changed requirement:** One consumer cannot migrate before the announced date. Must the compatibility test turn green on removal anyway? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

No. A date is a policy input, not evidence of safety. Choose extended support, a versioned endpoint, or explicit accepted breakage with an owner; revise the go/no-go gate accordingly.

</details>

</details>
