# Compute trending topics from duplicate and late events

## Application background

A sports app shows the most discussed topics from recent reactions. When a goal is scored, many people react to the same topic at once. The leaderboard should describe recent activity rather than count every reaction since the app launched.

Choose a time window, such as the last few minutes, and count each reaction in the appropriate window. Repeated messages and reactions delivered late can otherwise make a topic look more popular than it is.

### Example walkthrough

| Action | Expected behavior |
|---|---|
| Reaction `r-8` for goal-17 arrives twice | Count it once under the duplicate policy. |
| A reaction arrives two minutes after it happened | Apply the defined late-arrival rule. |
| An old window closes | Remove its contribution from the current ranking. |

A hot key is one topic receiving a disproportionate share of work. Splitting that work can help capacity, but the partial counts still need a clear combination rule.

## Your assignment

**Deliver:** Build a leaderboard for a declared recent time window. Handle repeated and late reactions, and tell readers how current the displayed ranking is.

**Required behavior:** Return the top 20 topics for a named event-time window and region, with as-of time and revision. The exercise permits two minutes of lateness and targets updates within thirty seconds for timely events.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope. The cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/trending_counts.py
```

**Supplied file:** [`examples/architecture-starts/trending_counts.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/trending_counts.py). You can also [read or download the source here](../../../../examples/architecture-starts/trending_counts.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only. It does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ. Compare the state transitions and outcomes.

```text
Partials: {('goal', 2): 1, ('goal', 3): 1, ('save', 1): 1}
Ranking: [('goal', 2), ('save', 1)]
```

### Set up your implementation workspace

Create `work/trending-counts/` in your checkout (or use a separate repository). Copy the supplied mechanism into that directory as `mechanism.py`, then extract its state transitions into functions you can call from your implementation. The record and module names below describe what you must implement. They are not a promise that files with those names already exist. Keep a `README.md` beside your implementation with its exact run commands and observed results.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| reactions | event_id,topic,region,event_time | Stable event identity and window attribution. |
| partials | window,topic,shard,count | Distributed counts with deterministic shard placement. |
| leaderboards | region,window,revision,as_of | Published ranked snapshot. Provisional/final flag. |

## Implement the assignment

### 1. Specify what one count means

Choose event types, bot/duplicate treatment, topic normalization and region source. Define window boundaries and a deterministic tie-breaker. Store event and received times so delayed transport is not mistaken for a new reaction.

### 2. Aggregate in two stages

Assign each event to a deterministic shard, deduplicate within the supported replay horizon and compute partial counts. Merge complete partials for the exact baseline. If you later send only local top-K candidates, prove the approximation behavior rather than claiming exact global top-K.

### 3. Publish immutable leaderboard revisions

Build a complete snapshot with as-of and finality metadata, then move one serving pointer. Late accepted events create a new revision. Reject stale writers so a delayed merge cannot overwrite a newer leaderboard.

### 4. Bound overload and history

Prioritize current windows, retain enough state for the two-minute lateness rule and send older corrections to a defined path. If sampling is introduced under overload, show that mode and its error implications to the consumer.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Duplicate e1 contributes once. Goal ranks above save. |
| Deliver a valid late reaction | The affected window gets a new revision. |
| Delay an old merge result | It cannot replace the current pointer. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target. The local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 500,000 events/s peak | At 200 bytes/event, about 100 MB/s before transport overhead. |
| Thirty-second freshness. Two-minute lateness | Freshness of the current display and completeness of an older window are different properties. |
| Hot topic receives 40% of traffic | 200,000 updates/s to one logical counter requires partial aggregation rather than one database row per event. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Compute trending topics from duplicate and late events: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/trending-counts.svg)

