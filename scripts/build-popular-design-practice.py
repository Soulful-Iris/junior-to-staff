#!/usr/bin/env python3.12
"""Author a researched interview-practice set and its box-first SVGs."""
from html import escape
from pathlib import Path
import textwrap

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'/'design-interview'
ASSETS.mkdir(parents=True,exist_ok=True)

# Exercises are original teaching material. Public community-question pages are
# linked per page; their lists are self-reported and generally omit interview
# dates. The code below deliberately does not claim a current company rubric.
DATA=[
{
'slug':'url-shortener','chapter':'03-production/01-system-design','title':'URL shortener: who owns the code?','prompt':'“Turn long links into short links that redirect quickly. Users can choose a custom alias, set an expiry, and inspect click counts. What happens if two people request the same alias?”','scale':'Assume 30 million new links/day, 3 billion redirects/day, and redirect p99 below 100 ms. Start with redirect correctness; make analytics asynchronous.','cases':[('New link','Create a URL with a 30-day expiry','Return one durable, unguessable short code.'),('Alias collision','Two tenants request `launch`','One conditional create wins; the other gets a conflict.'),('Expired link','Resolve after expiry','Return a defined not-found/expired response; never redirect stale cache.'),('Hot link','One campaign gets 80k redirects/s','Serve a safe cached mapping without losing expiry or abuse controls.')],
'thinking':'A code is an identifier, not proof that the row was created. Allocate with uniqueness enforced by the durable store, then publish the mapping to caches. Redirects are reads; clicks are events, so a slow analytics write must not block the redirect. Decide whether expired links are immediately invalid or invalid after a bounded cache TTL, then make that bound visible in the contract.','artifact':'Trace alias creation through uniqueness, cache fill, redirect, expiry invalidation, and click aggregation.',
'services':[('Amazon API Gateway','request entry','Authenticate link creation and shape redirects.','ALB + ECS when custom redirect handling and connection reuse matter.'),('Amazon DynamoDB','code mapping store','Conditional put gives the chosen code one owner.','Aurora PostgreSQL for relational ownership and reporting queries.'),('Amazon ElastiCache','redirect cache','Serve hot code-to-target lookups cheaply.','CloudFront for globally distributed redirect caching.'),('Amazon Kinesis','click event stream','Move click counts off the redirect path.','SQS for simpler asynchronous counting with looser event-time needs.')],
'edges':[(0,1),(0,2),(0,3)],'deep':'Two requests race for one human alias. Follow which conditional write wins and why a cache cannot arbitrate.','kind':'race','shape':'two writers → unique row → loser conflict; cache is filled only after commit.','senior':'A cached target was changed for a phishing report. Bound invalidation delay, add a deny list that wins over cache, and explain the emergency kill switch.','staff':'Aliases become a cross-region namespace. Choose a home for uniqueness, define collision behavior during partitions, and bound how many codes can be lost or allocated twice.',
'source':'https://www.hellointerview.com/community/questions/url-shortener-design/cm5svnaco01dqxszbok7e1lk1','source_text':'The current community interview-question catalog lists user-submitted URL-shortener reports across companies including PayPal, Microsoft, and JPMorgan Chase; individual report dates are not shown.'},
{
'slug':'rideshare-dispatch','chapter':'03-production/01-system-design','title':'Ride sharing: one driver, one accepted ride','prompt':'“A rider asks for a car. Drivers move every few seconds, one driver can accept only one trip, and the rider wants a live ETA. Design matching and state transitions.”','scale':'Assume 5 million active drivers, location p95 younger than 5 seconds, and bursts around commute and event traffic.','cases':[('Fresh location','Driver D7 reports at 10:00:03','Search a bounded nearby-cell set; compute road ETA before offer.'),('Two matchers','Both offer D7 a trip','One conditional reservation wins; the other tries its next candidate.'),('Late acceptance','D7 accepts after offer expires','Reject stale offer token and continue matching.'),('Stale GPS','D8 was nearby 40 seconds ago','Exclude or down-rank by freshness; do not claim it is currently nearby.')],
'thinking':'Split the fast changing location index from the authoritative ride record. Geospatial cells find candidates; a road-network ETA ranks them. An offer has an expiry and token. Accept must atomically transition the driver from AVAILABLE to RESERVED for this ride, then persist the rider-facing assignment. GPS updates are hints, not ownership.','artifact':'Draw location ingress separately from offer/accept state. Label freshness, cell coverage, offer expiry, and the conditional reservation.',
'services':[('Amazon API Gateway','rider/driver entry','Authenticate updates and ride requests.','ALB + ECS for persistent bidirectional traffic.'),('Amazon Kinesis','location update stream','Buffer high-volume GPS changes.','MSK when Kafka tooling and replay consumers dominate.'),('Amazon ElastiCache','geo candidate index','Keep short-lived driver cells and availability hints.','MemoryDB for stronger in-memory durability; a dedicated geo index for richer shapes.'),('Amazon DynamoDB','ride + reservation state','Conditionally reserve one driver and advance ride state.','Aurora for transactional multi-entity booking with lower write scale.'),('Amazon Location Service','route and ETA','Estimate route distance/time from candidates.','Self-hosted routing when map coverage, control, or price requires it.')],
'edges':[(0,1),(1,2),(2,3),(3,4)],'deep':'Drivers occupy moving grid cells, but a cell match is only candidate discovery. Draw neighboring-cell expansion, GPS age, and the later atomic accept decision.','kind':'grid','shape':'3×3 location cells with rider centered; nearby cells yield candidates, route ETA ranks them, availability reservation happens afterward.','senior':'An event venue creates a hot cell and floods location writes. Split or salt the index while preserving a bounded search radius and explain how drivers move between cells.','staff':'Different cities need local matching and disaster recovery. Define regional ownership, cross-region request behavior, regulatory location retention, and fairness across driver cohorts.',
'source':'https://www.hellointerview.com/community/questions/rideshare-architecture/cm6u9yzg000y87oi9k1oi7qx8','source_text':'The current community interview-question catalog lists ride-sharing design reports at companies including Google, Salesforce, Visa, and Meta; dates are generally omitted.'},
{
'slug':'food-delivery-marketplace','chapter':'03-production/01-system-design','title':'Food delivery: quote the right nearby options','prompt':'“Customers search nearby restaurants, place an order, and track delivery. Restaurants change hours and menus; couriers move; inventory can sell out between browse and checkout. Design the customer path.”','scale':'Assume 200,000 restaurants, 2 million concurrent shoppers during dinner, and availability freshness within 30 seconds.','cases':[('Nearby search','Cuisine + 3 km radius','Return open restaurants whose location and filters match.'),('Menu race','Last item sells after browse','Reject or substitute before payment capture; explain the reservation rule.'),('Courier GPS stale','Last update 90 seconds old','Show uncertainty or refresh; avoid precise false ETA.'),('Duplicate order submit','Mobile retry after timeout','Idempotency key returns the same order, not a second charge.')],
'thinking':'Search is a discovery view, not inventory authority. Index restaurant location and catalog for fast filtering; recheck opening state, price and stock at checkout. Persist an order state machine (CREATED → ACCEPTED → PREPARING → PICKED_UP → DELIVERED) and keep payment/courier side effects idempotent. A nearby result is not a confirmed order.','artifact':'Draw search projection, checkout authority, restaurant acceptance, courier assignment, and customer status as separate boxes.',
'services':[('Amazon OpenSearch Service','search index','Filter and rank current restaurant/menu candidates.','Aurora spatial queries at modest data size.'),('Amazon Location Service','nearby geometry','Find restaurants and estimate route distance.','OpenSearch geo queries for combined custom filters.'),('Amazon Aurora','order + stock authority','Transactionally validate price, stock and order creation.','DynamoDB conditional item updates for key-oriented inventory.'),('Amazon EventBridge','order event routing','Fan out accepted order changes to restaurant and courier workflows.','SNS when simple topic broadcast is enough.'),('Amazon SQS','work queue','Buffer assignment/retry work independently.','Step Functions when long-lived workflow state is the main need.')],
'edges':[(0,1),(1,2),(2,3),(3,4)],'deep':'Search can show stale stock. Follow the read projection into checkout and identify the exact point where the last item is reserved.','kind':'state','shape':'SEARCHED → CHECKED → RESERVED → PAID → ACCEPTED','senior':'A restaurant does not respond before the timeout. Separate payment authorization from capture, define cancellation compensation, and keep customer status honest.','staff':'Expand into a new country with different tax, courier and payment providers. Keep domain events stable while assigning regional ownership, compliance, and rollout measures.',
'source':'https://www.hellointerview.com/community/questions/nearby-restaurants-app/cmacvonzo00r0ad08c9ona48e','source_text':'The current community interview-question catalog lists food-delivery design reports at Uber, Meta and Twilio; the report dates are not shown.'},
{
'slug':'calendar-availability','chapter':'03-production/01-system-design','title':'Calendar: reserve time without hiding conflicts','prompt':'“People create events, invite guests, and look up free/busy time across calendars. Two organizers may book the same room at once. Time zones and daylight saving changes matter.”','scale':'Assume 100 million calendars, 3 million active users, and free/busy reads much more frequent than event writes.','cases':[('Overlap','Room booked 09:00–10:00; request 09:30–10:30','Reject or offer another slot under one conflict rule.'),('DST boundary','Recurring 09:00 local meeting crosses clock change','Preserve local wall time with explicit zone and recurrence semantics.'),('Concurrent booking','Two users claim the last room','One transaction/constraint wins; loser sees conflict.'),('Invite response','Guest accepts after organizer cancels','Reject stale event version or mark response to canceled event.')],
'thinking':'Store instants in UTC plus the original time-zone identifier and recurrence rule. Use interval overlap semantics `[start,end)` so adjacent meetings do not conflict. A precomputed free/busy view accelerates reads, but booking must check authoritative intervals at commit. Make invitations versioned events; a delayed response cannot resurrect a canceled meeting.','artifact':'Draw event authority, free/busy projection, notification delivery, and a conflict check using the exact interval boundary.',
'services':[('Amazon API Gateway','calendar API entry','Authenticate calendar reads and writes.','ALB + ECS for long-lived sync clients.'),('Amazon Aurora PostgreSQL','event + room store','Range constraints/transactions prevent conflicting reservations.','DynamoDB with carefully partitioned per-calendar transactions.'),('Amazon ElastiCache','free/busy cache','Speed repeated availability reads.','Aurora read replicas when freshness can remain transactional.'),('Amazon EventBridge','change event router','Publish event changes to notification and sync consumers.','Transactional outbox + SQS for tighter publish recovery.'),('Amazon SQS','notification queue','Retry mail/push without blocking calendar writes.','EventBridge Scheduler for delayed reminders.')],
'edges':[(0,1),(1,2),(1,3),(3,4)],'deep':'Adjacent intervals are legal; overlapping half-open intervals conflict. Compare 09:00–10:00 against 10:00–11:00 and 09:59–10:30.','kind':'intervals','shape':'Two horizontal time bars: [09:00,10:00) and [10:00,11:00) touch without overlap; [09:59,10:30) intersects and is rejected.','senior':'A calendar write succeeds but an invitation email is delayed. Explain source of truth, outbox, notification dedupe, and what the guest sees before delivery.','staff':'Support federated calendars across providers with different recurrence semantics. Set compatibility contracts, conflict ownership and a safe migration for stored time zones.',
'source':'https://www.hellointerview.com/community/questions/calendar-free-busy/cm8c1h59t005n8pgzdq4ynqjo','source_text':'The current community interview-question catalog lists calendar/free-busy reports at Microsoft, Oracle and LinkedIn; individual interview dates are not provided.'},
{
'slug':'video-streaming-platform','chapter':'03-production/01-system-design','title':'Video streaming: keep playback smooth at the edge','prompt':'“Creators upload large videos. Viewers start playback quickly and continue across different bandwidths and devices. Design ingest, processing, storage, and delivery.”','scale':'Assume 5 million daily uploads, 100 million viewers, 4K source files up to 20 GB, and playback start p95 under 2 seconds.','cases':[('Partial upload','Network drops at 80%','Resume multipart upload without restarting all bytes.'),('Worker retry','Transcode task delivered twice','Stable rendition key and manifest commit prevent duplicate publication.'),('Slow connection','Bandwidth falls mid-playback','Player switches to a lower bitrate segment.'),('Private video','Owner revokes access','New segment requests fail authorization after bounded token expiry.')],
'thinking':'Separate the control path (upload authorization, job state, manifest) from media bytes. Transcode into aligned segments at multiple bitrates; publish a manifest only after required renditions pass validation. A CDN serves immutable segments, while signed access controls protect private content. Model the player’s buffer and bitrate adaptation, not just the upload pipeline.','artifact':'Show source upload, processing fan-out, manifest publish point, CDN cache, and authorization on segment fetch.',
'services':[('Amazon S3','source + rendition objects','Durably store large media through multipart upload.','EFS only for shared POSIX scratch, not a public byte-serving path.'),('Amazon SQS','transcode work queue','Buffer rendition tasks and retry workers.','Step Functions for multi-stage workflows with explicit job state.'),('AWS Elemental MediaConvert','transcode service','Generate device/bitrate outputs without owning codec fleet.','ECS/EC2 with FFmpeg for custom filters or codec tuning.'),('Amazon CloudFront','media CDN','Serve cached segments near viewers.','Third-party CDN where geographic reach/contracts require it.'),('Amazon DynamoDB','job + manifest state','Track processing and publish only validated outputs.','Aurora for relational creator/catalog requirements.')],
'edges':[(0,1),(1,2),(2,3),(2,4)],'deep':'A single 4K file becomes a bitrate ladder. Show the player switching from 8 Mbps to 2 Mbps while the segment timeline remains aligned.','kind':'ladder','shape':'Adaptive ladder: 2160p / 8 Mbps, 1080p / 5 Mbps, 720p / 2 Mbps, 480p / 0.8 Mbps; buffer selects the next segment.','senior':'A viral launch empties origin capacity. Explain CDN cache key, segment immutability, cache warming limits, origin shielding, and how auth changes affect cacheability.','staff':'Multiple regions ingest the same creator’s content. Set source ownership, replication/egress trade-offs, takedown propagation target, and recovery behavior during an origin outage.',
'source':'https://www.hellointerview.com/community/questions/creator-viewer-paths/cm6wu2x3y0000356pl299toa0','source_text':'The current community interview-question catalog lists YouTube-style streaming reports at companies including Datadog, Snapchat and Meta; report dates are not disclosed.'},
{
'slug':'news-aggregator','chapter':'03-production/01-system-design','title':'News aggregator: freshness without a write storm','prompt':'“Collect articles from publishers, remove duplicates, and make a personalized feed from topics and followed sources. A major story arrives from hundreds of sources at once.”','scale':'Assume 50,000 publisher feeds, 20 million daily readers, and new stories visible within 60 seconds.','cases':[('Same story','Three publishers syndicate one article','Cluster canonical story while retaining source attribution.'),('Feed refresh','One publisher updates title','Refresh the item without creating an unrelated duplicate.'),('Breaking news','Topic query receives 5× normal traffic','Hot-topic cache and read fanout do not block ingestion.'),('Unfollow','Reader unfollows a source','Feed response stops showing it within the declared privacy/freshness bound.')],
'thinking':'Treat collection, canonicalization, ranking and feed reads as separate stages. Keep source article IDs and a canonical cluster ID; dedupe is probabilistic candidate grouping followed by explainable rules. Precompute ordinary feeds where it helps, but do not copy every breaking story to every user synchronously. Recheck follows and muted topics when composing the page.','artifact':'Trace publisher fetch → canonical story → topic index → feed composition; mark which copy is source and which is projection.',
'services':[('Amazon EventBridge Scheduler','poll schedule','Trigger publisher fetches at per-source cadence.','SQS delayed work when retry timing needs tighter control.'),('AWS Lambda','fetch/normalize worker','Parse small source feeds and enforce per-domain limits.','ECS for heavy parsers and persistent connections.'),('Amazon OpenSearch Service','article search index','Find text/topic candidates and support filtered discovery.','Aurora full-text search at lower volume.'),('Amazon DynamoDB','article + follow state','Store canonical IDs and reader/source relationships.','Aurora when joins and consistency across follows dominate.'),('Amazon ElastiCache','feed/result cache','Protect hot stories and repeated feed reads.','CloudFront for public non-personalized pages.')],
'edges':[(0,1),(1,2),(1,3),(1,4)],'deep':'Fanout-on-write can multiply one breaking story into millions of queue tasks. Compare a normal source with one followed by ten million readers.','kind':'fanout','shape':'One article → ordinary 1000 feed writes; viral article → 10,000,000 writes. Hybrid path stores story once and merges hot topic at read time.','senior':'Publisher fetches become rate-limited and malformed. Isolate domains, add backoff and quarantine, and tell readers when content is stale.','staff':'A new editorial policy changes canonicalization across regions. Define data ownership, safe reindexing, relevance quality measures, and rollback without duplicate feed entries.',
'source':'https://www.hellointerview.com/community/questions/news-aggregator-feed/cm96lh25n0039ad08067audlg','source_text':'The current community interview-question catalog lists personalized news-aggregation reports at Amazon, Microsoft and Rippling; interview dates are not shown.'},
{
'slug':'api-gateway-platform','chapter':'03-production/01-system-design','title':'API gateway: route safely across many teams','prompt':'“Build a shared gateway for dozens of product teams. It validates identity, routes API versions, enforces quotas, and protects downstream services. One team deploys a bad route rule.”','scale':'Assume 25,000 requests/s, 150 services and gateway p99 overhead under 15 ms.','cases':[('Unknown route','Caller requests `/v9/billing`','Fail closed with a clear 404; do not guess a backend.'),('Auth expires','Token expires during request','Return standardized 401; never send unauthenticated work downstream.'),('Bad config','New route points billing to staging','Validation blocks publish or staged rollout catches it.'),('Dependency slow','One service stalls 8 seconds','Per-route deadline and circuit breaker protect unrelated APIs.')],
'thinking':'The gateway should centralize policy and routing, not domain business logic. Treat config as a versioned artifact: validate route targets, auth modes, timeout budgets, and compatibility before a canary. Keep each request’s end-to-end deadline; retry only safe/idempotent operations and never beyond remaining time. Avoid becoming a global failure domain by isolating route/config caches and rollout.','artifact':'Draw config publish separately from request flow. Label the validation gate, per-route budget, auth decision, and backend health boundary.',
'services':[('Amazon API Gateway','managed API entry','Handle managed HTTP APIs and common auth/throttle policies.','ALB + ECS proxy for custom protocol transformations and high request control.'),('AWS Lambda','policy hook','Run short custom request validation.','ECS sidecar/plugin for low-latency stable policies.'),('Amazon Cognito','identity provider','Issue/verify user tokens for applicable products.','External OIDC provider when enterprise identity is already managed.'),('AWS AppConfig','route policy rollout','Version and gradually deploy routing/policy config.','GitOps config distribution when team-owned proxy fleet is preferred.'),('Amazon CloudWatch','route telemetry','Measure per-route latency, errors and throttles.','Existing OpenTelemetry stack with per-route labels and alarm ownership.')],
'edges':[(3,0),(0,1),(1,2),(0,4)],'deep':'A route rule is a production deploy. Trace old and new config through validation, canary traffic, alarm, rollback, and already-started requests.','kind':'rollout','shape':'config v42 → validate → 1% canary → latency alarm → restore v41; in-flight requests keep the deadline/config snapshot they started with.','senior':'A route has side effects and a timeout. Show why retry could duplicate work, how idempotency is exposed, and how retry budget prevents amplification.','staff':'Ten teams want incompatible gateway features. Set extension points, ownership and migration contracts while keeping the gateway’s failure modes bounded.',
'source':'https://www.hellointerview.com/community/questions/api-gateway-design/cmi7ehcp402t108adh7as55gb','source_text':'The current community interview-question catalog lists an API gateway platform prompt at MongoDB. It does not publish when that report occurred.'},
{
'slug':'online-judge','chapter':'03-production/01-system-design','title':'Online judge: untrusted code gets a small box','prompt':'“Users submit code to a timed contest. Compile and run it against hidden tests, report results, and update a live leaderboard. Submissions are untrusted.”','scale':'Assume 100,000 contest participants, 10,000 submissions/minute at peak and strict CPU, memory, and wall-time caps.','cases':[('Infinite loop','Submission never exits','Worker kills it at deadline and frees the isolated sandbox.'),('Fork bomb','Code spawns many processes','Sandbox denies process/resource escalation.'),('Duplicate submit','Client retries after lost ACK','One submission ID returns one result state.'),('Hidden tests','User requests detailed failure output','Do not expose test input, secrets, or another user’s source.')],
'thinking':'Persist a submission record, then enqueue compilation and execution. Run each language in a sandbox with no network, read-only base image, ephemeral filesystem, seccomp/container or microVM boundary, and hard CPU/memory/time limits. Workers are replaceable; results are versioned and idempotent. Treat compilation output and runtime output as hostile text before displaying it.','artifact':'Draw public API, durable submission state, queue, isolated compile/run pool, result checker, and leaderboard projection.',
'services':[('Amazon API Gateway','submission entry','Authenticate, bound payload size and rate.','ALB + ECS for custom upload/stream behavior.'),('Amazon S3','source + test artifacts','Keep versioned packages away from worker images.','EFS for shared read-only test corpora with careful isolation.'),('Amazon SQS','execution queue','Buffer work and separate compile from run tiers.','Step Functions for explicit multi-language orchestration.'),('Amazon ECS on AWS Fargate','isolated task compute','Run ephemeral bounded tasks with per-task roles.','EC2 microVM or dedicated sandbox fleet for stronger isolation and lower cost at scale.'),('Amazon DynamoDB','submission/result state','Store state transitions and idempotent result IDs.','Aurora for relational contest/rank queries.')],
'edges':[(0,1),(0,2),(2,3),(3,4)],'deep':'A language runtime must not read another submission’s files or reach internal network services. Draw the sandbox boundary and list capabilities denied by default.','kind':'layers','shape':'Internet → API → queue → ephemeral sandbox (CPU/memory/time caps, no network, scratch disk) → result sanitizer → user; secrets stay outside the sandbox.','senior':'A contest bursts at start time and leaderboard writes become hot. Partition execution by language/problem while aggregating rank updates asynchronously with visible freshness.','staff':'A new language requires an untrusted runtime and supply-chain updates. Define image provenance, patch windows, emergency disable, isolation tests and acceptable blast radius.',
'source':'https://www.hellointerview.com/community/questions/coding-contest-platform/cm4szs6ae002w3g2e09amf982','source_text':'The current community interview-question catalog lists an online coding-judge design at Meta, Whatnot, Microsoft and other companies; individual dates are unavailable.'},
{
'slug':'job-scheduler','chapter':'03-production/05-reliability','title':'Job scheduler: fire once on time, recover after a crash','prompt':'“Customers schedule one-time and recurring jobs. Workers can crash after doing the work but before acknowledging it. Schedule accuracy is one minute; a retry must not silently perform a financial action twice.”','scale':'Assume 10,000 jobs/s at peak, 50 million future schedules and execution history retained for one year.','cases':[('Due now','Job time = 12:00; worker polls 12:00:03','Dispatch within stated one-minute tolerance.'),('Worker crash','Side effect committed, ACK lost','Redelivery uses idempotency key or reconciles result.'),('Recurring job','Hourly schedule around DST','State whether schedule follows UTC or local wall clock.'),('Cancel race','Cancel arrives as job is claimed','One versioned state transition decides whether execution may start.')],
'thinking':'Separate the schedule definition, due-time index, execution record and worker queue. Partition by due-time bucket to find work efficiently, but spread hot minutes and large tenants. Claim a job with a lease and fencing/version token; if a worker outlives the lease, it cannot overwrite a newer result. Exactly-once side effects need downstream idempotency or reconciliation, not a queue label.','artifact':'Draw scheduled → due → leased → running → succeeded/retry/dead-letter states and mark the crash window.',
'services':[('Amazon EventBridge Scheduler','managed schedule trigger','Use for service-managed schedules with supported precision and scale.','Custom time-bucket index when per-tenant fairness or finer semantics are required.'),('Amazon DynamoDB','schedule + execution ledger','Store schedule versions, leases and idempotent state.','Aurora for transactional complex recurring rules.'),('Amazon SQS','worker queue','Buffer due executions with retry and DLQ handling.','Kinesis for ordered event streams rather than independent tasks.'),('AWS Lambda','short task worker','Run bounded jobs with simple concurrency controls.','ECS for long jobs or custom worker pools.'),('Amazon CloudWatch','lag + failure alarms','Track due-to-start delay, oldest due item and retry outcomes.','Existing telemetry system with the same latency denominator.')],
'edges':[(0,1),(1,2),(2,3),(3,4)],'deep':'A scheduler’s “exactly once” claim usually fails at the external effect/ack boundary. Show the lease expiry and duplicate delivery after worker crash.','kind':'states','shape':'SCHEDULED → DUE → LEASED(epoch 8) → RUNNING → SUCCEEDED; lease expires, second worker gets epoch 9, epoch 8 can no longer commit.','senior':'A 10-minute backlog follows an outage. Calculate drain capacity, prioritize overdue/tenant work, and avoid retrying a dependency already saturated.','staff':'Thousands of teams share the scheduler. Set noisy-neighbor quotas, migration and versioning rules, service SLOs, and a contract for jobs that cannot be safely retried.',
'source':'https://www.hellointerview.com/community/questions/job-scheduler-cron-history/cm7w828yv00sejmejlmofwtvp','source_text':'The current community interview-question catalog lists a distributed job-scheduler prompt at Robinhood, DoorDash, NVIDIA, Airbnb and other companies; the listed interview dates are not supplied.'},
{
'slug':'metrics-platform','chapter':'03-production/04-observability','title':'Metrics platform: query the right time window','prompt':'“Hundreds of thousands of hosts emit CPU, memory, throughput, and service metrics. Engineers build dashboards and alerts. One customer labels every request with a unique user ID.”','scale':'Assume 300,000 hosts, 10-second sampling and one-year retention for downsampled aggregates.','cases':[('Normal series','CPU by host and minute','Store/query an append-only time series efficiently.'),('Cardinality explosion','Label = unique request ID','Reject, cap, or isolate unbounded series before cost explodes.'),('Late sample','Host reconnects after 5 minutes','Backfill within a defined correction window.'),('No data','Critical service stops reporting','Alert on missing telemetry separately from threshold breach.')],
'thinking':'A metric identity is name plus label set; each distinct set creates another time series. Validate schema and cardinality at ingest, aggregate high-volume counters near the source, and separate high-resolution recent data from older rollups. Alert evaluation needs durable rules, missing-data semantics, and a notification path independent of the metrics query dashboard.','artifact':'Estimate series count from hosts × metrics × label combinations. Draw ingest, rollup, query and alert paths separately.',
'services':[('Amazon Kinesis Data Streams','metric event stream','Buffer high-rate metric batches and fan out consumers.','MSK where existing Kafka ecosystem and client guarantees dominate.'),('Amazon Managed Service for Apache Flink','stream aggregation','Window, downsample and compute event-time rollups.','Lambda for simpler low-state aggregation.'),('Amazon Timestream','time-series store','Serve timestamp/measure queries with retention tiers.','Amazon S3 + Athena for long-term low-cost analytics.'),('Amazon Managed Grafana','dashboard UI','Explore metrics and dashboard operational data.','Self-managed Grafana when plugins or tenancy controls require it.'),('Amazon CloudWatch Alarms','alert evaluation','Evaluate monitored signals and route alarm state.','Prometheus Alertmanager for Prometheus-native rule ownership.')],
'edges':[(0,1),(1,2),(2,3),(2,4)],'deep':'One unique label per request can turn a handful of measurements into millions of series. Compare bounded labels (region/status) with unbounded IDs.','kind':'cardinality','shape':'CPU × 300k hosts × 10s ≈ 2.59B samples/day; adding request_id creates near one new series per request and defeats bounded retention/cost.','senior':'A region’s telemetry path is delayed but services are healthy. Keep ingestion lag, missing-data alerts, and service health independent so observability failure is visible.','staff':'Set shared metric naming and cardinality budgets across many product teams. Define admission rules, exceptions, cost allocation, and safe dashboard/query isolation.',
'source':'https://www.hellointerview.com/community/questions/metrics-monitoring-alerts/cm6k7xmwh024f11hvvc0uq1e5','source_text':'The current community interview-question catalog lists monitoring-platform reports at Meta, LinkedIn, Stripe, MongoDB and others; it does not disclose when each interview happened.'},
{
'slug':'web-crawler','chapter':'04-scale-and-evolution/01-data-at-scale','title':'Web crawler: be fast without attacking one site','prompt':'“Starting from seed URLs, discover pages and index their content. Avoid fetching the same URL repeatedly, respect publisher crawl rules, and keep making progress when a worker dies.”','scale':'Assume 1 billion discovered URLs, 50,000 fetches/s and at least once crawl execution.','cases':[('Duplicate URL','`/a?utm=x` and `/a` canonicalize equal','Normalize under a versioned rule and fetch once per policy window.'),('Same host overload','One domain has a million queued pages','Enforce per-host concurrency and politeness delay.'),('Worker crash','Page fetched but frontier ACK lost','Idempotent page version and crawl lease tolerate retry.'),('Robots change','Host disallows a path','Stop future fetches and expire queued work under the new policy.')],
'thinking':'The frontier is a durable work scheduler keyed by normalized URL and host. Deduplication controls repeated work, but politeness is per origin and needs independent rate state. Workers fetch with bounded time/body size, extract links, and write content/version before advancing the frontier. A global queue that dispatches arbitrarily can violate a host’s crawl-delay even if its total rate is low.','artifact':'Trace one URL from discovery to normalized frontier, host gate, fetch, content store, and extracted links.',
'services':[('Amazon SQS','crawl frontier queue','Durably buffer distributed page work.','Kinesis when partitions and ordered per-key ingestion dominate.'),('Amazon DynamoDB','dedupe + host leases','Conditionally claim normalized URL and host budget.','ElastiCache for transient coordination plus durable backing store.'),('Amazon ECS','crawler workers','Run bounded browser/HTTP fetch and extraction workers.','Lambda for short static-page fetches only.'),('Amazon S3','page content archive','Store compressed page versions and replay inputs cheaply.','OpenSearch as searchable index, not raw archive.'),('Amazon OpenSearch Service','content search index','Serve indexed page queries.','S3/Athena for batch research queries.')],
'edges':[(0,1),(1,2),(2,3),(3,4)],'deep':'A scheduler needs host-aware fairness: 500k queued URLs from one site must not monopolize workers. Compare global FIFO with per-host due queues.','kind':'politeness','shape':'Frontier shards by host; each host lane has next_allowed_at and max_inflight=1. Scheduler picks eligible hosts, not just oldest URL globally.','senior':'A malicious page expands into endless URLs. Set depth, URL, MIME, size and domain budgets; quarantine patterns without losing unrelated frontier work.','staff':'Change normalization after years of indexing. Build dual keys/reconciliation, quantify duplicate and omission risk, and provide a reversible index migration.',
'source':'https://www.hellointerview.com/community/questions/web-crawler-design/cm80gligm049vtvyjklc6gxdw','source_text':'The current community interview-question catalog lists web-crawler reports at ZoomInfo, Atlassian, Microsoft, Expedia and others; the reports’ interview dates are not published.'},
{
'slug':'typeahead-search','chapter':'04-scale-and-evolution/01-data-at-scale','title':'Typeahead: useful suggestions before the next keystroke','prompt':'“As a user types a query, show the top five likely completions. Popular prefixes are extremely hot; ranking data changes every few minutes.”','scale':'Assume 80,000 queries/s, 150 ms end-to-end p99, and a 3-character minimum prefix.','cases':[('Prefix `iph`','Millions of possible terms','Return top five from a bounded precomputed candidate set.'),('New trending term','Ranking changes in 2 minutes','Publish a new index version without partial mixed results.'),('One hot prefix','`a` receives 12% of queries','Cache safely and avoid recomputing full descendant scans.'),('Unicode query','User types accented text','Normalize consistently while preserving display form.')],
'thinking':'Separate offline/stream ranking from online prefix lookup. Build a versioned prefix index containing top candidates by score; online reads should be bounded by prefix and small K, not scan every completion. Keep raw popularity signals distinct from personalization. Atomically swap index versions and measure suggestion latency, zero-result rate, and freshness.','artifact':'Draw term events → rank build → immutable prefix index → cache → bounded query; mark index version on response.',
'services':[('Amazon Kinesis','query/event stream','Collect searches and clicks for ranking updates.','SQS for simple asynchronous feedback without event-time windows.'),('AWS Glue','batch index build','Normalize and aggregate historical terms.','EMR when custom large-scale compute is needed.'),('Amazon S3','versioned index files','Hold immutable prefix snapshots for atomic publish.','DynamoDB when the complete lookup fits key-value access.'),('Amazon ElastiCache','prefix cache','Protect hot prefix reads with short TTL.','CloudFront for public query results where personalization is absent.'),('Amazon ECS','suggestion API','Serve bounded prefix lookups and ranking blend.','Lambda for sparse traffic with cold-start allowance.')],
'edges':[(0,1),(1,2),(2,3),(3,4)],'deep':'Prefix `iph` maps to a bounded list already ranked offline; extending to `ipho` performs a narrower lookup. Show where personalization can add or remove candidates.','kind':'prefix','shape':'root → i → ip → iph; each prefix node points to top-K [iphone, iphones, ...], updated through an immutable index-version swap.','senior':'A new vocabulary release improves quality but makes p99 worse. Split read latency by cache/index/network and roll back only the index version.','staff':'Multiple products want one shared suggestion platform. Govern normalization, source attribution, privacy, and quality evaluation without coupling every team to one ranking model.',
'source':'https://www.hellointerview.com/community/questions/typeahead-search-system/cm7l2wazy00t7105qdvnemtwy','source_text':'The current community interview-question catalog lists typeahead reports at Databricks, Meta, Expedia and Salesforce; it does not show interview dates.'},
{
'slug':'distributed-cache','chapter':'04-scale-and-evolution/01-data-at-scale','title':'Distributed cache: recover when one shard leaves','prompt':'“Build a low-latency distributed cache across many nodes. Clients read and write keys while nodes are added, removed, or become slow. Tell me what happens to hot keys and stale values.”','scale':'Assume 20 million keys, 2 million reads/s, 200 cache nodes and an average value of 2 KB.','cases':[('Node addition','Add 10% capacity','Move a bounded fraction of keys, not nearly every key.'),('Hot key','One object gets 15k reads/s','Replicate or coalesce reads without violating allowed staleness.'),('Cache miss storm','A shard restarts','Bound origin concurrency and jitter refill; do not stampede the database.'),('Stale value','Source record changes','State invalidation/version/TTL behavior and maximum stale interval.')],
'thinking':'State whether the cache is disposable or authoritative; this problem assumes disposable. Consistent hashing limits remapping, but replication and hot-key behavior still need a policy. Use request coalescing and per-key/origin budgets for misses. Invalidation carries a source version so delayed older fills cannot replace newer values. A cache outage must degrade to a bounded origin path, not unbounded reads.','artifact':'Draw key placement, replica choice, source-of-truth version, miss coalescing, and what a node-removal event remaps.',
'services':[('Amazon ElastiCache for Redis','managed memory cache','Use when Redis data structures and managed operations fit.','Amazon MemoryDB when durable in-memory primary data is required.'),('Amazon Route 53','service discovery','Resolve stable client endpoints.','Cloud Map for service-aware registration and discovery.'),('Amazon DynamoDB','durable backing data','Supply source values and versions for cache fills.','Aurora for relational source-of-truth reads.'),('Amazon CloudWatch','cache telemetry','Observe hit ratio, evictions, node health and origin QPS.','OpenTelemetry stack with per-shard metrics.'),('Amazon ECS','cache client service','Own coalescing, version checks and bounded fallback.','Lambda for intermittent, low-throughput clients.')],
'edges':[(1,0),(1,2),(0,4),(4,3)],'deep':'With consistent hashing, adding a node moves only neighboring ring ranges. Draw old/new ownership and a hot key copied to bounded replicas.','kind':'ring','shape':'Hash ring nodes A→B→C→D; adding E splits C→D range only. Hot key K remains on a primary plus controlled replicas; stale refill is rejected by source version.',
'senior':'The cache is unavailable and origin capacity is 10% of normal read traffic. Shed or serve stale by endpoint class, cap concurrency, and show how capacity recovers.','staff':'Choose shared vs tenant-dedicated cache pools. Set eviction fairness, data classification, migration, and cost/latency SLOs.',
'source':'https://www.hellointerview.com/community/questions/distributed-cache-system/cm6d9gnep03c46hpqrwc062ir','source_text':'The current community interview-question catalog lists distributed-cache design reports at Google, Microsoft, Meta and Amazon; interview dates are not displayed.'},
{
'slug':'distributed-key-value-store','chapter':'04-scale-and-evolution/01-data-at-scale','title':'Key-value store: acknowledge only what survives','prompt':'“Design a durable distributed `put/get/delete` store. Reads should see a caller’s successful write. Nodes fail, values range from small settings to multi-gigabyte objects, and the system must scale horizontally.”','scale':'Assume 2 million operations/s, 99.99% monthly availability and keys partitioned across 300 storage nodes.','cases':[('Read after write','Client puts v8 then reads from another node','Return v8 under the stated consistency contract.'),('One replica down','Two of three replicas are healthy','Define quorum and whether a write may be acknowledged.'),('Large object','Value is 2 GB','Store bytes separately; keep metadata and chunk manifest in KV path.'),('Tombstone expires','Old replica returns deleted value','Retention/repair protocol prevents resurrection.')],
'thinking':'Choose partitioning and replication before naming a database. A write has a version, replica quorum and durability promise. Read-your-writes can use session tokens or quorum reads. Deletes need tombstones long enough to reach every replica; compaction cannot erase the only evidence too early. Large values move through object storage with checksummed manifests. Distinguish acknowledgment latency from repair convergence.','artifact':'Draw hash partition → replica set → quorum response, then show hinted handoff/repair and tombstone propagation.',
'services':[('Amazon DynamoDB','managed key-value store','Choose for managed key access patterns and conditional writes.','Amazon Keyspaces for Cassandra-compatible wide-column workload.'),('Amazon S3','large-value object store','Keep multi-GB payload bytes outside the hot metadata path.','EBS only for attached block storage, not shared object access.'),('Amazon Route 53','client endpoint routing','Resolve regional/service endpoints.','AWS Global Accelerator for static anycast ingress.'),('Amazon CloudWatch','replica health telemetry','Track write latency, throttles, replication lag and repair backlog.','OpenTelemetry metrics where custom replica internals matter.'),('AWS Backup','recovery copies','Create point-in-time recovery protection for supported resources.','Application export snapshots for cross-engine recovery needs.')],
'edges':[(2,0),(0,1),(0,3),(0,4)],'deep':'An acknowledged write is absent on one replica. Draw quorum intersection, read repair, and why expiring a tombstone too early resurrects a deleted key.','kind':'quorum','shape':'3 replicas A/B/C; write quorum 2 commits on A+B; read quorum 2 intersects any acknowledged write under chosen quorum assumptions; C repairs before tombstone GC.',
'senior':'A rack loss causes repair traffic to compete with foreground reads. Set repair bandwidth, admission priority, and degraded-mode consistency behavior.','staff':'Offer this store to teams with different data models. Define API/version contracts, isolation, migrations and when to use a managed database instead of operating a new distributed store.',
'source':'https://www.hellointerview.com/community/questions/key-value-store/cm8gcrkz800b7epmpcj06fkwk','source_text':'The current community interview-question catalog lists a distributed key-value store prompt at LinkedIn, Databricks, Geico and Microsoft; individual report dates are not listed.'},
{
'slug':'ad-click-aggregator','chapter':'04-scale-and-evolution/01-data-at-scale','title':'Ad click aggregator: count late events once','prompt':'“Advertisers want minute-level click and impression counts. Events arrive more than once and sometimes minutes late; dashboards need recent counts while analysts query years of history.”','scale':'Assume 5 billion events/day, 30-second dashboard freshness and two years of historical queries.','cases':[('Duplicate click','SDK retries event id `x91`','Deduplicate within the stated window or expose count semantics.'),('Late click','Event timestamp 12:03 arrives at 12:07','Revise the correct event-time bucket with versioned result.'),('High-cardinality','Millions of campaigns × regions × devices','Bound dimensions and partition for both writes and analytics scans.'),('Dashboard read','Query campaign for last 60 minutes','Return freshness/watermark with aggregated buckets.')],
'thinking':'Ingest immutable event IDs, event-time and dimensions, then aggregate in event-time windows. Watermarks decide when a window is provisionally complete; late arrivals update a correction path. Keep an append-only raw archive for replay. Pre-aggregation serves dashboards cheaply, while an OLAP store handles historical multi-dimensional slices. Do not force one database to serve both paths.','artifact':'Draw click → stream → event-time windows → hot aggregate and raw archive; show a late event correcting one bucket.',
'services':[('Amazon Kinesis Data Streams','event stream','Buffer and replay high-volume click records.','MSK where Kafka ecosystem and partition control fit better.'),('Amazon Managed Service for Apache Flink','windowed aggregation','Manage keyed state, event time and late records.','Lambda for simpler non-windowed consumers.'),('Amazon S3','raw event archive','Retain immutable events for recompute and audit.','Glacier tiers for older, rarely queried raw data.'),('Amazon Redshift','analytics warehouse','Query dimensional history for advertiser reporting.','Athena on partitioned Parquet for lower-frequency scans.'),('Amazon DynamoDB','recent aggregate view','Serve hot recent buckets by campaign/time key.','Timestream for primarily time-series reads with lower dimensions.')],
'edges':[(0,1),(0,2),(1,3),(1,4)],'deep':'12:03 bucket receives an event at 12:07. Show provisional result, watermark advance, correction and the freshness marker in the dashboard.','kind':'windows','shape':'12:00–12:01 window count=93 provisional; late event +1 arrives; revised version=94 after watermark policy; raw archive retains both source events.',
'senior':'A single advertiser becomes a hot partition and report requests scan too much history. Salt writes, merge on read, and cap query ranges with an async export path.','staff':'Products disagree about attribution windows and fraud filtering. Version event schemas and metric definitions, measure reconciliation gaps, and provide backfills without rewriting history invisibly.',
'source':'https://www.hellointerview.com/community/questions/ad-click-aggregator/cm4t0kxb6004488il22wqa2nn','source_text':'The current community interview-question catalog lists ad-click aggregation at Meta, Rippling, Google, Amazon and others; no date is attached to each report.'},
]

