# Feature rollout: the switch that failed after 100%

> **Interviewer:** “A new checkout path works in staging. Release it to 5% of customers, then 50%, then everyone. A billing bug appears only after a full day. How do you make activation, observation, and rollback safe?”

**Your contract.** Use a stable customer assignment (not a fresh coin toss per request), a reversible old path, and a meaningful error signal. A percentage rollout alone cannot catch a bug that appears after a daily job runs. This is a constructed exercise.

| Situation | Expected behavior |
|---|---|
| One customer makes 20 requests at 5% | All requests take the same assigned path for this version |
| Failure starts at 50% | Stop expansion and revert flag; confirm affected requests drain |
| Batch job runs 24 hours after 100% | Bake time or delayed gate catches the regression; recovery plan addresses writes already made |
| Control path schema was removed | Toggle cannot restore behavior; migration sequencing must have kept both paths compatible |

![Manual all-at-once activation cannot observe a safe cohort](../../../../assets/design-next/feature-rollout-before.svg)

## Decide what the flag actually protects

Hash `(stable account ID, experiment/flag version)` to keep assignment stable; specify what happens when customer membership changes. Separate deploying compatible code from activating the behavior. Store a validated configuration version, observe per-cohort error and conversion rates, and rollback on a **guardrail** signal. A flag reversal is not a data rollback: if the new path writes incompatible records, use expand–migrate–contract and a compensating workflow. Account for an alarm with no data before relying on it as a guardrail.

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
