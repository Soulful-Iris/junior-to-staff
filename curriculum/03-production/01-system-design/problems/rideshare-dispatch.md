# Ride sharing: one driver, one accepted ride

## What you are building

> Build dispatch for a ride service. Nearby-driver search finds two candidates, but the same driver receives offers for two riders. GPS messages arrive out of order, and a disconnected dispatcher resumes after its lease expired.

**Working contract:** A ride and driver may belong to at most one active assignment. Location search suggests candidates; accepting an offer conditionally commits the ride, driver and offer under the current dispatch epoch.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Five million active drivers; one update every five seconds | One million location updates/s if all are reporting; regional partitioning and retention are major decisions. |
| Location p95 age under five seconds | Track event age separately from ingestion latency; stale positions must be excluded or clearly downgraded. |
| Ten-second offer lifetime | A late acceptance must fail after the offer is replaced or expires. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/rideshare_dispatch.py
```

[Open the starting code](../../../../examples/architecture-starts/rideshare_dispatch.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| locations | driver_id,event_time,sequence,cell | Latest useful position; a lossy search projection. |
| rides / drivers | ride_id and driver_id,assignment,status | Authoritative availability and ownership. |
| offers | offer_id,ride_id,driver_id,epoch,expires_at | A bounded invitation, not an assignment. |

## AWS implementation

![Ride sharing: one driver, one accepted ride: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/rideshare-dispatch.svg)

The high-volume location path can drop obsolete updates; the assignment path cannot drop ownership conflicts. Keeping those paths separate prevents a fast but stale geo cache from assigning one driver twice.

## Build it in this order

### 1. Build regional candidate lookup

Partition positions by geographic cell and region. Accept only newer per-driver sequence updates; expire stale locations. Query neighboring cells and rank by estimated pickup time. A geo index may contain a driver who is already assigned, so treat each candidate as provisional.

### 2. Create a versioned offer

Persist ride, driver, expiry and dispatcher epoch. Deliver the offer with a stable offer ID. The mobile client shows its expiration and sends that exact ID when accepting, rather than submitting a new free-form driver choice.

### 3. Commit both owners together

In DynamoDB TransactWriteItems, update ride and driver with availability conditions and update the offer with epoch/expiry conditions. All conditions belong to that single transaction. On conflict, fetch current ride status before trying another candidate.

### 4. Handle disconnects and cancellation

A new dispatcher increments ownership epoch before issuing replacement offers. Old acceptances and old dispatchers fail conditional writes. Cancellation releases a driver only if the assignment ID still matches; it cannot clear a newer assignment.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Location stream | Choose partition keys and provision shards/throughput from measured record size; monitor per-partition lag and event age. |
| DynamoDB transactions | Keep ride/driver/offer checks in one transaction in the selected region; persist request identity beyond SDK retry-token windows. |
| WebSocket delivery | Track connections as ephemeral routes; reconnect fetches durable offer/ride state. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | r1 owns d7; r2 conflicts; sequence 8 cannot overwrite sequence 9. |
| Accept an expired offer | The write is rejected even if its push notification arrived late. |
| Resume a paused old dispatcher | Its epoch cannot commit a new assignment. |

## The next design decision

Let a driver cross a regional boundary while an offer is active. Choose one assignment authority until the ride completes or perform an explicit authority transfer. Do not independently mark the driver free in both regions.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>

> **Interviewer:** “A rider asks for a car. Drivers move every few seconds, one driver can accept only one trip, and the rider wants a live ETA. Design matching and state transitions.”

This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 5 million active drivers, location p95 younger than 5 seconds, and bursts around commute and event traffic. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Fresh location | Driver D7 reports at 10:00:03 | Search a bounded nearby-cell set; compute road ETA before offer. |
| Two accept attempts | Both try to assign D7, or two drivers accept the same ride | One joined assignment transaction wins; the loser retries matching. |
| Late acceptance | D7 accepts after offer expires | Reject stale offer token and continue matching. |
| Stale GPS | D8 was nearby 40 seconds ago | Exclude or down-rank by freshness; do not claim it is currently nearby. |

![The failure path and repaired design for Ride sharing](../../../../assets/design-interview/rideshare-dispatch-before.svg)

## Think from the contract to the boxes

Split the fast changing location index from the authoritative ride record. Geospatial cells find candidates; a road-network ETA ranks them. An offer has an expiry and token. An offer is a short-lived invitation, not a reservation. On accept, commit driver ownership, ride ownership and replay identity together. GPS updates are hints, not ownership.

### The decision that makes one assignment true

`POST /rides/{ride_id}/accept` carries `offer_id` and `operation_id`; the authenticated driver identity comes from the server. In a single-region DynamoDB transaction, check that the offer names this driver and ride, is still open and unexpired; conditionally change `Driver(D7): AVAILABLE → RESERVED(ride_id)` and `Ride(R9): SEARCHING → ASSIGNED(D7)`; consume the offer; store `Operation(driver, operation_id, request_hash, result)` and an outbox event. Reuse of an operation ID with a different request is a conflict.

```mermaid
flowchart LR
  A["Accept: D7, R9, operation K"] --> T["One transaction: offer + driver + ride + replay + outbox"]
  T --> OK["Commit: D7 owns R9; R9 names D7"]
  T --> NO["Conflict or expiry: no reservation committed"]
  OK --> R["Relay event; duplicate delivery allowed"]
