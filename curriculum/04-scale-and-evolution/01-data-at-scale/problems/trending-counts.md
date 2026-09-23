# Trending counts: the spike that breaks one partition

> **Interviewer:** “Show the ten most popular topics in the last five minutes. Most topics get a few events; a celebrity mention receives 100,000 events/s. Mobile events can arrive two minutes late and can be delivered twice. What exactly does ‘trending now’ mean?”

Assume 500,000 events/s peak globally, a 30-second refresh target, and a two-minute allowed lateness window. Specify event-time versus processing-time semantics before choosing a stream processor.

| Stream event | Expected effect |
|---|---|
| Event ID 17 delivered twice | Count once within the dedup retention policy |
| Event occurred 12:01, arrives 12:03 | Update the 12:01 event-time window if within allowed lateness |
| Event older than allowed lateness | Record late-drop or correction policy; never silently count in the current minute |
| One topic receives 100,000 events/s | Do not direct every increment to one serial counter |

![One hot counter serializes the entire trend; salted partials spread the load](../../../../assets/design-practice/trending-counts-boundary.svg)

## The aggregation contract

Each input has event ID, topic ID, event timestamp, and receipt timestamp. Partition hot topics into deterministic or randomly salted partial counters, then merge into windows; make the top-ten projection derived and repairable. If event IDs are deduplicated, state retention and the cost of keeping them. A watermark says when you consider an event-time window complete; early results are provisional until lateness closes. Ties need a stable topic-ID rule. A continuously changing ranking cannot promise the same top ten across two simultaneous reads without a snapshot version.

![A hundred partial counters distribute one hot topic before an event-time merge](../../../../assets/design-practice/trending-counts-deep.svg)

Only three of the hundred partials are drawn. The 1,000 events/s per shard is an average, not an automatic maximum; the hash/salt distribution and slowest partition still need measurement.

![Late arrival corrects a provisional count after the first top-ten read](../../../../assets/design-practice/trending-counts-trace.svg)

**Senior follow-up:** One input partition goes idle while the rest advance. Explain the global watermark bottleneck and an idle-partition policy. Show what correction a user sees when #10 becomes #11 after a late event.

**Staff follow-up:** A bot floods a topic. Decide which boundary verifies identity and abuse policy; quantify the effect of revoking events already included in materialized windows. Separate a fast approximate public display from an auditable billing count if the product needs both.

**Practice artifact:** Partition/merge boxes, annotated watermark timeline, rough per-shard write rate under 100-way salting, and a test for duplicate plus late arrival.

**AWS translation:** Kinesis partitions by the chosen routing key; a single hot key can still bottleneck a shard. Use stream processing and a versioned materialized view; DynamoDB conditional aggregation on a single hot key may not absorb this rate. See the chapter's event-time windows and hot-partition cases for the mechanics.

**Evidence:** [Spotify's March 2026 Wrapped engineering post](https://engineering.atspotify.com/2026/3/inside-the-archive-2025-wrapped) discusses capacity, replay, recovery, and a high-stakes launch. These trend numbers and rules are constructed practice, not Spotify workload claims.
