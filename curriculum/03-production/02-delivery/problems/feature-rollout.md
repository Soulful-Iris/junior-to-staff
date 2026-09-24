# Feature rollout: the switch that failed after 100%

## What you are building

> Roll out a new invoice-calculation path to a subscription product. The web path looks healthy at 5% exposure, but a daily renewal worker will not execute until midnight. Users must remain in a stable cohort and operators need an immediate way to restore the old compatible behavior.

**Working contract:** Evaluate a versioned flag against a stable subject identity. Exposure is deterministic for a given flag salt and subject. Turning the flag off restores the supported old path; it cannot undo irreversible writes already made by the new path.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100,000 eligible accounts; 5% initial exposure | About 5,000 accounts, with random variation; hash cohorts are not an exact-count allocation. |
| Daily renewal job | A ten-minute observation window cannot reveal a defect in a path that runs once per day. |
| One-minute configuration freshness bound | Record applied version and age; define the fallback when refresh is stale. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/feature_rollout.py
```

[Open the starting code](../../../../examples/architecture-starts/feature_rollout.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| flag_config | flag_id,version,salt,percentage,overrides | Deterministic exposure and explicit emergency control. |
| exposure_event | subject,flag_version,variant,path | Evidence of which behavior actually ran. |
| release_record | code_version,config_version,data_compatibility | Rollback boundary and owner. |

## AWS implementation

![Feature rollout: the switch that failed after 100%: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/feature-rollout.svg)

AppConfig distributes the policy; application code evaluates exposure and preserves compatible behavior. A flag cannot reverse an external charge or repair incompatible stored data.

## Build it in this order

### 1. Keep both paths compatible

Introduce the new code behind a flag while retaining the old reader/writer contract. Inventory web requests, scheduled jobs, retries and admin tools that use the behavior. Record any data change the old code cannot understand before calling the flag a rollback mechanism.

### 2. Assign and record stable cohorts

Hash a stable subject with a fixed flag salt; increasing percentage should include the previous cohort. Record actual exposure at execution time, not only configuration assignment. Keep employee overrides and emergency-off precedence explicit.

### 3. Observe the relevant work cycle

Compare errors, latency and business outcomes for equivalent exposed/control cohorts. Wait through the daily renewal path and representative traffic before widening exposure. Low traffic may require a longer observation window rather than a claim that zero errors proves safety.

### 4. Exercise rollback and cleanup

Turn the flag off and confirm the old path processes records written during exposure. Reconcile external effects that cannot be undone. After adoption, remove dead code and retire the flag under a named owner/date so configurations do not accumulate indefinitely.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Config consumer | Validate snapshots, expose applied version and keep a documented stale-config fallback. |
| Metrics | Record bounded variant/path labels and stable release identity; protect personal cohort identifiers. |
| Rollback | Limit controller permissions to the relevant application/environment; retain the prior valid configuration. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Assignment repeats consistently, a larger rollout retains prior exposure, and 0% disables everyone. |
| Disable after a new-path write | The old path can still read/process the record or the documented repair is required. |
| Observe only daytime traffic | The rollout remains unproven for the midnight renewal path. |

## The next design decision

Let product change the hash salt mid-rollout. Explain cohort churn and experiment contamination, then make salt changes an explicit new experiment rather than a harmless configuration edit.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>

> **Interviewer:** “A new checkout path works in staging. Release it to 5% of customers, then 50%, then everyone. A billing bug appears only after a full day. How do you make activation, observation, and rollback safe?”

**Your contract.** Use a stable customer assignment (not a fresh coin toss per request), a compatible control path during the rollback window, and a meaningful error signal. A percentage rollout alone cannot catch a bug that appears after a daily job runs. This is a constructed exercise.

| Situation | Expected behavior |
|---|---|
| One customer makes 20 requests at 5% | All requests take the same assigned path for this assignment salt |
| Failure starts at 50% | Stop new exposure after propagation; drain/cancel admitted work by contract and repair committed effects |
| Batch job runs 24 hours after 100% | Bake time or delayed gate catches the regression; recovery plan addresses writes already made |
| Control path schema was removed | Toggle cannot restore behavior; migration sequencing must have kept both paths compatible |

![Manual all-at-once activation cannot observe a safe cohort](../../../../assets/design-next/feature-rollout-before.svg)

## Decide what the flag actually protects

Hash `(stable account ID, assignment salt)` into a fixed bucket. **Keep the salt unchanged across 5% → 50% → 100%**; the configuration revision changes the threshold, not the assignment. A new salt means an intentional new experiment. Use the trusted account identity rather than a browser-selected ID; define how account merges move membership. Separate deploying compatible code from activating the behavior. Store a validated configuration version, observe per-cohort error and conversion rates, and rollback on a **guardrail** signal. A flag reversal is not a data rollback: if the new path writes incompatible records, use expand–migrate–contract and a compensating workflow. Account for an alarm with no data before relying on it as a guardrail.

### A cohort you can reproduce

This is a routing bucket, not an authorization or randomness primitive. The
same account and salt map to the same integer on every runtime.

```python
import hashlib
import json

