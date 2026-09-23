# Approval desk: a support agent that proposes before it acts

## The reviewer's brief

> “Support staff spend time turning customer messages into refund requests. Build an AI assistant that proposes the refund amount, shows the operator exactly what would happen, and records one approved result even if the operator retries. Customers sometimes ask for more than they paid. The model sometimes invents a tool.”

**End product:** a working proposal/approval workflow backed by a durable sandbox refund ledger. It parses customer messages with a model, validates the action in code, persists a proposal, binds approval to its digest, and atomically updates the order and receipt. It does not move real money; adding a payment provider is an explicit follow-up with different failure behavior.

![Expected output with paid amount, pending refund, committed receipt, and repeat approval](../../../../assets/ai-projects/agent-result.svg)

## Define the actual problem

The model is allowed to propose one operation: `refund`. A proposal must contain an integer amount in cents, within 1..100,000, and no more than the remaining paid balance. It expires after 15 minutes. Orders support up to 20 proposal records in this bounded implementation. Separate invocations create and approve a proposal; the model has no path to call the approval handler.

| Case | Exact input or workload | Expected outcome |
|---|---|---|
| Normal proposal | Order paid 5,000 cents; message `Please refund USD 12.50` | `PENDING_APPROVAL`, amount 1,250 cents; balance still unchanged |
| First approval | Operator submits the stored proposal digest before expiry | `COMMITTED`, one receipt, refunded balance becomes 1,250 |
| Retry | Repeat the exact approval request | Same receipt; refunded balance remains 1,250 |
| Changed request | Reuse `ticket-1` with message `Please refund USD 1.00` | Conflict; do not reinterpret an existing request ID |
| Wrong digest | Approve a digest other than the stored proposal's | Reject; no balance change |
| Expiry | Approve at or after the proposal's expiry timestamp | Reject; create a fresh request after review |
| Competing refunds | Two pending 1,250-cent proposals against a 2,000-cent order | First may commit; second fails the fresh balance check |
| Invented capability | Model returns tool `shell` or amount `true` | Reject; only the recognized tool and integer money contract pass |

## Why proposal and execution are separate

A **tool proposal** is untrusted structured data. An **approval** is an operator decision bound to exact data. A **receipt** is evidence of a committed state transition. An attractive explanation from a model is none of these authorities.

The proposal digest covers order ID, request ID, amount, policy version, and expiry. Showing “approve refund” without these values would let the operator approve an ambiguous action. A changed amount requires a new digest and a new review.

![Before immediate execution and repeated balance changes; after bounded proposal, exact approval, atomic receipt](../../../../assets/ai-projects/agent-before.svg)

## Draw the AWS architecture

![AWS CLI operator, Lambda proposal and approval stages, Bedrock, and DynamoDB sandbox state](../../../../assets/ai-projects/agent-aws.svg)

| AWS service / general role | Responsibility | Alternative and why |
|---|---|---|
| Amazon Bedrock / proposal inference | Translate a customer message to candidate tool and amount | Deterministic form entry is better when the message already has structured fields |
| AWS Lambda / application policy and action handler | Validate tool, money, proposal expiry, digest, and balance | ECS when integrating long-lived agent sessions or streaming tools |
| Amazon DynamoDB / order and approval state | One conditional write commits sandbox balance and receipt together | Aurora transaction if real order state already lives in SQL |
| AWS IAM / operator invocation boundary | Only authorized sandbox operators invoke the Lambda | Cognito/OIDC plus application roles for a real user-facing product |
| AWS Step Functions Standard / durable workflow | **Extension** for timers, multi-stage human approval, and reconciliation | Keep direct state transitions for this bounded two-stage flow |

## Implement the whole workflow

1. **Create the sandbox order.** Store `paid_cents`, zero refunded balance, and an empty proposal collection. An existing order ID cannot be overwritten by another create.
2. **Handle request identity.** A repeat request ID with the same message returns the saved proposal. The same ID with a changed message conflicts.
3. **Ask the model.** Request JSON with tool and amount. It receives the customer message but no AWS credential, arbitrary tool registry, or approval capability.
4. **Apply policy.** Reject unknown tools, floats, booleans masquerading as integers, nonpositive amounts, and amounts beyond the order balance.
5. **Save for review.** Persist the exact action, policy version, expiry and digest. No ledger effect happens yet.
6. **Approve separately.** The operator submits order ID, request ID and digest. The handler rereads state, verifies expiry and current balance, then conditionally writes the new balance and receipt.
7. **Recover a lost response.** Retry the same approval. If it already committed, return its existing receipt. If a competing write caused a conflict, reload and re-evaluate.

