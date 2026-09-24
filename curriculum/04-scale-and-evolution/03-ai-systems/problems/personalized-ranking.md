# Personalized ranking: low latency and evidence of quality

## What you are building

> Build product recommendations for a storefront. The ranking model scores 200 candidates, but a feature service sometimes stalls for 170 ms. Restricted or out-of-stock items must remain excluded even when the service falls back to a popular-items list.

**Working contract:** Return eligible ranked items within a 250 ms p95 budget. Personalized scoring is optional under deadline pressure; authorization and availability filtering are mandatory for every path, including cached fallback.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 40,000 requests/s × 200 candidates | Eight million candidate scores/s before feature retrieval and batching. |
| 250 ms p95 response budget | Example: 30 ms candidates, 50 ms features, 80 ms inference, 20 ms eligibility, 30 ms transport, 40 ms reserve. |
| Feature freshness target: two seconds | Store observation time and define which stale features may be omitted versus which require rejection. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/personalized_ranking.py
```

[Open the starting code](../../../../examples/architecture-starts/personalized_ranking.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| candidate_set | request_id,item_ids,source_version | Bounded retrieval output before ranking. |
| feature_vector | entity,feature_version,observed_at | Typed features with freshness evidence. |
| ranking_run | model_version,feature_version,fallback_reason | Reproducible scoring mode and deadline outcome. |

## AWS implementation

![Personalized ranking: low latency and evidence of quality: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/personalized-ranking.svg)

The inference endpoint ranks candidates; the application owns deadlines and eligibility. Keeping a useful baseline makes feature/inference outages an explicit product behavior instead of a hidden timeout.

## Build it in this order

### 1. Build an eligible baseline

Retrieve a bounded candidate list and return a deterministic popular/recent ordering after current eligibility checks. Measure that baseline’s latency and usefulness. Keep the same eligibility module for personalized and fallback paths.

### 2. Version feature and model contracts

Define feature names, types, defaults, observation times and training/serving transformations. Record model and feature schema versions together. Missing data is not automatically zero; choose a documented default or omit personalization.

### 3. Spend one shared deadline

Pass remaining time to feature retrieval and inference. If the feature path consumes 170 ms, skip expensive scoring when the response reserve is insufficient. Cancel work that no longer contributes to a response and record the fallback reason without making the user wait for a doomed model call.

### 4. Evaluate the served system

Compare engagement or task success with guardrails for eligibility, latency and cohort effects. Record actual served model/feature versions and fallback frequency. Offline ranking quality alone cannot reveal how often production users receive the fallback.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Inference | Pin model artifact/version and bound endpoint concurrency; retain a measured non-model fallback. |
| Feature cache | Timestamp every value, cap staleness per feature and include schema version in keys. |
| Feedback | Join impressions to outcomes with stable IDs; record actual exposure rather than intended assignment. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | A 170 ms feature delay triggers fallback, and ineligible item a is still excluded. |
| Serve stale features | The chosen feature policy is applied and recorded. |
| Roll back the model | The feature schema remains compatible with the restored model. |

## The next design decision

Run 10,000 model variants. Estimate artifact, feature and observation cardinality, then choose whether all variants deserve live infrastructure or whether most can be evaluated offline first.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



Assume 40,000 peak recommendation requests/s, two-second fresh interaction signals, and 10,000 simultaneous experiment variants/segments as an intentionally extreme follow-up. A plausible rank score is not evidence that the system is safe or helpful.

| Case | Required result |
|---|---|
| Blocked author appears among candidates | Filter before response; cached scores do not grant permission |
| Feature store times out at 170 ms | Fall back to an eligible non-personalized list within deadline |
| Model scores differ offline and online | Detect feature/version skew; canary gate stops wider release |
| Variant improves clicks but raises complaints | Do not use click-through alone as release criterion |

## Decide what can fail independently

Candidate retrieval, current eligibility/ownership, feature lookup, ranking, and final filters have separate responsibilities. Allocate an end-to-end latency budget including network, P95 feature fetch, inference, and serialization, with room for variance; 250 ms is a request deadline, not five separate 250-ms allowances. Version both model and features, propagate experiment assignment deterministically, log exposure only after an item was actually shown. Preserve a safe default path when ranking is unavailable.

The allocation adds to 250 ms. If the feature call needs 170 instead of its allotted 100 ms, the whole path overruns unless a timeout triggers fallback early. The chart's 20 ms slack is a teaching budget, not a guarantee that independent P95 stages combine into a P95 request.

## Put the AWS names on the boxes

**Why these boxes, and what changes the choice:** SageMaker endpoints serve a managed ranker; ECS inference fits a lighter model with existing deployment tooling. DynamoDB serves versioned online features. ECS enforces final eligibility and fallback; CloudWatch observes latency and denial outcomes, not model quality by itself.



**Senior follow-up:** A rollout raises average CTR 3% while a small language cohort experiences a 20% complaint rise. Define evaluation slices, minimum sample size, rollback signals, and an owner for the trade-off. Explain why the offline metric cannot substitute for an online guardrail.

**Staff follow-up:** A privacy deletion crosses online features, training sets, caches, exposure logs, and models. Set retention and retraining policy, ownership, an audit trail, and a response contract while deletion propagates. Separate serving reliability from experimentation governance.

**Practice artifact:** Separate online serving and offline evaluation diagrams, latency budget, stale-block test, and go/no-go release memo.

**AWS translation:** S3 + batch/stream processing for training data, an explicitly versioned low-latency feature store, ECS/SageMaker endpoint as suits workload, CloudWatch for p95 and fallback rates. IAM boundaries and product eligibility checks address different risks. [Spotify's January 2026 engineering article](https://engineering.atspotify.com/2026/1/why-we-use-separate-tech-stacks-for-personalization-and-experimentation) discusses keeping personalization serving and experimentation distinct; exercise numbers are original.

</details>