assert len(DATA)==15
INK='#243c34'; MUTED='#596b63'; GREEN='#267259'; RED='#af563e'

def text(x,y,s,size=17,color=INK,weight='normal',anchor='start'):
 return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>'
def rect(x,y,w,h,head,sub='',color=GREEN):
 fill='#fff0ea' if color==RED else '#edf7f2'
 t=text(x+w/2,y+34,head,15 if len(head)>25 else 17,INK,'600','middle')
 if sub:t+=text(x+w/2,y+63,sub,14,MUTED,'normal','middle')
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{color}" stroke-width="2"/>'+t
def arrow(x,y,xx,yy,color=GREEN):
 return f'<path d="M{x} {y} L{xx} {yy}" stroke="{color}" stroke-width="2.5" fill="none" marker-end="url(#{"g" if color==GREEN else "r"})"/>'
def wrapped(x,y,value,size=16,color=MUTED,weight='normal',width=105,step=23):
 lines=textwrap.wrap(value,width=width,break_long_words=False)[:3]
 return ''.join(text(x,y+i*step,line,size,color,weight) for i,line in enumerate(lines))
def service_rect(x,y,w,h,heading,sub):
 lines=textwrap.wrap(heading,width=26,break_long_words=False)[:2]
 out=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#edf7f2" stroke="{GREEN}" stroke-width="2"/>'
 if len(lines)==1:
  out+=text(x+w/2,y+37,lines[0],16,INK,'600','middle')+text(x+w/2,y+68,sub,14,MUTED,'normal','middle')
 else:
  out+=text(x+w/2,y+29,lines[0],14,INK,'600','middle')+text(x+w/2,y+48,lines[1],14,INK,'600','middle')+text(x+w/2,y+73,sub,13,MUTED,'normal','middle')
 return out
