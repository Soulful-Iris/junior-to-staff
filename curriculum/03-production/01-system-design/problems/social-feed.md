# Social feed: a popular author changes the shape

## What you are building

> Build a following feed for a creator network. Ordinary authors have hundreds of followers, while one celebrity has ten million. A post deleted or made private must not remain readable simply because its ID is in a follower’s cached feed.

**Working contract:** GET /feed returns up to 30 currently authorized posts using a stable cursor. New eligible posts should appear within ten seconds under normal load. Feed materialization is a candidate index; post visibility is checked before returning content.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 20 million daily users; 15,000 writes/s and 120,000 reads/s peak | Read amplification, fan-out and content storage need separate capacity models. |
| 30 items/page | 120,000 reads/s can require 3.6 million candidate checks/s before batching and caching. |
| Celebrity with ten million followers | One post can create ten million inbox writes; use a different delivery strategy for such authors. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/social_feed.py
```

[Open the starting code](../../../../examples/architecture-starts/social_feed.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| posts | author,post_id,version,visibility,deleted | Current content and authorization authority. |
| feed_entries | reader,sort_key,post_id | Candidate references, never independent permission grants. |
| follow_edges | follower,author,revision | Relationship source for fan-out and read-time eligibility. |

## AWS implementation

![Social feed: a popular author changes the shape: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/social-feed.svg)

The hybrid design spends writes for ordinary authors and reads for celebrities. Neither path owns privacy; current source state decides which content can leave the service.

## Build it in this order

### 1. Build a read-time feed first

Query recent posts by followed authors and merge by a deterministic order. Use opaque cursors that preserve ordering across pages. Measure the cost before introducing fan-out; this baseline is also a recovery path when materialization lags.

### 2. Materialize ordinary-author candidates

Emit post events from an outbox and append idempotent references to follower inboxes. Record fan-out progress and age. Treat deletion as a source version change so late create events cannot resurrect a removed post.

### 3. Handle celebrities on read

Keep very large-author streams separate and merge them with the reader’s materialized candidates. Choose a threshold from measured fan-out cost and read frequency, not follower count alone. Bound candidate fetches so one empty/private stream cannot cause unbounded refill work.

### 4. Authorize before returning content

Batch-fetch current post metadata and apply membership, blocks, privacy and deletion rules. Cached candidates may survive; restricted content must not. Define whether a cursor remains usable when eligibility changes, and tolerate shorter pages rather than leaking an item.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Feed storage | Partition inboxes by reader and time range; bound retained candidates and large-author fan-out. |
| Caching | Keep content authorization outside cached candidate membership; never cache a shared private response under an unscoped key. |
| Operations | Track ten-second freshness attainment, fan-out lag, candidate rejection rate and read amplification. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | A cached private candidate is filtered; revoking the remaining post produces an empty result. |
| Pause fan-out | Freshness age rises and the bounded read-time fallback remains available. |
| Deliver an old create after deletion | Its version cannot make the post visible again. |

## The next design decision

Introduce ranked ordering. Freeze or version enough ranking context to make pagination understandable, then explain how you avoid duplicate posts when new scores arrive between pages.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>

> **Interviewer:** “Build a home feed. Most authors have hundreds of followers; one has eight million. People expect their own new post immediately and friends' posts within ten seconds. Show what happens when the popular author posts four times in a minute.”

Assume 20 million daily readers, 15,000 ordinary writes/s, 120,000 peak read requests/s, and a home page of 30 items. These are capacity assumptions, not observed company numbers. First clarify follow privacy, delete behavior, ranking versus recency, and the ten-second measurement point.

| Event | Expected user behavior |
|---|---|
| Author publishes and refreshes immediately | Own post visible from authoritative write path |
| Eight-million-follower author posts | Posting acknowledgement does not wait for eight million feed writes |
| Follower is removed before feed read | Former follower cannot read a now-private post from stale fanout |
| One fanout partition lags | Feed can show an explicit partial/freshness state; catch up with cursor |

![Write fanout overwhelms the queue for a popular author; hybrid read path protects posting](../../../../assets/design-practice/social-feed-boundary.svg)

## Show the multiplication

Fanout on write copies or indexes each ordinary post into follower feed candidates. For a 500-follower account one post entails roughly 500 feed insertions. For eight million followers, four posts would imply 32 million candidate insertions in a minute. A hybrid design writes the post once, fanouts ordinary accounts, and merges popular-account posts at read time. Mark thresholds as measured operational choices; the 500/8m distinction is illustrative.

![A source post splits into ordinary write fanout and viral read-time merge](../../../../assets/design-practice/social-feed-deep.svg)

The fork shows why average follower count is a bad capacity input. Work for the viral branch moves to reads, so also estimate what happens to read amplification when many followed popular authors post at once.

![Publication, delayed fanout, read-time merge, and privacy check](../../../../assets/design-practice/social-feed-trace.svg)

## What each store owns

Posts live in the source-of-truth store; follower edges and privacy are authoritative elsewhere; feed rows are a repairable projection. On pagination, pin a ranking/version watermark or specify how inserts move the page boundary. Stable IDs prevent duplicates when fanout and read-time merge both produce the same post. Cache an eligible candidate list, but recheck authorization on read for private content and revoke or filter cached rows when relationships change.

## Put the AWS names on the boxes

![AWS service boxes labeled with their general architectural roles](../../../../assets/design-practice/social-feed-aws.svg)

**Why these boxes, and what changes the choice:** DynamoDB owns post IDs and versioned views; Aurora is a reasonable alternative for follower joins under smaller load. SQS decouples ordinary fanout but has duplicate delivery; cache readers merge high-fanout authors. Neither queue nor cache replaces read-time privacy checks.

Read the smaller label under each service first: it names the architectural job. Then ask whether that service supplies the guarantee in the problem, or simply moves work to the next box.

**Senior follow-up:** Queue backlog exceeds the ten-second freshness target. Derive backlog duration from ingestion and drain rates, choose whether to shed expensive ranking or delay social content, and define a user-facing freshness metric. A DLQ alone does not catch the main queue up.

**Staff follow-up:** A creator with eight million followers is removed for abuse while their post remains in millions of projections. Specify source-of-truth revocation, projection repair, regional invalidation, and audit evidence. A complete purge of every copy may take time; access control cannot rely on that purge finishing.

**Practice artifact:** Baseline and hybrid box diagrams, fanout estimate, freshness calculation, one privacy revocation test, and a failure-injection recovery plan.

**AWS translation:** S3 for large media; DynamoDB/RDS for posts and follower relationships subject to access patterns; SQS/Kinesis for asynchronous fanout as appropriate; ElastiCache for hot candidates. Queue delivery can duplicate, so projection writes must be idempotent. [Spotify's 2026 engineering discussion](https://engineering.atspotify.com/2026/1/why-we-use-separate-tech-stacks-for-personalization-and-experimentation) separates serving and evaluation responsibilities; this exercise makes the simpler feed/data ownership distinction without claiming to reproduce Spotify's design.

</details>
