# Aggregate click events with late arrivals and reconciliation

## Application background

An advertiser opens a dashboard to see how many people clicked each campaign. Click messages include an event ID and the time the click happened. They may arrive twice or reach your service minutes after the actual click.

The dashboard should update quickly, but finance needs a more carefully reconciled count for billing. Those outputs can have different completion rules as long as the interface makes the difference visible.

### Example walkthrough

| Action | Expected behavior |
|---|---|
| Click `c-17` arrives twice | Count one click under the duplicate policy. |
| A click from 12:00 arrives at 12:02 | Apply the stated rule for updating the earlier reporting window. |
| Finance prepares a bill | Use the reconciled record rather than treating the live dashboard as final. |

Event time is when the click happened. Arrival time is when your service received it. Windowed reports must choose which time they use and how late corrections work.

## Your assignment

**Deliver:** Build campaign counts that handle repeated and late clicks. Address unusually busy campaigns and distinguish provisional dashboard values from reconciled billing evidence.

**Required behavior:** Aggregate by campaign and event-time window with a documented duplicate window and late-arrival policy. Dashboard values are provisional until finalized. Reporting counts are not automatically a charge ledger.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope. The cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/ad_click_aggregator.py
```

**Supplied file:** [`examples/architecture-starts/ad_click_aggregator.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/ad_click_aggregator.py). You can also [read or download the source here](../../../../examples/architecture-starts/ad_click_aggregator.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only. It does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ. Compare the state transitions and outcomes.

```text
e1 duplicate
e3 too late: reconciliation path
Provisional counts: {('c7', 60): 1, ('c7', 0): 1}
```

### Set up your implementation workspace

Create `work/ad-click-aggregator/` in your checkout (or use a separate repository). Copy the supplied mechanism into that directory as `mechanism.py`, then extract its state transitions into functions you can call from your implementation. The record and module names below describe what you must implement. They are not a promise that files with those names already exist. Keep a `README.md` beside your implementation with its exact run commands and observed results.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| clicks | event_id,campaign,event_time,received_time | Original identity and both clocks. |
| window_state | campaign,window_start,shard | Deduplication and partial event-time counts. |
| reports | campaign,window,revision,finalized | Versioned aggregates served to advertisers. |

## Implement the assignment

### 1. Ingest a stable click envelope

Preserve event ID from the event producer, campaign and event timestamp, and add received time at ingestion. Validate timestamp bounds so a future-dated event cannot advance watermarks arbitrarily. Keep attribution policy version with derived results.

### 2. Aggregate event-time windows

Define window boundaries, watermark source and allowed lateness. Deduplicate within the declared replay horizon, checkpoint state with progress, and emit revisions when a late accepted event changes a prior window. Show provisional/final status in the API.

### 3. Shard hot campaigns

Split one campaign into deterministic partial counters and merge them for serving. Estimate both write distribution and merge work. A random shard suffix does not solve duplicate identity unless every replay chooses the same shard.

### 4. Reconcile billing separately

Preserve the evidence needed for invalid-traffic filtering, attribution corrections and financial reconciliation. A fast dashboard may undercount during lag. Do not convert an approximate or revisable count directly into irreversible charges.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Duplicate e1 is ignored, e2 updates an older window, and e3 goes to late reconciliation. |
| Pause a partition | The freshness indicator reveals lag rather than presenting the count as complete. |
| Replay a corrected attribution rule | Publish a new report version and explain the change. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target. The local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Five billion clicks/day | About 57,870 events/s average. Burst and largest-campaign rate need separate estimates. |
| Thirty-second dashboard freshness | Budget transport, aggregation and serving delay. Late input can still revise an older window. |
| Two-year reporting history | Store compact window aggregates. Raw-event retention and billing evidence have separate policies. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Aggregate click events with late arrivals and reconciliation: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/ad-click-aggregator.svg)

The stream processor owns provisional event-time state, the serving table owns a particular published revision, and the archive supports rebuilding. Those are distinct guarantees from a billing ledger.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local event sequence or input stream | Amazon Kinesis: click event transport | Implement producer/consumer adapters, partition keys, durable acceptance and checkpoint/replay behavior. |
| Local window/aggregation loop | Managed Service for Apache Flink: window aggregation | Implement stream processing with state, checkpoints, event-time handling and a declared late-event policy. |
| Local file, object fixture or exported payload | Amazon S3: raw click archive | Implement upload/download and metadata adapters, scoped access, object naming, retention and incomplete-upload cleanup. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: serving aggregates | Design partition/sort keys and write a storage adapter with conditional updates or transactions. Python state and SQL are not uploaded as a database. |
| Application or worker process | Amazon ECS: reporting API | Build a container and task definition. Supply configuration, task roles and graceful shutdown behavior. |
| Local counters, timestamps and diagnostic output | Amazon CloudWatch: data freshness metrics | Emit bounded metrics and logs, build the named operational view and configure retention and access. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Flink job | Configure checkpoint storage and a documented watermark/late-data policy. Size keyed state from dedup horizon. |
| Serving table | Use campaign/time access patterns and conditional aggregate revisions to reject old writes. |
| Archive | Partition by received date and preserve original event time. Control access to user/device identifiers. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement. It is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works
### Worked follow-up: Separate revisable click reports from finalized invoices

