# 4. Shedding the right thing

## What you are building

> Add overload admission to a reading-list API. Interactive saves matter more than bulk exports, but total capacity is only 100 equal-cost requests/s. Later, critical traffic alone reaches 120/s, so priority cannot make every request succeed.

**Working contract:** Keep resource usage bounded and allocate capacity by trusted work class. Admit only work that can fit a finite deadline. Rejection is explicit and measured, including when critical demand exceeds physical capacity.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 80 critical + 50 bulk requests/s; capacity 100/s | Admit all 80 critical and at most 20 bulk; reject at least 30 bulk/s. |
| 120 critical requests/s; capacity 100/s | At least 20 critical/s must be rejected or wait within a stated finite budget. |
| One export costs 100 saves | Request-count fairness is misleading; budget the constrained resource cost. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/04_shedding_the_right_thing.py
```

[Open the starting code](../../../../examples/architecture-starts/04_shedding_the_right_thing.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| work_class | route,tenant_tier,cost_weight | Trusted classification and estimated dependency cost. |
| admission_state | active,queued,deadline,budget | Bounded resource allocation. |
| outcome | class,admitted,rejected,expired,completed | User-visible accounting and fairness evidence. |

## AWS implementation

![4. Shedding the right thing: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/04-shedding-the-right-thing.svg)

The constrained database determines useful capacity. Separate bulk delivery allows deferral, while early admission protects interactive work without pretending priority creates resources.

## Build it in this order

### 1. Place admission before expensive work

Classify by authenticated account and route, not a client-controlled priority header. Check budget before taking database connections or starting external effects. Return a documented 429/503 and bounded Retry-After when work cannot be admitted.

### 2. Reserve and lend capacity explicitly

Give interactive saves a reserved share and allow bulk work to borrow spare capacity under a revocable bound. Preserve per-tenant fairness within each class. An unlimited paid tier is not a capacity policy.

### 3. Use weighted cost when needed

Measure database/CPU work per operation and choose approximate cost units. Bound both concurrency and rate where their effects differ. Revisit weights when exports become more expensive; one request counter cannot represent every workload.

### 4. Recover gradually

Expire waiting work that missed its useful deadline and ramp bulk admission after critical queues recover. Show class-specific useful completions and rejection, so a fast rejection response is not mistaken for improved successful latency.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Pools | Account for API and worker connections together; keep a hard total dependency budget. |
| Queues | Fixed depth/age bounds and explicit expiry behavior; do not hide interactive requests in an unbounded queue. |
| Policy | Version class weights and reserve settings; inspect the resulting allocation before increasing limits. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The first case rejects 30 bulk/s; the second rejects 20 critical/s. |
| Make exports 100 times more expensive | Weighted admission reduces their share appropriately. |
| Remove overload | Bulk traffic returns gradually after critical waiting clears. |

## The next design decision

An accepted bulk job represents a paid obligation. Distinguish admission rejection from cancellation of already accepted work, and preserve status/refund or rescheduling semantics.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · Critical traffic exceeds capacity

**Changed requirement:** All 120 requests/s are critical. How does the design remain live? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Reserve a bounded critical queue only if the latency budget allows it, then shed excess. Record denied critical work explicitly; inspect absolute arrival/capacity evidence before blaming classification.

</details>

## Follow-up 2 · Work costs differ

**Changed requirement:** An export takes 100 times the database work of a save. Are request-count limits enough? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use separate concurrency/work budgets and per-tenant fairness. The shared database budget constrains all classes; protect control and recovery operations too.

</details>

## Supplied mechanism practice

- [Runnable reliability arithmetic and incident lab](../labs/reliability/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
