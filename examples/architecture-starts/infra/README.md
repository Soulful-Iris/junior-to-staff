# Provision and wire an AWS project foundation

Start with the local command on the project page. When its state transitions are clear, use this foundation for projects that need a durable record, a work queue and private output objects. It creates those resources; it does **not** deploy an API, worker, login system or every service in the project diagram. Keep the local and AWS implementations behind the same application interfaces.

## What the template creates

[Open the CloudFormation template](async-foundation.json).

| Resource | Initial setting | Why it is here |
|---|---|---|
| DynamoDB state table | String `pk` and `sk`; on-demand capacity; point-in-time recovery; optional `expires_at` TTL | Durable job/request records and conditional state changes. Choose keys for the project’s access patterns. |
| SQS work queue | 60-second visibility; four-day retention; encrypted; five receives before redrive | Delivery of accepted work with bounded repeated failures. Tune visibility to the actual worker and renew when necessary. |
| SQS dead-letter queue | Fourteen-day retention; encrypted | Keeps exhausted deliveries available for explicit diagnosis and repair. |
| Private S3 output bucket | Public access blocked; encrypted; incomplete multipart uploads aborted after seven days | Immutable attempt objects or source artifacts, with publication decided in the state table. |

The bucket starts without versioning so the small exercise has straightforward cleanup. Use unique immutable keys such as `attempts/job-7/epoch-2/result.csv`. If the project requires historical object versions, enable versioning deliberately and include all versions/delete markers in its retention and cleanup procedure. Do not apply a blanket expiry rule to objects still referenced by completed jobs.

The queue can redeliver. A visibility setting does not replace idempotency or ownership checks. DynamoDB TTL is eventual cleanup; application code still checks expiry when making an admission, authorization or publication decision.

## Deploy and inspect

Use an AWS CLI profile for a disposable exercise account/environment. The commands create billed AWS resources when you run them; choose the region and retain only the resources your project needs. No AWS deployment was performed as part of this documentation update.

Run from the repository root:

```bash
export AWS_PROFILE=your-exercise-profile
export AWS_REGION=us-east-1
export GUIDE_STACK=architecture-exercise

aws sts get-caller-identity
aws cloudformation deploy \
  --stack-name "$GUIDE_STACK" \
  --template-file examples/architecture-starts/infra/async-foundation.json

aws cloudformation describe-stacks \
  --stack-name "$GUIDE_STACK" \
  --query 'Stacks[0].Outputs' \
  --output table
```

This template creates no IAM roles, so it needs no IAM capability acknowledgement. The deploying identity still needs permission to create the named resources. If creation fails, inspect `aws cloudformation describe-stack-events --stack-name "$GUIDE_STACK"` and the specific failed resource; a deployment command returning does not imply every resource is ready.

Capture outputs for the application adapters:

```bash
export GUIDE_STATE_TABLE=$(aws cloudformation describe-stacks --stack-name "$GUIDE_STACK" --query 'Stacks[0].Outputs[?OutputKey==`StateTableName`].OutputValue' --output text)
export GUIDE_QUEUE_URL=$(aws cloudformation describe-stacks --stack-name "$GUIDE_STACK" --query 'Stacks[0].Outputs[?OutputKey==`WorkQueueUrl`].OutputValue' --output text)
export GUIDE_BUCKET=$(aws cloudformation describe-stacks --stack-name "$GUIDE_STACK" --query 'Stacks[0].Outputs[?OutputKey==`OutputBucketName`].OutputValue' --output text)
```

These variables are configuration, not secrets. Keep credentials in the profile/runtime identity, not in committed application files.

## Wire the application boundaries

| Local interface | AWS adapter | Exact responsibility |
|---|---|---|
| `store.accept(request_id, payload_hash)` | DynamoDB conditional/transactional write | Commit one logical intent and its dispatch record; an exact retry reuses the result. |
| `dispatch.pending()` | Outbox relay calling SQS `SendMessage` | Mark dispatch progress only after accepted publication; a crash can repeat delivery. |
| `store.claim(job_id)` | Conditional epoch/lease update | Allocate current ownership; do not infer ownership from receiving a message. |
| `objects.write(attempt_key, bytes)` | S3 `PutObject` | Upload a complete immutable attempt object; this alone does not make it the visible result. |
| `store.publish(job_id, epoch, pointer)` | Conditional state/pointer update | Require current epoch and source version before making the result visible. |
| `delivery.complete(receipt_handle)` | SQS `DeleteMessage` | Acknowledge after the durable result; duplicate completed jobs can be acknowledged without repeating effects. |