def bucket(account_id: str, assignment_salt: str) -> int:
    payload = json.dumps([account_id, assignment_salt],
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % 10000

accounts = [f"account-{i}" for i in range(1000)]
assigned = {a: bucket(a, "checkout-A") for a in accounts}
cohort_5 = {a for a, value in assigned.items() if value < 500}
cohort_50 = {a for a, value in assigned.items() if value < 5000}
assert cohort_5 and cohort_5 <= cohort_50
assert all(bucket(a, "checkout-A") == assigned[a] for a in accounts)
assert all(0 <= value < 10000 for value in assigned.values())
assert any(bucket(a, "checkout-B") != assigned[a] for a in accounts)
```

A 5% threshold is approximate over a finite population, not a promise of exactly
50 of these 1,000 accounts. Rolling back to 0% changes admission, not bucket
identity or already committed billing effects.

![Named AWS boxes pair a gradual config rollout with independent telemetry](../../../../assets/design-next/feature-rollout-aws.svg)

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| AWS AppConfig (configuration rollout) | Validate, ramp, bake and revert flag versions | Homegrown flag service if targeting rules and audit needs exceed its features, with ownership cost |
| Amazon CloudWatch (metrics and alarms) | Evaluate cohort guardrails and trigger configured rollback | Existing observability platform with reliable cohort-aware telemetry and rollback wiring |
| Amazon ECS (application runtime) | Run both compatible code paths during exposure | AWS Lambda for stateless request processing and existing serverless deployment |
| Amazon RDS for PostgreSQL (relational database) | Keep both data representations compatible during migration | Amazon DynamoDB for a key-oriented model with conditional writes |

AWS AppConfig can roll back on configured CloudWatch alarms during deployment and bake time; it cannot reverse side effects already persisted by customers. Check alarm permissions and a measurable signal before turning on automatic rollback.

![Two timelines distinguish configuration rollback from irreversible data writes](../../../../assets/design-next/feature-rollout-detail.svg)

**Senior follow-up:** The 5% cohort sees an error increase but revenue improves. Define primary and guardrail measures, minimum sample size, and a decision rule rather than “watch the dashboard.”

**Staff follow-up:** Four services read different flag versions during the migration. Define global compatibility, blast-radius boundaries, release ownership, and a reversible migration window that spans both schema and behavior.

**Practice artifact:** Draw control plane, request path, and measurement path. Trace one customer across 5%, 50%, rollback, and next-day batch processing.

**Source boundary:** Original prompt. [AWS AppConfig rollback documentation](https://docs.aws.amazon.com/appconfig/latest/userguide/monitoring-deployments.html) establishes AWS behavior; a [May 2026 Meta ingestion migration](https://engineering.fb.com/2026/05/12/data-infrastructure/migrating-data-ingestion-systems-at-meta-scale/) illustrates why transition and rollback strategies matter, without implying Meta asks this question.

</details>
