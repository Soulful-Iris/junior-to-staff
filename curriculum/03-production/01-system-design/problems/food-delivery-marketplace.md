# Build restaurant discovery and authoritative checkout

## Application background

A customer browses nearby restaurants, sees a meal for £12.50 and adds it to a basket. The browsing page uses a searchable copy of restaurant data so it can respond quickly. The restaurant may change a price or sell out before the customer pays.

At checkout, the application must ask the current menu and inventory records whether it can still accept the order. A price shown earlier is not permission to charge a different amount without telling the customer.

### Example walkthrough

| Action | Expected behavior |
|---|---|
| The customer sees a £12.50 meal | Show the price and selected meal. |
| The restaurant raises the price before checkout | Ask the customer to accept the new price. |
| The restaurant has sold out | Reject that item instead of confirming an impossible order. |

The search copy helps users discover meals. The authoritative records are the current records that decide whether an order may be accepted.

## Your assignment

**Deliver:** Build restaurant browsing and order placement. At checkout, check the current price and availability before confirming what the customer agreed to buy.

**Required behavior:** GET /restaurants searches nearby open restaurants. POST /orders submits item IDs, displayed price version and request identity. The order service revalidates availability and returns either a committed priced order or an explicit change requiring customer acceptance.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope. The cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/food_delivery_marketplace.py
```

**Supplied file:** [`examples/architecture-starts/food_delivery_marketplace.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/food_delivery_marketplace.py). You can also [read or download the source here](../../../../examples/architecture-starts/food_delivery_marketplace.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only. It does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ. Compare the state transitions and outcomes.

```text
{'status': 409, 'new_price': 1400, 'needs_acceptance': True}
```

### Set up your implementation workspace

Create `work/food-delivery-marketplace/` in your checkout (or use a separate repository). Copy the supplied mechanism into that directory as `mechanism.py`, then extract its state transitions into functions you can call from your implementation. The record and module names below describe what you must implement. They are not a promise that files with those names already exist. Keep a `README.md` beside your implementation with its exact run commands and observed results.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| menu_items | restaurant,item,price_minor,currency,version | Authoritative price and sale availability. |
| search_documents | restaurant,location,menu_revision | Discovery projection with freshness metadata. |
| orders | customer,request_id,priced_items,state | Immutable accepted price snapshot and fulfillment state. |

## Implement the assignment

### 1. Build discovery as a projection

Store restaurant opening rules, service area and menu revision in the source database. Index geographic/search fields asynchronously. Return an as-of marker and stable IDs. Do not place the only copy of availability in the search index.

### 2. Make checkout authoritative

Load current items and versions inside the order transaction. Calculate integer minor-unit totals, currency, fees and taxes under an explicit pricing policy. A changed price returns a new quote for acceptance instead of silently charging more.

### 3. Track fulfillment transitions

Record created, restaurant_accepted, preparing, assigned, delivered or cancelled with conditional versions. A restaurant rejection and a payment success need an explicit refund/reconciliation path. Separate estimated delivery time from a guaranteed promise.

### 4. Add dispatch and degraded browsing

Use location/routing services for candidate travel estimates. When search indexing lags, show stale discovery honestly and keep authoritative checkout available where possible. Bound restaurant-level order intake so a viral promotion cannot create impossible kitchen demand.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | The old £12.50 cart receives a £14.00 change requiring acceptance. |
| Remove an item while search is stale | Checkout rejects the unavailable item. |
| Retry a committed order | The original order returns without another charge. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target. The local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 200,000 restaurants. Two million concurrent shoppers | Popular restaurants and geographic cells are hot spots even when total capacity is sufficient. |
| Catalog freshness target: 30 seconds | Search may be stale. Price and stock are checked again at the order boundary. |
| 100 items/restaurant assumption | 20 million menu records before option combinations and search-index overhead. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Build restaurant discovery and authoritative checkout: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/food-delivery-marketplace.svg)

OpenSearch finds candidates. Aurora decides what is being purchased. A location service provides geography and routing, not inventory ownership or a restaurant’s ability to fulfill an order.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local static/media delivery path | Amazon CloudFront: shopper application delivery | Configure an origin, cache policy and private-content access. Distinguish cached bytes from current authorization. |
| Application or worker process | Amazon ECS: marketplace API | Build a container and task definition. Supply configuration, task roles and graceful shutdown behavior. |
| Local derived search records | Amazon OpenSearch Service: discovery index | Implement indexing, updates/deletions and queries. Recheck current authorization before returning sensitive results. |
| Local records and transaction boundary | Amazon Aurora PostgreSQL: order and menu authority | Write PostgreSQL schema/migrations and a database adapter. Configure credentials, connection limits and recovery. |
| Local coordinates or nearby candidate calculation | Amazon Location Service: geographic routing | Implement geospatial query/update adapters and a freshness rule. Assignment authority stays in the reservation state. |
| Local pending-work collection | Amazon SQS: fulfillment events | Publish committed job intent, consume messages and persist deduplication/ownership state. Add visibility, retry and dead-letter handling. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Search index | Version source updates and tombstones. Monitor oldest unapplied change, not just cluster health. |
| Order database | Unique customer/request identity, short transactions and explicit price snapshots. |
| Location integration | Treat route estimates as time-sensitive predictions. Cache within a documented freshness bound. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement. It is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works
### Worked follow-up: Coordinate restaurant acceptance before capturing payment

A restaurant cannot fulfill an item even though discovery showed it available. Capturing money and declaring success before acceptance leaves the system with a business obligation that a database rollback cannot erase.