For an HTTP application, add the chosen API/runtime and identity resources from its project page. For a relational project, implement the same transaction boundaries in PostgreSQL rather than forcing its interval joins or relational constraints into this table schema. Search, stream processing, model inference and media conversion also need their own explicitly configured adapters.

A state-key example is `pk=TENANT#acme#JOB#7, sk=STATE`; attempts might use `sk=ATTEMPT#2`. Scope keys to the tenant where required. Keep request identity and job identity distinct when one request creates multiple jobs.

## Scope the runtime roles

| Runtime | Needed access | Access it should not inherit |
|---|---|---|
| API/intent writer | Required item read/write operations on its state table | Output deletion, queue consumption, unrelated tables |
| Outbox relay | Read/update dispatch records; `sqs:SendMessage` on the work queue | Provider credentials or arbitrary bucket access |
| Worker | Receive/delete/change visibility on its queue; required conditional state operations; `s3:PutObject` under its attempt prefix | Public bucket policy changes or unrestricted object deletion |
| Download application | Current authorization lookup and the required object read/signing path | Trust in a client-supplied bucket/key without ownership checks |
| Cleanup operator | Named exercise resources only | Broad deletion rights across the account |

Use the output ARNs when writing policies. DynamoDB transaction authorization depends on the underlying item actions used by the transaction; consult the transaction IAM reference rather than inventing a blanket transaction permission. A runtime in a private subnet also needs an explicit route to each AWS service or external provider it uses, through appropriate endpoints or controlled egress.

For Lambda consuming SQS, configure the event source mapping and partial batch failure behavior deliberately. For ECS, implement bounded long polling and visibility renewal. Both workers still use the job-store publication condition.

## Observe one cloud operation

After implementing the worker adapter, submit one synthetic job under a stable ID, inspect its state, and inspect the output pointer. Stop the worker after upload but before publication; resume it and observe the documented retry behavior. This is direct operation of your application, not a new CI or scheduled check.

Useful inspection commands:

```bash
aws dynamodb describe-table --table-name "$GUIDE_STATE_TABLE"
aws dynamodb describe-continuous-backups --table-name "$GUIDE_STATE_TABLE"
aws sqs get-queue-attributes --queue-url "$GUIDE_QUEUE_URL" --attribute-names All
aws s3api get-public-access-block --bucket "$GUIDE_BUCKET"
```

Queue counters are approximate delivery evidence; inspect the authoritative job record to decide whether a particular job succeeded. Record the exact resource IDs, configured limits and observed outcome in your project handoff.

## Remove the disposable environment

Stop the API/relay/workers first so they cannot recreate work. Confirm that the stack name and bucket belong to this disposable exercise. The following commands permanently remove its objects and resources:

```bash
aws s3 rm "s3://$GUIDE_BUCKET" --recursive
aws cloudformation delete-stack --stack-name "$GUIDE_STACK"
aws cloudformation wait stack-delete-complete --stack-name "$GUIDE_STACK"
```

These cleanup commands match the supplied unversioned bucket. If you enabled versioning, remove the intended object versions and delete markers as well; a recursive removal of current keys is not sufficient. Remove any API, compute, database, log groups or other resources you added outside this foundation through their own IaC stack. Keep the redacted project evidence outside the deleted environment.

## Service references

- [SQS CloudFormation resource](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-sqs-queue.html)
- [SQS visibility and redelivery](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
- [DynamoDB table CloudFormation resource](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-dynamodb-table.html)
- [DynamoDB transaction behavior](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html)
- [IAM for DynamoDB transactions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis-iam.html)
- [S3 bucket CloudFormation resource](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-s3-bucket.html)
- [CloudFormation deploy command](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy.html)
- [CloudFormation delete command](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/delete-stack.html)
