# Evolve tag responses without breaking old clients

## Application background

A reading-list app shows tags beside each bookmark. Its existing mobile client receives strings such as `"databases"` and displays them directly. The new web interface needs a stable tag ID and a color so a tag can be renamed without losing its identity.

Replacing the strings with objects in the existing response would surprise old mobile code. Customers may keep that old app for months. The service needs to support both representations while clients move to the new one.

### Example walkthrough

| Action | Expected behavior |
|---|---|
| An old client requests bookmark tags | Return `["databases"]` in its supported representation. |
| A new client requests the new representation | Return objects such as `[{"id":"tag-7","name":"databases","color":"blue"}]`. |
| The tag is renamed | Keep `tag-7` as its identity while changing its display name. |

An API contract is the agreed request and response behavior that callers rely on. Compatibility means the supported older callers can continue to work during the change.

## Your assignment

**Deliver:** Implement old and new tag response formats from one stored model. Define how callers select a format and when support for the old one can end.

**Required behavior:** Keep tags as string[] for the supported old contract and add a separately named tagObjects field or explicit API version. Reject incompatible input clearly. Both representations derive from one canonical stored model.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope. The cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py
```

**Supplied file:** [`examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py). You can also [read or download the source here](../../../../examples/architecture-starts/04_the_api_that_does_not_break_its_callers.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only. It does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ. Compare the state transitions and outcomes.

```text
{'tags': ['databases'], 'tagObjects': [{'id': 't7', 'label': 'databases', 'color': 'blue'}]}
Old client: databases
New client: t7
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

Work in your own branch or copy `examples/reading-list-starter/` to `work/04-the-api-that-does-not-break-its-callers/`. `app.py` exists in that directory. Add the modules named below there as you separate HTTP, storage and background work. The server has demo membership, not production authentication.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| canonical_tags | tag_id,label,color,version | Single source of tag meaning. |
| legacy_adapter | canonical tags → string[] | Preserves field type and legacy ordering. |
| current_adapter | canonical tags → tagObjects[] | Explicit richer representation without reusing the old field type. |

## Implement the assignment

### 1. Capture actual caller behavior

Write down request/response examples used by supported clients, including nulls, empty lists, unknown fields and error shapes. Do not assume every client ignores additional fields. Use an explicit version if strict decoders require it.

### 2. Add a canonical model and adapters

Store tag IDs and metadata once. Build response serializers for the old and new contracts. Keep legacy tags as strings. Do not overload the same field with mixed types. Decide how old clients create or rename tags without stable IDs.

### 3. Run both client paths

Use a small old-client script that joins tag strings and a new-client script that reads IDs. Send both through the same application state. Check a real error response too. Compatible success bodies do not protect callers from changed error semantics.

### 4. Retire deliberately

Measure requests by explicit client/API version, publish the support window and keep an owner for the adapter. Remove it only after the agreed condition. Database migration and API retirement are separate steps.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | The old string-joining client and new ID-reading client both work. |
| Send an old tag-create request | The canonical model is updated through a defined adapter. |
| Remove tagObjects from a legacy response | The old client remains unaffected. Tags still has the same type. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target. The local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 90-day old-client support window | Keep compatibility until observed usage and policy allow retirement, not merely until the new UI ships. |
| 10,000 active clients. 15% old-version assumption | 1,500 clients would be affected by an in-place type change. |
| Two response shapes, one stored tag identity | Avoid independently mutable parallel fields that drift. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Evolve tag responses without breaking old clients: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/04-the-api-that-does-not-break-its-callers.svg)

Compatibility belongs at the application boundary. A managed gateway can route versions, but it cannot infer the meaning of tags or repair a changed JSON type for old callers.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: versioned HTTP entry | Create routes and an integration. Translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: compatibility application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: canonical tag records | Design partition/sort keys and write a storage adapter with conditional updates or transactions. Python state and SQL are not uploaded as a database. |
| Local static/media delivery path | Amazon CloudFront: current web client | Configure an origin, cache policy and private-content access. Distinguish cached bytes from current authorization. |
| Local counters, timestamps and diagnostic output | Amazon CloudWatch: compatibility usage | Emit bounded metrics and logs, build the named operational view and configure retention and access. |
| Local versioned configuration | AWS AppConfig: adapter configuration | Publish validated configuration versions and consume them with bounded caching and rollback behavior. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Routing | Keep version selection explicit and observable. Do not infer a contract from incidental user-agent text. |
| Data | One canonical tag representation. Adapters cannot independently overwrite competing copies. |
| Retirement | Record supported versions and usage evidence. Deployment remains independent of this curriculum exercise. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement. It is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Change units from milliseconds to seconds. Use a new field name or version and explicit conversion. Keeping a JSON number type does not preserve its semantic contract.

<details>
<summary>Follow-up scenarios and worked designs</summary>

## Follow-up 1 · Usage cannot be seen

**Changed requirement:** Both clients call the same URL, and the server cannot tell which JSON field they read. How do you measure retirement?

<details>
<summary>Worked design and implementation</summary>

Use explicit version/capability telemetry where feasible, client inventories and owner acknowledgments. Endpoint traffic alone cannot reveal field access. The removal decision must name uninstrumented and offline clients.

**Make retirement evidence specific.** A server log showing 10,000 calls to `/bookmarks` cannot tell whether a browser reads `duration_ms`. Add an explicit client contract version where you control clients and maintain an owner inventory for integrations you do not. Keep unknown traffic as its own category. An offline mobile client may not appear during the observation week.

Deliver a retirement table with client, version, owner, last observation and migration evidence. For a client with no telemetry, record the unsupported inference instead of calling it unused. A decision to break that client must be a named product decision.

</details>

## Follow-up 2 · A team misses the sunset

**Changed requirement:** One consumer cannot migrate before the announced date. Must the compatibility test turn green on removal anyway?

<details>
<summary>Worked design and implementation</summary>

No. A date is a policy input, not evidence of safety. Choose extended support, a versioned endpoint, or explicit accepted breakage with an owner. Revise the go/no-go gate accordingly.

**Offer a concrete compatibility path.** Keep the old endpoint or field interpretation behind a version adapter while the delayed consumer migrates. Put the conversion in one owned module rather than scattering old/new checks through business logic. Give the exception a review date and support owner.

For a milliseconds-to-seconds change, an old client receiving 1500 must still interpret 1.5 seconds. A new `duration_seconds: 1.5` field may coexist with `duration_ms: 1500`. Show both responses and a delayed-client request after the announced sunset. The date does not convert 1500 into 1.5 or prove the client stopped calling.

</details>

</details>
