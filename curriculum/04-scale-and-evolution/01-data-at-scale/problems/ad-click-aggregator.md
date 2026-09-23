# Ad click aggregator: count late events once

> **Interviewer:** “Advertisers want minute-level click and impression counts. Events arrive more than once and sometimes minutes late; dashboards need recent counts while analysts query years of history.”

This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 5 billion events/day, 30-second dashboard freshness and two years of historical queries. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Duplicate click | SDK retries event id `x91` | Deduplicate within the stated window or expose count semantics. |
| Late click | Event timestamp 12:03 arrives at 12:07 | Revise the correct event-time bucket with versioned result. |
| High-cardinality | Millions of campaigns × regions × devices | Bound dimensions and partition for both writes and analytics scans. |
| Dashboard read | Query campaign for last 60 minutes | Return freshness/watermark with aggregated buckets. |

![The failure path and repaired design for Ad click aggregator](../../../../assets/design-interview/ad-click-aggregator-before.svg)

## Think from the contract to the boxes

Ingest immutable event IDs, event-time and dimensions, then aggregate in event-time windows. Watermarks decide when a window is provisionally complete; late arrivals update a correction path. Keep an append-only raw archive for replay. Pre-aggregation serves dashboards cheaply, while an OLAP store handles historical multi-dimensional slices. Do not force one database to serve both paths.

**First diagram:** Draw click → stream → event-time windows → hot aggregate and raw archive; show a late event correcting one bucket.

![AWS services named with their provider-neutral architectural roles](../../../../assets/design-interview/ad-click-aggregator-aws.svg)

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon Kinesis Data Streams** / event stream | Buffer and replay high-volume click records. | MSK where Kafka ecosystem and partition control fit better. |
| **Amazon Managed Service for Apache Flink** / windowed aggregation | Manage keyed state, event time and late records. | Lambda for simpler non-windowed consumers. |
| **Amazon S3** / raw event archive | Retain immutable events for recompute and audit. | Glacier tiers for older, rarely queried raw data. |
| **Amazon Redshift** / analytics warehouse | Query dimensional history for advertiser reporting. | Athena on partitioned Parquet for lower-frequency scans. |
| **Amazon DynamoDB** / recent aggregate view | Serve hot recent buckets by campaign/time key. | Timestream for primarily time-series reads with lower dimensions. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

![A focused failure, capacity, or state diagram for Ad click aggregator](../../../../assets/design-interview/ad-click-aggregator-deep.svg)

## Pressure-test the design

**Follow-up: 12:03 bucket receives an event at 12:07. Show provisional result, watermark advance, correction and the freshness marker in the dashboard.**

**Senior expectation:** A single advertiser becomes a hot partition and report requests scan too much history. Salt writes, merge on read, and cap query ranges with an async export path.

**Staff expectation:** Products disagree about attribution windows and fraud filtering. Version event schemas and metric definitions, measure reconciliation gaps, and provide backfills without rewriting history invisibly.

**Practice artifact:** Draw click → stream → event-time windows → hot aggregate and raw archive; show a late event correcting one bucket. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists ad-click aggregation at Meta, Rippling, Google, Amazon and others; no date is attached to each report. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/ad-click-aggregator/cm4t0kxb6004488il22wqa2nn).
