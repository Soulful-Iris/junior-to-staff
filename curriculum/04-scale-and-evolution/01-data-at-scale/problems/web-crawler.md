# Web crawler: be fast without attacking one site

## What you are building

> Build a crawler for a public research index. It must discover a billion URLs while obeying per-host limits. Some pages contain infinite calendar links, redirects point at private addresses, and workers restart after fetching but before recording completion.

**Working contract:** Fetch only allowed public HTTP(S) destinations, respect the configured robots and host policy, and record a durable frontier state. Fetches may repeat; canonical URL identity and content/version handling prevent uncontrolled duplicate work.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| One billion discovered URLs | At 200 bytes/frontier entry, about 200 GB raw before indexes and history. |
| 50,000 fetches/s target | At 100 KiB/response, about 4.8 GiB/s inbound; network and storage dominate alongside politeness. |
| One concurrent fetch/host initial policy | Large aggregate throughput requires many eligible hosts; it cannot override an individual host limit. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/web_crawler.py
```

[Open the starting code](../../../../examples/architecture-starts/web_crawler.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| frontier | normalized_url,normalization_version,state,next_due | Durable URL identity and scheduling. |
| host_policy | host,robots_version,next_allowed,inflight | Shared host budget across workers. |
| fetch_results | url,attempt,status,content_hash,final_url | Evidence, deduplication and retry classification. |

## AWS implementation

![Web crawler: be fast without attacking one site: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/web-crawler.svg)

The frontier owns work identity; the host scheduler owns permission to fetch now. A distributed queue alone supplies neither robots policy nor fleet-wide per-host fairness.

## Build it in this order

### 1. Build a bounded frontier

Normalize scheme/host and remove fragments while preserving query semantics unless a source-specific rule proves equivalence. Version normalization rules. Persist discovered URLs idempotently and cap URL length, crawl depth and per-host discovery budget to contain calendar traps.

### 2. Coordinate host scheduling

Fetch and cache robots policy under a documented failure rule. A shared host scheduler issues leases respecting concurrency and next_allowed. Workers cannot independently apply one-request-per-host and accidentally multiply the limit across the fleet.

### 3. Make outbound fetches safe

Resolve and validate all destination addresses, pin the validated connection target, and repeat validation for every redirect. Block private, loopback, link-local and metadata ranges. Bound redirects, body bytes, decompression ratio and total time; do not execute page scripts in the first milestone.

### 4. Record outcomes and recover

Store status, final URL, content hash and retry time before completing the lease. Crash recovery can refetch, so content storage is immutable and frontier completion is conditional on the current attempt. Extract links under a bounded parser and preserve provenance.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Networking | Controlled egress with application-level destination pinning; deny internal address space and credential endpoints. |
| Frontier partitions | Spread URL records while coordinating host policy separately; a popular host must not bypass its limit. |
| Storage | Compressed immutable content with explicit retention; quarantine oversized/malformed responses without retry loops. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Fragment variants deduplicate; a distinct query remains distinct. |
| Redirect a public URL to a private IP | The fetch is rejected before the private connection. |
| Restart after content upload | A repeated fetch cannot publish under a stale attempt lease. |

## The next design decision

Change normalization rules after 500 million URLs are stored. Plan identity migration and aliasing so new rules do not duplicate the whole crawl or collapse URLs whose query parameters carry meaning.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>

> **Interviewer:** “Starting from seed URLs, discover pages and index their content. Avoid fetching the same URL repeatedly, respect publisher crawl rules, and keep making progress when a worker dies.”

This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 1 billion discovered URLs, 50,000 fetches/s and at least once crawl execution. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Duplicate URL | `/a?utm=x` and `/a` canonicalize equal | Normalize under a versioned rule and fetch once per policy window. |
| Same host overload | One domain has a million queued pages | Enforce per-host concurrency and politeness delay. |
| Worker crash | Page fetched but frontier ACK lost | Idempotent page version and crawl lease tolerate retry. |
| Robots change | Host disallows a path | Stop future fetches and expire queued work under the new policy. |

![The failure path and repaired design for Web crawler](../../../../assets/design-interview/web-crawler-before.svg)

## Think from the contract to the boxes

The frontier is a durable work scheduler keyed by normalized URL and host. Deduplication controls repeated work, but politeness is per origin and needs independent rate state. Workers fetch with bounded time/body size, extract links, and write content/version before advancing the frontier. A global queue that dispatches arbitrarily can violate a host’s crawl-delay even if its total rate is low.

**First diagram:** Trace one URL from discovery to normalized frontier, host gate, fetch, content store, and extracted links.

![AWS services named with their provider-neutral architectural roles](../../../../assets/design-interview/web-crawler-aws.svg)

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon SQS** / crawl frontier queue | Durably buffer distributed page work. | Kinesis when partitions and ordered per-key ingestion dominate. |
| **Amazon DynamoDB** / dedupe + host leases | Conditionally claim normalized URL and host budget. | ElastiCache for transient coordination plus durable backing store. |
| **Amazon ECS** / crawler workers | Run bounded browser/HTTP fetch and extraction workers. | Lambda for short static-page fetches only. |
| **Amazon S3** / page content archive | Store compressed page versions and replay inputs cheaply. | OpenSearch as searchable index, not raw archive. |
| **Amazon OpenSearch Service** / content search index | Serve indexed page queries. | S3/Athena for batch research queries. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

![A focused failure, capacity, or state diagram for Web crawler](../../../../assets/design-interview/web-crawler-deep.svg)

## Pressure-test the design

**Follow-up: A scheduler needs host-aware fairness: 500k queued URLs from one site must not monopolize workers. Compare global FIFO with per-host due queues.**

**Senior expectation:** A malicious page expands into endless URLs. Set depth, URL, MIME, size and domain budgets; quarantine patterns without losing unrelated frontier work.

**Staff expectation:** Change normalization after years of indexing. Build dual keys/reconciliation, quantify duplicate and omission risk, and provide a reversible index migration.

**Practice artifact:** Trace one URL from discovery to normalized frontier, host gate, fetch, content store, and extracted links. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists web-crawler reports at ZoomInfo, Atlassian, Microsoft, Expedia and others; the reports’ interview dates are not published. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/web-crawler-design/cm80gligm049vtvyjklc6gxdw).

</details>
