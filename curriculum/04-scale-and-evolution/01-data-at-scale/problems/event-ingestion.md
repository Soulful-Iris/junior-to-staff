# Event ingestion: change a schema without losing yesterday

## What you are building

> Build telemetry ingestion for connected devices. Producers retry after timeouts, one firmware version emits malformed events, and analysts need to replay seven days of input after fixing a transformation. Accepted events must be recoverable even when one record cannot be processed.

**Working contract:** POST /events accepts a versioned envelope and stable producer/event identity. A success means durable acceptance under the stated storage policy. Invalid schemas are rejected or quarantined with a reason; they must not block unrelated partitions forever.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100,000 events/s burst; 1 KiB/event assumption | About 100 MiB/s and 8.85 TB/day decimal if sustained; peak duration changes the bill. |
| Seven-day replay retention | Roughly 62 TB raw at that sustained rate, before compression/replication. |
| Processing target: 30 seconds behind | Track oldest event age and partition lag, not just consumer process health. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/event_ingestion.py
```

[Open the starting code](../../../../examples/architecture-starts/event_ingestion.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| envelope | producer_id,event_id,schema_version,event_time | Stable identity and interpretation contract. |
| raw_objects | partition,time_range,checksum | Durable original bytes and replay manifest. |
| consumer_checkpoint | consumer,partition,offset | Progress coupled to durable output or replay-safe application. |

## AWS implementation

![Event ingestion: change a schema without losing yesterday: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/event-ingestion.svg)

Kinesis provides a transport and retention window; replay-safe outputs and checkpoints are still application responsibilities. S3 retains the input needed to rebuild a new processing generation.

## Build it in this order

### 1. Define durable acceptance

Validate envelope size and required identity before writing. Document whether success means the stream accepted the event or the archive contains it. If the producer retries, preserve its event ID; an HTTP request ID generated anew on every attempt cannot deduplicate the logical event.

### 2. Archive replayable input

Write original records into immutable objects with schema/version metadata and a manifest of partition ranges. Keep invalid-but-accepted records in a restricted quarantine with a reason. Preserve enough evidence to distinguish absent input from failed processing.

### 3. Couple output and progress

Process a bounded batch, commit output idempotently, then advance the checkpoint. A crash after output but before checkpoint causes replay, so the sink must reject duplicate event identities or apply deterministic versioned updates. Do not skip a poison record silently.

### 4. Replay into a new generation

Run corrected transformations into separate output tables/prefixes, compare counts and representative records, then move a versioned read pointer. Keep the original consumer checkpoint unchanged so replay cannot accidentally rewind live processing.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Stream capacity | Calculate from both records/s and bytes/s, review current account limits and hot partition keys. |
| Archive retention | Seven-day exercise retention with lifecycle rules; restrict raw data and quarantine readers. |
| Consumer limits | Bound batch bytes and execution time; alarms identify stalled partitions rather than averaging them away. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | e1 is applied once; unsupported e2 is quarantined. |
| Crash after writing a batch | Replay leaves one logical output per identity. |
| Replay seven-day input | New output generation can be inspected before switching readers. |

## The next design decision

Change an event field from cents to decimal currency. Introduce an explicit schema version and conversion rule; identical field names do not make historical data semantically compatible.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



**Your contract.** Assume 100,000 events/s during bursts, seven-day stream retention for the exercise, and an immutable long-term raw store. Say whether clients have clocks you trust; the answer changes event-time semantics. This is an original practice prompt.

| Input | Expected behavior |
|---|---|
| Old reading `temp=32` without unit | Decode as old schema version using explicitly documented unit |
| New reading `temp=32, unit=F` | Normalize using versioned schema; don't silently mix F and C |
| Device retries event `e4` | Dedupe by device/event ID within declared window; replay remains safe |
| Event arrives 9 minutes late | Raw event retained; dashboard revision follows chosen watermark and correction policy |

## Preserve the record before its projections

Assign producer ID, event ID, schema version, and both event and receipt times. Validate envelopes at ingress; quarantine undecodable records instead of losing them. Store immutable raw events for replay, then run separately versioned normalization and aggregation consumers. Partition by a key that distributes load without losing the ordering you actually need (typically per device). A stream preserves order within a shard, not a global order. Changing a schema means a decoder strategy and backward/forward compatibility tests, not just adding a column.

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| Amazon Kinesis Data Streams (event stream) | Buffer and replay ordered per-shard events during retention | Amazon MSK (managed Kafka) when the ecosystem or partition control requires Kafka |
| Amazon S3 (raw archive) | Retain immutable event bytes beyond stream retention | Long-retention Kafka tier if replay and operational trade-offs warrant it |
| AWS Lambda (transform worker) | Validate versions, normalize, and quarantine bad records | Amazon ECS for heavy sustained compute or custom batching |
| Amazon DynamoDB (materialized view) | Serve latest per-device or window state through key lookups | Amazon Timestream for time-series queries with its own data model |
| Amazon SQS (quarantine queue) | Hold parse failures for investigation and repair | S3 error prefix for bulk triage when individual queue actions aren't useful |

On-demand Kinesis scaling does not automatically isolate a single hot partition key; choose device partitions and estimate the hottest device and aggregate separately. Reprocessing the archive must use idempotent output versioning to avoid doubles.

**Senior follow-up:** An old firmware bug sends wrong units for a week. Recompute one week's dashboard without hiding production freshness; distinguish corrected totals and previously displayed totals.

**Staff follow-up:** Different regions use different retention rules and models. Define schema ownership, quality gates, replay budgets, and evidence that migrations preserved counts.

**Practice artifact:** Draw raw vs derived stores; walk the four inputs; define an envelope and one compatibility test. State the exact partition key and its hot-key risk.

**Source boundary:** Original scenario inspired by [Meta's May 2026 ingestion migration account](https://engineering.fb.com/2026/05/12/data-infrastructure/migrating-data-ingestion-systems-at-meta-scale/), not a reported interview prompt. [Kinesis sizing documentation](https://docs.aws.amazon.com/streams/latest/dev/how-do-i-size-a-stream.html) supplies a current service constraint.

</details>
