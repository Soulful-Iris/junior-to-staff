# Webhook delivery: a timeout is not a rejection

## What you are building

> Build outbound webhooks for a commerce API. A customer endpoint returns 500 for an hour, another is healthy, and a third accepts an event but drops the response. Operators need to replay a specific event without creating a new business event.

**Working contract:** Each committed source event creates one logical delivery per subscription. Attempts may repeat for 48 hours. Receivers use stable event IDs to deduplicate; senders sign the exact body and expose delivery history.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 50,000 subscriptions; 8,000 source events/s | Delivery rate equals events times matching subscriptions; measure fan-out instead of assuming 8,000 HTTP calls/s. |
| 48-hour retry window | Backlog storage depends on failure rate and payload size; cap per-endpoint outstanding work. |
| Ten-second HTTP deadline; 1,000 concurrent calls | At ten-second service time capacity is only 100 attempts/s, so deadlines and concurrency materially change throughput. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/webhook_delivery.py
```

[Open the starting code](../../../../examples/architecture-starts/webhook_delivery.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| events | event_id,schema_version,body_hash | Immutable source event and exact bytes. |
| deliveries | subscription_id,event_id,state,next_attempt | One logical delivery with bounded retry horizon. |
| attempts | delivery_id,attempt_no,status,latency | Individual network outcomes; never overwrite history. |

## AWS implementation

![Webhook delivery: a timeout is not a rejection: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/webhook-delivery.svg)

SQS transports work; the ledger owns retry eligibility and evidence. Per-endpoint limits are application behavior and do not appear automatically because the queue scales.

## Build it in this order

### 1. Commit source and dispatch intent

Write an outbox event with the business transition. Expand eligible subscriptions using a recorded subscription snapshot or clearly defined selection time. Preserve event ID and immutable body through every retry and manual replay.

### 2. Implement signed HTTP delivery

Sign timestamp plus raw body bytes with the subscription secret. Document verification, timestamp tolerance and rotation overlap. Use HTTPS, strict deadlines and capped response bodies. Validate destination DNS and every redirect against an outbound policy; block private and metadata addresses at connection time.

### 3. Isolate failing endpoints

Limit concurrency per endpoint and tenant. Apply bounded exponential backoff with jitter and a 48-hour terminal deadline. A healthy destination must keep progressing while another fails. Respect a capped Retry-After without allowing an endpoint to consume unbounded resources.

### 4. Expose replay and ambiguity

Return event and attempt history to authorized customers. A 2xx means the endpoint accepted the request, not that its business logic ran exactly once. Manual replay uses the same event identity and is recorded as another attempt.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Worker networking | Route outbound requests through a controlled egress path; the application must pin validated destinations and avoid redirect bypasses. |
| SQS scheduling | For retries beyond a queue delay limit, keep next_attempt in the ledger and dispatch due work; do not sleep a worker for hours. |
| Secret access | Fetch only the subscription secret/version needed; never put secrets in payload logs or customer-visible attempt records. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Both attempts carry one event identity; the receiver applies it once. |
| Make one endpoint return 500 | Other endpoints continue; failed attempts back off and eventually expire. |
| Redirect to a private address | The worker records a destination-policy rejection before opening the connection. |

## The next design decision

Allow customers to rotate a secret while attempts wait. Decide whether you sign with the current secret or an event-bound version, publish the overlap contract, and show how receivers verify a replay.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



**Your contract.** Assume 50,000 subscriptions, 8,000 events/s at peak, 48-hour delivery attempts, endpoint-specific secrets, and a visible replay tool. Ask whether per-subscription ordering matters: it changes partitioning and throughput. This is a constructed practice problem.

| Event at our boundary | Expected state and next action |
|---|---|
| Checkout commits `order.paid` but producer crashes | Durable outbox retains the event for later dispatch |
| Receiver commits event `e21`, response is lost | Retry **same event ID**; receiver should deduplicate; delivery remains uncertain until success |
| Receiver returns 429 with retry hint | Back off for this destination, preserve other destinations' progress |
| Permanent 400 due to obsolete schema | Stop repeated hot retries; surface a failure and replay path after repair |

## Reason about two boundaries

In the order transaction, write an outbox row with a stable event ID; a dispatcher publishes it asynchronously. Each subscription gets a **delivery attempt record** keyed by event ID and endpoint. Sign the raw payload with a rotating secret, enforce an outbound URL policy against private-network targets, and use a short timeout. Retries with jitter are bounded by age and attempts. A 2xx confirms transport reception only; the merchant owns idempotent processing. A replay uses the same event ID for the same logical event, with a new delivery-attempt ID.

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| Aurora PostgreSQL outbox | Atomically commit order plus event intent | DynamoDB transaction with an outbox item for a DynamoDB-owned order |
| EventBridge | Route events to interested subscriptions | SNS for simple topic broadcast with fewer routing needs |
| SQS per delivery tier | Buffer retries and isolate slow endpoints | EventBridge API destinations for a simpler managed outbound path when its timeout and retry controls fit |
| Lambda or ECS worker | Sign, rate-limit, call endpoint, record outcome | ECS when long-lived connection control or predictable high throughput dominates |
| SQS dead-letter queue | Retain exhausted deliveries for triage and replay | Explicit failure table if richer query and operator tooling are required |

EventBridge routing plus a queue does **not** make the order write atomic with publication. The outbox and reconciler close that gap. If using EventBridge API destinations directly, verify its execution timeout and bounded retry behavior against the 20-second receiver; use an asynchronous receipt contract where necessary.

**Senior follow-up:** One customer floods 429s. Budget per-endpoint concurrency and inspect oldest queued age, retry count, terminal failures, and delivery-to-commit delay; ensure their backlog does not consume the whole worker pool.

**Staff follow-up:** Rotate signing keys without invalidating already queued events. Define which payload schema and secret version each attempt uses; explain how consumers migrate versions and how operators replay a week without a thundering herd.

**Practice artifact:** Draw the order transaction, delivery lane, and operator replay lane. Walk the four rows above and distinguish event ID from attempt ID.

**Source boundary:** Original exercise. Current [EventBridge API destinations](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html) and [DLQ behavior](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html) supply AWS constraints; neither makes the receiver exactly-once.

</details>