| Starting design | Changed requirement |
|---|---|
| Checkout reserves items under an accepted quote. | The restaurant may reject or time out, and substitutions need customer consent. |

**Revised architecture.** Follow the changed responsibility and failure path below. This is a design to implement. The supplied local example does not provision these components.

```mermaid
flowchart TD
O["Accepted quote"] --> R["Restaurant decision"]
 O --> P["Payment authorization"]
 R -->|accepted unchanged| C["Capture eligibility"]
 P --> C
 R -->|substitution| U["Renew customer consent"]
 R -->|reject or timeout| X["Cancel and reconcile authorization"]
```

**What to implement.** Persist the accepted quote, promotion version and substitution permissions. Track restaurant acceptance and payment authorization separately. Capture only when the chosen policy permits fulfillment. On timeout, move the order to a visible unresolved or cancellation state and void authorization where supported. A changed price or unapproved substitution creates a new customer decision. Use durable workflow state and idempotent provider adapters, with compensation recorded as its own operation.

**Walk through the result.** Order O authorizes payment, then the restaurant proposes a more expensive replacement. Show awaiting customer approval with no capture. Decline the replacement and record cancellation plus the authorization-release outcome. If release is uncertain, retain repair work rather than marking every component rolled back.




Add restaurant-specific promotions and substitutions. Define which changes require renewed customer consent and which can be applied within the accepted quote. Preserve the exact accepted policy version.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 200,000 restaurants, 2 million concurrent shoppers during dinner, and availability freshness within 30 seconds. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Nearby search | Cuisine + 3 km radius | Return open restaurants whose location and filters match. |
| Menu race | Last item sells after browse | Reject or substitute before payment capture. Explain the reservation rule. |
| Courier GPS stale | Last update 90 seconds old | Show uncertainty or refresh. Avoid precise false ETA. |
| Duplicate order submit | Mobile retry after timeout | Idempotency key returns the same order, not a second charge. |

## Think from the contract to the boxes

Search is a discovery view, not inventory authority. Index restaurant location and catalog for fast filtering. Recheck opening state, price and stock at checkout. Persist an order state machine (CREATED → ACCEPTED → PREPARING → PICKED_UP → DELIVERED) and keep payment/courier side effects idempotent. A nearby result is not a confirmed order.

### Follow one order across the boundaries

| Arrow | Commit / acknowledgement meaning | Retry and recovery |
|---|---|---|
| Authenticated shopper → checkout (`order_key`, menu version, items) | Aurora transaction conditionally decrements available stock and creates reservation, order, replay result and outbox. A stale price returns conflict before payment. | Same key + same request returns the stored result. Different request conflicts. |
| Outbox relay → EventBridge → restaurant queue (`order_id`, version) | Database commit accepted the order request. Queue acknowledgement is not restaurant acceptance. | Relay retries. Restaurant transition is conditional on current order version. |
| Payment worker → provider (`payment_intent_id`) | Authorization reserves funds. Capture occurs only after restaurant acceptance. | Reconcile timeout with the same provider key. Do not switch providers while the first outcome is unknown. |
| Restaurant response → order authority | Accept or a two-minute timeout wins one conditional state transition. | Timeout releases stock and queues authorization void. A late capture requires a durable, idempotent refund operation. |

Each worker authenticates with a role limited to its queue and domain records. Shopper identity cannot be taken from the queued body without validating its trusted origin. Keep provider deadlines shorter than the operation deadline and persist uncertainty instead of labelling it failure.

**Freshness budget (exercise target):** change detection 5 s + queue delay 5 s + indexing 15 s + visibility 5 s = **30 s**. If backlog breaks that budget, label discovery stale. Checkout still reads current authority. At 2 million shoppers refreshing once per 30 s, budget roughly **66,667 discovery reads/s**, before bursts.

**Failure trace:** stock/order/outbox commit → relay crashes → shopper retries. Return the original order. Relay later publishes its existing event. Deliver that event twice and timeout the restaurant: assert one stock release and one void/refund intent, not a second order.

**First diagram:** Draw search projection, checkout authority, restaurant acceptance, courier assignment, and customer status as separate boxes.

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon OpenSearch Service** / search index | Filter and rank current restaurant/menu candidates. | Aurora spatial queries at modest data size. |
| **Amazon Location Service** / route and ETA | Estimate routes for locations supplied by the owned restaurant index. It is not the authority for our menus, stock or filters. | Another routing provider. Keep owned catalog search in OpenSearch or Aurora spatial queries. |
| **Amazon Aurora** / order + stock authority | Transactionally validate price, stock and order creation. | DynamoDB conditional item updates for key-oriented inventory. |
| **Amazon EventBridge** / order event routing | Route changes sent by the transactional outbox relay. Routing does not close the database/publish gap. | SNS when simple topic broadcast is enough. |
| **Amazon SQS** / work queue | Buffer assignment/retry work independently. | Step Functions when long-lived workflow state is the main need. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

## Pressure-test the design

**Follow-up: Search can show stale stock. Follow the read projection into checkout and identify the exact point where the last item is reserved.**

**Senior expectation:** A restaurant does not respond before the timeout. Separate payment authorization from capture, define cancellation compensation, and keep customer status honest.

**Staff expectation:** Expand into a new country with different tax, courier and payment providers. Keep domain events stable while assigning regional ownership, compliance, and rollout measures.

**Practice artifact:** Draw search projection, checkout authority, restaurant acceptance, courier assignment, and customer status as separate boxes. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists food-delivery design reports at Uber, Meta and Twilio. The report dates are not shown. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/nearby-restaurants-app/cmacvonzo00r0ad08c9ona48e).

</details>