![Animated flow from customer message through proposal and human review to conditional commit](../../../../assets/ai-projects/agent-flow.svg)

```python
if proposal["status"] == "COMMITTED":
    return proposal  # The prior receipt is the retry result.
if now >= proposal["expires_at"]:
    raise Invalid("proposal expired")
```

The actual handler checks the digest before this branch and current balance before committing. Read `agent_propose` and `agent_approve` in the supplied application to follow the complete order of checks.

## Run it

```bash
python3.12 examples/ai-systems/demo.py agent
```

The session creates a USD 50.00 order, proposes USD 12.50, approves, and repeats approval. Compare the two `receipt` fields: they must match. Inspect the tests for expiry, stale writes, changed message IDs, competing proposals, and invented tools. On AWS run `cloud_smoke.py agent --function "$AI_FUNCTION"` from the workbench directory.

![Proposal lifecycle with pending approval and explicit rejection paths](../../../../assets/ai-projects/agent-state.svg)

## Follow-up: connect a real payment provider

The sandbox's balance and receipt fit in one database update. A remote payment call cannot join that transaction. If the provider charges/refunds and the response is lost, a local timeout does not mean the payment failed.

![The sandbox's one conditional write and the extra guarantee needed for external payments](../../../../assets/ai-projects/agent-mechanism.svg)

**Senior follow-up:** add `APPROVED → SUBMITTED → CONFIRMED / UNKNOWN` states. Persist a stable provider idempotency key before submission. On timeout, query/reconcile that key; do not generate a fresh refund ID. Record the provider receipt separately from the model proposal.

**Staff follow-up:** add independent approver roles, limits by region, policy version migrations, and emergency revocation. The same person may not be allowed to propose and approve. Split handlers and IAM permissions or add a verified application authorization service; the current sandbox operator has both capabilities by design.

## Engineer FAQs

**Is the digest a password?** No. It identifies the reviewed action. An attacker with approval authority and the digest could still approve; authentication and authorization remain separate requirements.

**Why store expiry instead of just a DynamoDB TTL?** TTL deletion is asynchronous. The application must compare the deadline when approving. A retained expired record also explains why an old request was rejected.

**Can the model approve its own proposal?** The supplied model adapter only returns JSON. It has no tool execution loop, network credentials, or route to invoke `agent.approve`.

**Why integer cents?** Decimal currency should not depend on binary floating-point arithmetic. Currency scale and supported currencies must be part of the contract; this project supports USD only.

**What does “once” actually mean?** At most one committed sandbox ledger effect for this request, because the receipt and amount are one conditional record update. Model inference may repeat after an interrupted proposal attempt. A real provider needs its own idempotency contract.

**Would Step Functions remove the need for request IDs?** No. Workflow durability and remote side-effect idempotency solve different problems. Human callbacks also need expiry and a secure mechanism for resolving the correct pending action.

**What happens if two operators approve together?** One conditional write succeeds. The other gets a conflict, reloads state, and can retrieve the same receipt. Blindly retrying the stale write is incorrect.

## What you are expected to hand over

Bring a pending proposal with the exact amount, a committed receipt, a duplicate approval trace, and the competing-refund test. Include the difference between sandbox atomicity and external-provider reconciliation, plus the IAM/application role split for a product deployment.

### How the review conversation gets harder

| Review gate | Changed requirement | Evidence to bring |
|---|---|---|
| Baseline | USD 12.50 refund on a USD 50 order | Proposal, approval, one receipt |
| Failure | Reply to approval is lost | Retry returns the saved receipt |
| Senior | Payment provider accepts then times out | `UNKNOWN` state, stable key and reconciliation |
| Staff | Requester cannot also approve | Separate verified capabilities and auditable decision |
| Evidence | Model proposes a shell command | Recognized-tool validation rejects it before effects |
| Handoff | Original operator is unavailable | Durable pending action, expiry rules and recovery instructions |

## Research behind the design

Reviewed September 23, 2026. The [AWS human approval tutorial](https://docs.aws.amazon.com/step-functions/latest/dg/tutorial-human-approval.html) demonstrates a paused workflow and an external approval. [Conditional writes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html) supply the version guard used here. Amazon's [February 2026 agent evaluation report](https://aws.amazon.com/blogs/machine-learning/evaluating-ai-agents-real-world-lessons-from-building-agentic-systems-at-amazon/) discusses evaluating tool choice and recovery as well as final answers. The sandbox ledger and its exact policy limits are original reference code.
