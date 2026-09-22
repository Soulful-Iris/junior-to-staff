# AWS · translate a mechanism into infrastructure

AWS is the implementation platform for this path. It is not a claim that all interviewers expect AWS product names. Explain the vendor-neutral requirement, then choose a service and show its operational consequences.

## Service decisions

| Need | Candidate AWS services | Decision to explain | Implementation proof |
|---|---|---|---|
| Short request handlers | API Gateway + Lambda | Burst behavior, duration, cold start, dependency connections | Request validation, deadline, version conflict |
| Long-lived/container work | ALB + ECS/Fargate | Process lifecycle, load balancing, task count, graceful drain | Health check and shutdown without losing work |
| Static frontend and objects | S3 + CloudFront | Cache policy, private access, invalidation, byte transfer | Upload directly; verify permissions and expiry |
| Relational data | RDS/Aurora | Transactions, joins, indexes, connection budget | Query plan and concurrent-write test |
| Key-based access | DynamoDB | Partition key, hot keys, conditional writes, read consistency | Atomic create and duplicate rejection |
| Independent jobs | SQS standard + Lambda/ECS | At-least-once delivery, visibility, partial failure, DLQ | Retry after lost acknowledgement |
| Ordered groups | SQS FIFO | Ordering scope, message groups, retries and deduplication scope | One slow group does not block unrelated groups |
| Routing/fan-out | EventBridge / SNS | Event filtering and subscribers versus durable processing state | Failed subscriber and retry contract |
| Repeated low-latency reads | ElastiCache | Freshness, eviction, outage fallback, hot-key behavior | Stampede and outage test |
| Identity and permissions | Cognito + IAM | User authentication versus service privileges and object authorization | Cross-tenant denial and least-privilege role |
| Operations | CloudWatch / tracing | User outcomes, queue age, cost/cardinality | Alarm threshold and trace showing a slow dependency |

## Local-first progression and optional infrastructure

| Lab | Implement | Level extension |
|---|---|---|
| [0 · Application contract boundary](labs/api-contract/README.md) | Local request/response validators and malformed-200 tests | Senior: actual validation boundary; lead: compatible rollout and service lifecycle |
| [1 · Conditional data writes](lab-1-data.md) | A DynamoDB table, atomic first write, duplicate and conflict behavior | Junior: explain keys; senior: model access patterns; staff: tenant partition policy |
| [2 · Direct object upload](lab-2-upload.md) | Private S3 object upload through a short-lived capability | Junior: byte flow; senior: finalization/versioning; staff: retention and regional strategy |
| [3 · Durable queued work](labs/job-pipeline/README.md) | SAM template, SQS, Lambda worker, DynamoDB results, alarms, DLQ | Junior: follow one job; senior: inject duplicates; staff: quotas and replay governance |
| [4 · Recovery beyond one result](../architecture/labs/recovery-migration/README.md) | Local leases/fencing, provider uncertainty, outbox, replay and migration | Senior: failure schedules; lead: rebalance, region loss and rollback |

For relational practice use the [PostgreSQL lab](../architecture/labs/postgresql/README.md).
For cache/outage and warm-link authorization use the
[cache and revocation tests](../architecture/labs/cache-consistency/README.md).

Labs 1 and 2 are command-driven exercises with small scripts. Lab 3 includes executable infrastructure and unit tests. Deploy to your own disposable learning account/stack only when ready; these steps create billable resources. No resources were deployed while preparing this branch. Choose your region and verify current pricing/quotas. The examples avoid hard-coded account IDs and never require committing credentials.

## Primary documentation, checked 2026-09-22

- [DynamoDB conditional expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)
- [DynamoDB transactions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html)
- [Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
- [SQS partial-batch responses](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)
- [SAM SQS event properties](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-sqs.html)
- [S3 presigned uploads](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)

These live technical references may predate the research window. They establish service behavior, not recent interview frequency.

REST API Gateway basic validation covers configured **requests**; response
models alone do not enforce backend response-body schemas. The local contract
lab shows application response validation and records API flavor, media-type,
and parameter-format limits. As checked 2026-09-22, [App Mesh support ends
September 30, 2026](https://docs.aws.amazon.com/app-mesh/latest/userguide/what-is-app-mesh.html).
Treat App Mesh as retirement scope; evaluate supported alternatives against
their actual features and keep deadlines, retries, and validation explicit.

[Architecture](../architecture/concepts.md) · [Interview home](../README.md)

## Learn from actual incidents

The [production casebook](../production/README.md) maps five recent incidents to AWS implementation exercises: configuration rollout, retry budgets, deployment headroom, stale status projections, and hot partitions.