Partial aggregation absorbs hot-topic writes. A versioned snapshot avoids serving half of a new ranking mixed with half of an old one.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local event sequence or input stream | Amazon Kinesis: reaction event stream | Implement producer/consumer adapters, partition keys, durable acceptance and checkpoint/replay behavior. |
| Local window/aggregation loop | Managed Service for Apache Flink: partial aggregation | Implement stream processing with state, checkpoints, event-time handling and a declared late-event policy. |
| Local file, object fixture or exported payload | Amazon S3: replay archive | Implement upload/download and metadata adapters, scoped access, object naming, retention and incomplete-upload cleanup. |
| Local dictionary, SQLite records or state model | Amazon DynamoDB: leaderboard snapshots | Design partition/sort keys and write a storage adapter with conditional updates or transactions. Python state and SQL are not uploaded as a database. |
| Local cache, counter or coordination state | Amazon ElastiCache: current leaderboard cache | Implement a Redis/Valkey adapter and atomic operations, expiry and unavailable-cache behavior. Keep the durable authority separate. |
| Application or worker process | Amazon ECS: trends API | Build a container and task definition. Supply configuration, task roles and graceful shutdown behavior. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Partitioning | Use event/topic shards to spread a hot topic. Monitor the largest partition rather than mean utilization. |
| State retention | Retain dedupe/window state for lateness plus the replay contract. Document later-event handling. |
| Serving | Cache by window and revision. Keep a short current-pointer lifetime and visible as-of metadata. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement. It is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Limit memory with approximate heavy-hitter sketches. Specify false-positive/false-negative and count-error behavior, then decide whether the product can display an approximate ranking without misleading users.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



Assume 500,000 events/s peak globally, a 30-second refresh target, and a two-minute allowed lateness window. Specify event-time versus processing-time semantics before choosing a stream processor.

| Stream event | Expected effect |
|---|---|
| Event ID 17 delivered twice | Count once within the dedup retention policy |
| Event occurred 12:01, arrives 12:03 | Update the 12:01 event-time window if within allowed lateness |
| Event older than allowed lateness | Record late-drop or correction policy. Never silently count in the current minute |
| One topic receives 100,000 events/s | Do not direct every increment to one serial counter |

## The aggregation contract

Each input has event ID, topic ID, event timestamp, and receipt timestamp. Partition hot topics into deterministic or randomly salted partial counters, then merge into windows. Make the top-ten projection derived and repairable. If event IDs are deduplicated, state retention and the cost of keeping them. A watermark says when you consider an event-time window complete. Early results are provisional until lateness closes. Ties need a stable topic-ID rule. A continuously changing ranking cannot promise the same top ten across two simultaneous reads without a snapshot version.

Only three of the hundred partials are drawn. The 1,000 events/s per shard is an average, not an automatic maximum. The hash/salt distribution and slowest partition still need measurement.

## Put the AWS names on the boxes

**Why these boxes, and what changes the choice:** Kinesis partitions input. A hot topic must be salted or otherwise distributed, because a hot partition key stays hot. Lambda aggregates windows or Managed Service for Apache Flink handles complex event-time work. DynamoDB serves a versioned result and S3 enables replay.



**Senior follow-up:** One input partition goes idle while the rest advance. Explain the global watermark bottleneck and an idle-partition policy. Show what correction a user sees when #10 becomes #11 after a late event.

**Staff follow-up:** A bot floods a topic. Decide which boundary verifies identity and abuse policy. Quantify the effect of revoking events already included in materialized windows. Separate a fast approximate public display from an auditable billing count if the product needs both.

**Practice artifact:** Partition/merge boxes, annotated watermark timeline, rough per-shard write rate under 100-way salting, and a test for duplicate plus late arrival.

**AWS translation:** Kinesis partitions by the chosen routing key. A single hot key can still bottleneck a shard. Use stream processing and a versioned materialized view. DynamoDB conditional aggregation on a single hot key may not absorb this rate. See the chapter's event-time windows and hot-partition cases for the mechanics.

**Evidence:** [Spotify's March 2026 Wrapped engineering post](https://engineering.atspotify.com/2026/3/inside-the-archive-2025-wrapped) discusses capacity, replay, recovery, and a high-stakes launch. These trend numbers and rules are constructed practice, not Spotify workload claims.

</details>