An advertiser paid for yesterday's clicks using fraud policy 3. Recomputing the dashboard with policy 4 may lower the count, but overwriting the invoice would erase what was actually charged.

| Starting design | Changed requirement |
|---|---|
| Late events can revise dashboard aggregates. | A finalized invoice must remain explainable after fraud policy changes. |

**Revised architecture.** Follow the changed responsibility and failure path below. This is a design to implement. The supplied local example does not provision these components.

```mermaid
flowchart TD
E["Retained click events"] --> D["Revisable dashboard aggregates"]
 E --> F["Versioned invoice calculation"]
 F --> I["Final invoice evidence"]
 E --> N["New fraud policy calculation"]
 N --> A["Adjustment referencing invoice"]
 I --> A
```

**What to implement.** Keep raw event IDs and versioned metric definitions. At invoice finalization, retain the time range, attribution policy, fraud version and evidence manifest used for its lines. Later corrections create adjustment entries that reference the original invoice. The dashboard can show a newer provisional generation with its own watermark. Use the warehouse for recomputation and a transactional billing ledger for final documents and adjustments.

**Walk through the result.** Invoice I contains 1,000 billable clicks under policy 3. Policy 4 excludes 100 of those clicks. Show the original invoice unchanged, a separately approved adjustment for 100 and a dashboard count of 900 under policy 4. Deliver the three linked records and explain which is authoritative for each question.




An advertiser disputes yesterday’s invoice after fraud filtering changes. Define immutable invoice evidence, correction entries and the relationship between a revisable dashboard and a finalized financial document.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 5 billion events/day, 30-second dashboard freshness and two years of historical queries. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Duplicate click | SDK retries event id `x91` | Deduplicate within the stated window or expose count semantics. |
| Late click | Event timestamp 12:03 arrives at 12:07 | Revise the correct event-time bucket with versioned result. |
| High-cardinality | Millions of campaigns × regions × devices | Bound dimensions and partition for both writes and analytics scans. |
| Dashboard read | Query campaign for last 60 minutes | Return freshness/watermark with aggregated buckets. |

## Think from the contract to the boxes

Ingest immutable event IDs, event-time and dimensions, then aggregate in event-time windows. Watermarks decide when a window is provisionally complete. Late arrivals update a correction path. Keep an append-only raw archive for replay. Pre-aggregation serves dashboards cheaply, while an OLAP store handles historical multi-dimensional slices. Do not force one database to serve both paths.

**First diagram:** Draw click → stream → event-time windows → hot aggregate and raw archive. Show a late event correcting one bucket.

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon Kinesis Data Streams** / event stream | Buffer and replay high-volume click records. | MSK where Kafka ecosystem and partition control fit better. |
| **Amazon Managed Service for Apache Flink** / windowed aggregation | Manage keyed state, event time and late records. | Lambda for simpler non-windowed consumers. |
| **Amazon S3** / raw event archive | Retain immutable events for recompute and audit. | Glacier tiers for older, rarely queried raw data. |
| **Amazon Redshift** / analytics warehouse | Query dimensional history for advertiser reporting. | Athena on partitioned Parquet for lower-frequency scans. |
| **Amazon DynamoDB** / recent aggregate view | Serve hot recent buckets by campaign/time key. | Timestream for primarily time-series reads with lower dimensions. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

## Pressure-test the design

**Follow-up: 12:03 bucket receives an event at 12:07. Show provisional result, watermark advance, correction and the freshness marker in the dashboard.**

**Senior expectation:** A single advertiser becomes a hot partition and report requests scan too much history. Salt writes, merge on read, and cap query ranges with an async export path.

**Staff expectation:** Products disagree about attribution windows and fraud filtering. Version event schemas and metric definitions, measure reconciliation gaps, and provide backfills without rewriting history invisibly.

**Practice artifact:** Draw click → stream → event-time windows → hot aggregate and raw archive. Show a late event correcting one bucket. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists ad-click aggregation at Meta, Rippling, Google, Amazon and others. No date is attached to each report. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/ad-click-aggregator/cm4t0kxb6004488il22wqa2nn).

</details>
