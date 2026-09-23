# Food delivery: quote the right nearby options

> **Interviewer:** “Customers search nearby restaurants, place an order, and track delivery. Restaurants change hours and menus; couriers move; inventory can sell out between browse and checkout. Design the customer path.”

This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 200,000 restaurants, 2 million concurrent shoppers during dinner, and availability freshness within 30 seconds. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Nearby search | Cuisine + 3 km radius | Return open restaurants whose location and filters match. |
| Menu race | Last item sells after browse | Reject or substitute before payment capture; explain the reservation rule. |
| Courier GPS stale | Last update 90 seconds old | Show uncertainty or refresh; avoid precise false ETA. |
| Duplicate order submit | Mobile retry after timeout | Idempotency key returns the same order, not a second charge. |

![The failure path and repaired design for Food delivery](../../../../assets/design-interview/food-delivery-marketplace-before.svg)

## Think from the contract to the boxes

Search is a discovery view, not inventory authority. Index restaurant location and catalog for fast filtering; recheck opening state, price and stock at checkout. Persist an order state machine (CREATED → ACCEPTED → PREPARING → PICKED_UP → DELIVERED) and keep payment/courier side effects idempotent. A nearby result is not a confirmed order.

**First diagram:** Draw search projection, checkout authority, restaurant acceptance, courier assignment, and customer status as separate boxes.

![AWS services named with their provider-neutral architectural roles](../../../../assets/design-interview/food-delivery-marketplace-aws.svg)

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon OpenSearch Service** / search index | Filter and rank current restaurant/menu candidates. | Aurora spatial queries at modest data size. |
| **Amazon Location Service** / nearby geometry | Find restaurants and estimate route distance. | OpenSearch geo queries for combined custom filters. |
| **Amazon Aurora** / order + stock authority | Transactionally validate price, stock and order creation. | DynamoDB conditional item updates for key-oriented inventory. |
| **Amazon EventBridge** / order event routing | Fan out accepted order changes to restaurant and courier workflows. | SNS when simple topic broadcast is enough. |
| **Amazon SQS** / work queue | Buffer assignment/retry work independently. | Step Functions when long-lived workflow state is the main need. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

![A focused failure, capacity, or state diagram for Food delivery](../../../../assets/design-interview/food-delivery-marketplace-deep.svg)

## Pressure-test the design

**Follow-up: Search can show stale stock. Follow the read projection into checkout and identify the exact point where the last item is reserved.**

**Senior expectation:** A restaurant does not respond before the timeout. Separate payment authorization from capture, define cancellation compensation, and keep customer status honest.

**Staff expectation:** Expand into a new country with different tax, courier and payment providers. Keep domain events stable while assigning regional ownership, compliance, and rollout measures.

**Practice artifact:** Draw search projection, checkout authority, restaurant acceptance, courier assignment, and customer status as separate boxes. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists food-delivery design reports at Uber, Meta and Twilio; the report dates are not shown. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/nearby-restaurants-app/cmacvonzo00r0ad08c9ona48e).