def svg(title,desc,body,h=560):
 return (f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{h}" viewBox="0 0 960 {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>'
 '<style>text{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}</style>'
 f'<defs><marker id="g" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{GREEN}"/></marker><marker id="r" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{RED}"/></marker></defs>'
 f'<rect x="1" y="1" width="958" height="{h-2}" rx="19" fill="#fbfcf8" stroke="#d9e2d9"/>{body}</svg>')

def draw_scene(d):
 slug=d['slug']; body=text(42,56,d['title'],25,INK,'700')
 # Signature concept card; each graph is drawn from that problem's own trace.
 body+=wrapped(43,96,d['deep'],16,MUTED,width=98,step=22)
 kind=d['kind']; shape=d['shape']
 if kind=='grid':
  for i in range(3):
   for j in range(3):
    x=320+j*105;y=151+i*93; body+=f'<rect x="{x}" y="{y}" width="92" height="80" rx="8" fill="{"#e5f4e9" if (i,j)!=(1,1) else "#fff0ea"}" stroke="{"#267259" if (i,j)!=(1,1) else "#af563e"}"/>'
    body+=text(x+46,y+43,('rider' if (i,j)==(1,1) else f'cell {i}{j}'),13,INK,'normal','middle')
  body+=text(790,192,'candidate IDs',15,GREEN,'700')+text(790,224,'freshness check',15,GREEN)+text(790,256,'road ETA',15,GREEN)
 elif kind=='intervals':
  body+=text(64,181,'Room A',16,INK,'700')
  for y,label,start,end,col in [(204,'Booked [09:00,10:00)',310,590,GREEN),(296,'Adjacent [10:00,11:00)',590,870,GREEN),(388,'Conflicting [09:59,10:30)',585,730,RED)]:
   body+=text(65,y+24,label,15,MUTED);body+=f'<rect x="{start}" y="{y}" width="{end-start}" height="38" rx="8" fill="{"#e8f4eb" if col==GREEN else "#fff0ea"}" stroke="{col}" stroke-width="2"/>'
  body+=text(495,474,'Half-open [start,end): touching edges are free; overlap is not.',16,INK,'600','middle')
 elif kind=='fanout':
  body+=rect(80,175,210,78,'One article','story s42')
  body+=arrow(300,214,410,214)
  body+=rect(421,150,214,126,'ordinary story','1,000 writes')
  body+=arrow(640,214,747,214,RED)
  body+=rect(757,150,160,126,'viral story','10,000,000 writes',RED)
  body+=rect(250,367,460,93,'hybrid reader','store once; merge hot stories on demand')
  body+=arrow(529,282,481,356)
 elif kind=='ladder':
  for i,(r,rate,w) in enumerate([('2160p','8 Mbps',670),('1080p','5 Mbps',520),('720p','2 Mbps',360),('480p','0.8 Mbps',205)]):
   y=148+i*78;body+=text(80,y+29,r,16,INK,'700');body+=f'<rect x="210" y="{y}" width="{w}" height="43" rx="8" fill="#eaf4ed" stroke="#267259"/>';body+=text(235+w,y+28,rate,15,MUTED)
  body+=text(76,493,'Each aligned segment can switch rendition as bandwidth changes.',17,INK,'600')
 elif kind=='rollout':
  for i,(label,caption,color) in enumerate([('v42','validate',GREEN),('1%','canary',GREEN),('ALARM','rollback',RED),('v41','restore config',GREEN)]):
   x=60+i*222;body+=rect(x,200,185,102,label,caption,color)
   if i<3:body+=arrow(x+187,250,x+218,250,color)
  body+=text(480,390,'Already committed data needs a repair plan; a flag cannot undo it.',17,RED,'700','middle')
 elif kind=='layers':
  for i,(h,sub) in enumerate([('Public API','size + identity'),('Durable queue','bounded payload'),('Ephemeral sandbox','CPU · memory · time'),('Result checker','no secrets to user')]):
   y=133+i*89;body+=rect(184,y,582,69,h,sub,RED if i==2 else GREEN)
   if i<3:body+=arrow(475,y+71,475,y+85)
  body+=text(482,518,'Network denied · filesystem temporary · worker role scoped',16,MUTED,'normal','middle')
 elif kind=='states':
  seq=shape.split(' → ')
  for i,s in enumerate(seq):
   x=32+i*(900/len(seq));body+=rect(x,208,150,84,s,'one owned transition',RED if 'refund' in s or 'conflict' in s else GREEN)
   if i<len(seq)-1:body+=arrow(x+152,250,x+174,250)
  body+=text(480,390,'Every retry reads durable state before creating another side effect.',17,MUTED,'600','middle')
 elif kind=='politeness':
  for i,(host,queued,nextat) in enumerate([('site A','500k','12:02:00'),('site B','120','12:00:04'),('site C','9','12:00:01')]):
   y=150+i*103;body+=rect(70,y,225,71,host,queued+' URLs');body+=rect(530,y,250,71,'next allowed',nextat);body+=arrow(305,y+35,518,y+35)
  body+=text(482,490,'Choose among eligible hosts, not the largest global queue.',17,GREEN,'700','middle')
 elif kind=='prefix':
  for i,(prefix,topk) in enumerate([('i','ipod · iphone · ipad'),('ip','iphone · ipad · ipod'),('iph','iphone · iphones · ...'),('ipho','iphone · iphones · ...')]):
   x=55+i*220;body+=rect(x,210,190,106,prefix,topk)
   if i<3:body+=arrow(x+192,262,x+215,262)
  body+=text(480,412,'Top-K per immutable index version keeps work bounded.',17,MUTED,'600','middle')
 elif kind=='ring':
  body+='<circle cx="480" cy="300" r="180" fill="none" stroke="#9db6a5" stroke-width="3"/>'
  for i,n in enumerate('ABCDE'):
   import math
   angle=math.radians(-90+i*72);x=480+180*math.cos(angle);y=300+180*math.sin(angle)
   body+=f'<circle cx="{x:.1f}" cy="{y:.1f}" r="31" fill="{"#fff0ea" if n=="E" else "#edf7f2"}" stroke="{"#af563e" if n=="E" else "#267259"}" stroke-width="2"/>'+text(x,y+6,n,17,INK,'700','middle')
  body+=text(480,525,'Adding E remaps its adjacent ring range; hot keys need a separate replica policy.',15,MUTED,'normal','middle')
 elif kind=='quorum':
  for i,n in enumerate('ABC'):
   x=170+i*230;body+=rect(x,161,165,95,'Replica '+n,('ACK write v8' if n in 'AB' else 'missed v8'),GREEN if n in 'AB' else RED)
  body+=arrow(330,272,576,329);body+=arrow(560,272,386,329)
  body+=rect(330,343,300,90,'Quorum intersection','read meets A or B; repair C')
  body+=text(480,485,'Do not garbage-collect a delete marker before replicas have converged.',16,RED,'700','middle')
 elif kind=='windows':
  body+=rect(80,158,225,100,'12:00 bucket','93 · provisional')
  body+=arrow(312,207,412,207,RED)
  body+=rect(422,158,210,100,'Late event','event time 12:00')
  body+=arrow(640,207,736,207)
  body+=rect(746,158,172,100,'Revised','94 · v2')
  body+=f'<path d="M80 333 H919" stroke="#96ab9d" stroke-width="2"/><path d="M305 319 V350 M735 319 V350" stroke="{GREEN}" stroke-width="3"/>'
  body+=text(307,392,'window start',15,MUTED,'normal','middle')+text(737,392,'watermark / correction',15,MUTED,'normal','middle')
 elif kind=='cardinality':
  body+=text(95,155,'LABELS',14,MUTED,'700')
  body+=rect(80,180,350,91,'region × status','bounded combinations')
  body+=rect(510,180,350,91,'request_id','near one series per request',RED)
  body+=text(254,337,'~few thousand series',18,GREEN,'700','middle')
  body+=text(686,337,'unbounded cardinality',18,RED,'700','middle')
  body+=text(480,444,'Series count = metric name + every distinct label set.',17,INK,'600','middle')
 elif kind=='race':
  body+=rect(78,182,245,93,'Request A','alias = launch')+rect(637,182,245,93,'Request B','alias = launch')
  body+=arrow(330,224,413,300)+arrow(635,224,546,300)
  body+=rect(360,304,240,90,'Unique condition','only one create wins')
  body+=arrow(397,400,285,450,GREEN)+arrow(564,400,700,450,RED)
  body+=rect(72,457,245,66,'Winner','code reserved')+rect(642,457,245,66,'Loser','409 conflict',RED)
 elif kind=='geo':
  body+=rect(82,163,230,86,'Location update','event time + accuracy')
  body+=arrow(315,205,405,205)
  body+=rect(417,163,230,86,'Geo cell index','short-lived candidates')
  body+=arrow(650,205,739,205)
  body+=rect(750,163,160,86,'Route ETA','road distance')
  body+=rect(252,352,440,91,'Atomic driver claim','one offer token wins')
  body+=arrow(829,256,652,347)
 else:
  body+=rect(115,220,710,128,d['title'].split(':')[0],d['artifact'][:55])
 return body


for d in DATA:
 chapter=ROOT/'curriculum'/d['chapter'];path=chapter/'problems'/f"{d['slug']}.md"
 source_note=f"**Evidence and origin:** {d['source_text']} The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop."
 body=f"""# {d['title']}

> **Interviewer:** {d['prompt']}

This is a **commonly listed system-design interview prompt** with a concrete practice contract. {d['scale']} Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
"""
 for a,b,c in d['cases']: body+=f'| {a} | {b} | {c} |\n'
 body+=f"""
![The failure path and repaired design for {d['title'].split(':')[0]}](../../../../assets/design-interview/{d['slug']}-before.svg)

## Think from the contract to the boxes

{d['thinking']}

**First diagram:** {d['artifact']}

![AWS services named with their provider-neutral architectural roles](../../../../assets/design-interview/{d['slug']}-aws.svg)

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
"""
 for svc,role,why,alt in d['services']: body+=f'| **{svc}** / {role} | {why} | {alt} |\n'
 body+=f"""
Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

![A focused failure, capacity, or state diagram for {d['title'].split(':')[0]}](../../../../assets/design-interview/{d['slug']}-deep.svg)

## Pressure-test the design

**Follow-up: {d['deep']}**

**Senior expectation:** {d['senior']}

**Staff expectation:** {d['staff']}

**Practice artifact:** {d['artifact']} Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

{source_note}

**Interview report listing:** [Open the community question entry]({d['source']}).
"""
 path.write_text(body,encoding='utf-8')

 # Contrast image: three explicit failures on the left; repaired authority on right.
 title=d['title'].split(':')[0];fail=[x[0]+': '+x[2] for x in d['cases'][:3]];fix=[d['cases'][0][2],d['cases'][1][2],d['cases'][2][2]]
 s=text(42,55,title+' / BEFORE AND AFTER',25,INK,'700')
 s+='<rect x="34" y="86" width="425" height="424" rx="16" fill="#fff6f2"/><rect x="501" y="86" width="425" height="424" rx="16" fill="#eff8f2"/>'
 for x,caption,arr,col in [(53,'WITHOUT A CONTRACT',fail,RED),(521,'WITH AN EXPLICIT GUARANTEE',fix,GREEN)]:
  s+=text(x,124,caption,14,col,'700')
  for i,label in enumerate(arr):
   y=151+i*111;s+=rect(x+12,y,350,75,label[:45],color=col)
   if i<2:s+=arrow(x+185,y+78,x+185,y+103,col)
 (ASSETS/f"{d['slug']}-before.svg").write_text(svg(title+': design failure and repair','Three failure examples compared with their repaired outcomes.',s),encoding='utf-8')

 # AWS diagram: service label and generic architectural role share each box.
 s=text(42,50,'AWS SERVICE / GENERAL ROLE',15,MUTED,'700')+text(42,87,title,25,INK,'700')
 slots=[(35,131),(350,131),(665,131),(193,359),(508,359)]
 edges=d.get('edges',[(0,1),(1,2),(2,3),(3,4)])
 for a,b in edges:
  x,y=slots[a];xx,yy=slots[b]
  if y==yy and x<xx:s+=arrow(x+274,y+48,xx-10,yy+48)
  elif y==yy:s+=arrow(x-5,y+48,xx+280,yy+48)
  elif y<yy:s+=arrow(x+137,y+100,xx+137,yy-12)
  else:s+=arrow(x+137,y-7,xx+137,yy+111)
 boxes=d['services'][:5]
 for (x,y),(svc,role,why,alt) in zip(slots,boxes): s+=service_rect(x,y,270,96,svc,role)
 s+=text(44,523,'The product name is shown with its general role. The page explains alternatives and guarantees.',15,MUTED)
 (ASSETS/f"{d['slug']}-aws.svg").write_text(svg(title+': AWS service and role boxes','; '.join(svc+' is '+role for svc,role,_,_ in boxes),s),encoding='utf-8')

 # Signature visual (unique diagram grammar per problem).
 s=draw_scene(d)
 (ASSETS/f"{d['slug']}-deep.svg").write_text(svg(title+': pressure test',d['deep']+' '+d['shape'],s),encoding='utf-8')

print(f'Wrote {len(DATA)} interview problems and {len(DATA)*3} diagrams')