```

| Interleaving | Required outcome |
|---|---|
| D7 accepts R9 and R10 concurrently | Driver condition lets only one transaction commit. |
| D7 and D8 accept R9 concurrently | Ride condition lets only one transaction commit. |
| Process dies before transaction commit | Neither side is reserved; another attempt may win. |
| Commit succeeds; reply or event delivery is lost | Read the stored operation result; outbox relay retries. No second assignment. |

Treat transaction conflicts as conflicts, not as unconditional retries of stale offers. The server checks expiry at the acceptance decision using a trusted clock; an expired TTL row is not proof of deletion. One authority Region owns each ride/driver assignment. At five million drivers reporting every five seconds, ingress is **one million location updates/s** before retries: partition and rate-limit that separate hint path. Measure accept throughput independently; a hot city must not serialize on one shared counter.

**Acceptance exercise:** run both races above, interrupt immediately before/after commit, and replay the same operation. Assert both uniqueness rules and no permanently reserved driver without an assigned ride. These are proposed deployment tests, not a claim of live DynamoDB execution.

**First diagram:** Draw location ingress separately from offer/accept state. Label freshness, cell coverage, offer expiry, and the conditional reservation.

![AWS services named with their provider-neutral architectural roles](../../../../assets/design-interview/rideshare-dispatch-aws.svg)

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon API Gateway** / rider/driver entry | Authenticate updates and ride requests. | ALB + ECS for persistent bidirectional traffic. |
| **Amazon Kinesis** / location update stream | Buffer high-volume GPS changes. | MSK when Kafka tooling and replay consumers dominate. |
| **Amazon ElastiCache** / geo candidate index | Keep short-lived driver cells and availability hints. | MemoryDB for stronger in-memory durability; a dedicated geo index for richer shapes. |
| **Amazon DynamoDB** / ride + reservation state | Transact driver, ride, offer, replay result and outbox conditions together. | Aurora for transactional multi-entity booking with lower write scale. |
| **Amazon Location Service** / route and ETA | Estimate route distance/time from candidates. | Self-hosted routing when map coverage, control, or price requires it. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

![A focused failure, capacity, or state diagram for Ride sharing](../../../../assets/design-interview/rideshare-dispatch-deep.svg)

## Pressure-test the design

**Follow-up: Drivers occupy moving grid cells, but a cell match is only candidate discovery. Draw neighboring-cell expansion, GPS age, and the later atomic accept decision.**

**Senior expectation:** An event venue creates a hot cell and floods location writes. Split or salt the index while preserving a bounded search radius and explain how drivers move between cells.

**Staff expectation:** Different cities need local matching and disaster recovery. Define regional ownership, cross-region request behavior, regulatory location retention, and fairness across driver cohorts.

**Practice artifact:** Draw location ingress separately from offer/accept state. Label freshness, cell coverage, offer expiry, and the conditional reservation. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists ride-sharing design reports at companies including Google, Salesforce, Visa, and Meta; dates are generally omitted. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/rideshare-architecture/cm6u9yzg000y87oi9k1oi7qx8).

</details>
