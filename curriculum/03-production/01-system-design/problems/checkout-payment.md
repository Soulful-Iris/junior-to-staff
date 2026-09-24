# Checkout: paid twice, ordered once?

## What you are building

> Build checkout for a small online retailer. Customers reserve stock, pay through an external provider and receive an order confirmation. During an incident, a provider charges the card but its response is lost. Support needs to distinguish an unpaid order from an unknown payment and repair it without charging twice.

**Working contract:** POST /checkouts requires a stable request ID and cart fingerprint. GET /checkouts/{id} exposes pending, payment_unknown, paid, confirmed or refund_required. Timeout must never be translated into definitely_not_charged.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 200 checkout requests/s peak | At a two-second mean provider response, about 400 calls are in flight; connection pools and provider quotas need an explicit ceiling. |
| 10% of provider responses time out | At peak, 20 unknown outcomes/s need reconciliation; unknown is a stored state, not an error message discarded from logs. |
| Inventory hold: 10 minutes | A late successful payment may arrive after stock is released; reserve, finalize or refund through explicit compensating work. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/checkout_payment.py
```

[Open the starting code](../../../../examples/architecture-starts/checkout_payment.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| checkouts | checkout_id,request_id,cart_hash,state | One immutable customer intent per request identity. |
| payment_attempts | checkout_id,provider_key,charge_id,status | Owns the relationship to provider evidence. |
| outbox | checkout_id,event_version | Confirmation and repair jobs committed with order state. |

## AWS implementation

![Checkout: paid twice, ordered once?: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/checkout-payment.svg)

Aurora owns order truth; the provider owns charge truth. A queue coordinates retryable work across those authorities. Their independent commits are the reason for a durable unknown state and compensating actions.

## Build it in this order

### 1. Persist checkout before contacting payment

Validate the cart and calculate money in integer minor units with currency. Store request ID, cart fingerprint and the reserved-stock reference. Exact replay returns the same checkout; changed cart under that ID returns 409.

### 2. Record the payment attempt

Allocate one provider key for this order attempt and persist it before sending. Apply a bounded deadline. A timeout records `payment_unknown`; it does not clear the attempt key. Use a provider that supports deduplication and lookup for the required retry horizon.

### 3. Reconcile ambiguous outcomes

Implement `reconcile.py` to look up the attempt or safely repeat the same key under the provider’s contract. Validate webhook signatures and deduplicate provider event IDs. Handle callbacks arriving before, during or after polling with conditional state transitions.

### 4. Finalize or compensate

Commit paid evidence and order transition. If the inventory hold is gone, record `refund_required` or attempt an explicit new reservation according to product policy. Put confirmation/refund work in an outbox. A database rollback cannot undo a completed external charge.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Aurora PostgreSQL | Unique request and provider-operation keys; one transaction for order state and outbox; size DB connections independently of HTTP concurrency. |
| SQS reconciliation queue | Retain the original checkout identity on retries; DLQ after bounded failures; monitor oldest unknown-payment age. |
| Payment integration | Keep credentials in Secrets Manager; validate callback signatures; document provider idempotency retention and query behavior before live charging. |
| API + worker separation | Return pending status without holding a request open for a long reconciliation loop. Restrict the worker role to required tables and secrets. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Order becomes payment_unknown, then paid; the provider fixture contains one charge. |
| Retry with a changed cart | 409 and no second payment attempt. |
| Let stock expire before payment is confirmed | A visible repair/refund state, never an invented all-or-nothing rollback. |

## The next design decision

Add two payment providers. Define which provider owns an attempt before failover: switching providers after a timeout can create two charges because their idempotency domains are independent. Route only new attempts automatically; reconcile ambiguous existing ones with their original provider.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



Assume 200 checkout requests/s peak, 10% provider timeouts during an incident, and an inventory reservation that expires after ten minutes. These are exercise conditions. Clarify whether the contract promises no duplicate charge, no duplicate order, or both; each needs its own authority.

| Event sequence | Required decision |
|---|---|
| Provider charges, response lost | Retry uses same provider idempotency key; reconcile unknown result |
| Client retries same checkout with changed cart | Reject conflicting reuse of request ID |
| Inventory hold expires while charge succeeds | Order state records repair/refund work; do not pretend payment rolled back |
| Confirmation worker receives duplicate | One confirmation event per committed order version |

## Find each authority

Your order database owns order state; the payment provider owns charge state; an inventory authority owns the hold. Save checkout intent and immutable cart fingerprint before calling the provider. Reuse one provider key per order attempt and check the provider's actual idempotency retention; your internal record must live long enough for your retry and reconciliation window. Unknown is a real state between attempted and verified success. Never treat a timeout as “not charged.”

## A durable answer under failure

Show PENDING → PAYMENT_UNKNOWN/PAID → CONFIRMED or REFUND_REQUIRED. Persist the external charge reference on confirmation. To send receipts, commit an outbox event in the same database transaction as the order state and publish it asynchronously; consumers still deduplicate delivery. The reconciliation job compares provider charge IDs and local order IDs, pays attention to refunds and provider webhooks arriving out of order, and reports exceptions to a human owner.

## Put the AWS names on the boxes

**Why these boxes, and what changes the choice:** An Aurora transaction records intent and local state; DynamoDB transactional writes are an alternative for key-oriented orders. SQS retries can duplicate work: the provider idempotency key and status lookup are still required. An ECS worker suits high-volume, long-running reconciliation.



**Senior follow-up:** Provider idempotency lasts only 24 hours; a DLQ is replayed in three days. Derive why replaying a charge blindly is unsafe, then use provider status lookup, a durable attempt record, and manual escalation for unknowns. Make the maximum auto-retry window explicit.

**Staff follow-up:** Regional failover starts a second worker while the first may still run. Fence ownership or use the same durable order ID/provider key; decide how to audit and repair split decisions. Explain what “exactly once” refers to and what proof you can actually gather.

**Practice artifact:** Three-column ledger of order, hold, and charge after each failure; before/after diagram; operator reconciliation checklist; and one replay test where provider success arrives late.

**AWS translation:** RDS transaction/outbox or DynamoDB transactions for local state; SQS for retryable workers (at least once); EventBridge for notification routes; provider payment API remains external. SQS FIFO deduplication has a bounded interval and cannot make a provider side effect globally exactly once. See [AWS SQS deduplication](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html).

**Source note:** Constructed practice, not an attributed interview or payment provider guarantee.

</details>
