# Build and deploy the AI project workbench

Four finished reference implementations follow this page. Run a complete session locally, inspect its saved state and failures, then use the same request contract on AWS. You build a document assistant, an approval-based support agent, an extraction pipeline, and an evaluation/release registry. Each has its own project page, examples, diagrams, and review conversation.

**Supplied:** runnable Python references, persistent local storage, a Bedrock adapter, an AWS deployment template, fixtures, session runners and boundary tests. **Validation boundary:** local tests, mocked adapters, template validation and a live AWS run are different checks; success in one does not certify another. No live AWS deployment or real-model quality result is claimed here. The deterministic fixture is a test double, not a trained language model.

## Start with one visible result

From the repository root, using Python 3.12 or later:

```bash
python3.12 examples/ai-systems/demo.py assistant
python3.12 examples/ai-systems/demo.py agent
python3.12 examples/ai-systems/demo.py extraction
python3.12 examples/ai-systems/demo.py evaluation
python3.12 -m unittest discover -s examples/ai-systems -p 'test_*.py' -v
```

The core tests use Python's standard library. To also run the mocked AWS persistence and Converse adapter checks, install `examples/ai-systems/requirements-test.txt` and repeat the test command. Mocked service tests verify the adapters; they do not replace a live AWS smoke run.

Each demo creates isolated temporary storage and prints the actual requests followed by actual responses. Repeat without cleanup. Use `--output /tmp/assistant-session.json` to preserve the transcript. The fixed clock in these demos makes approval timestamps reproducible; the application uses the real clock normally.

| Session | What completion looks like | Persisted authority |
|---|---|---|
| Document assistant | Authorized excerpt appears; hidden and revoked documents produce `NO_EVIDENCE` | Document catalog with readers and content version |
| Support agent | `PENDING_APPROVAL`, then one `COMMITTED` receipt; retry returns that same receipt | One order record containing balance and proposal |
| Extraction | One accepted invoice, duplicate reuse, one `REVIEW_REQUIRED` record | Record ID + source hash + validated result |
| Evaluation | Two evaluated releases, promotion, rollback to the earlier release | Immutable reports + conditional active-release pointer |

## Know the names before connecting the boxes

| Name | What it means here | AWS equivalent |
|---|---|---|
| Inference | A request that asks a model to produce a result | Amazon Bedrock Converse |
| Retrieval | Selecting source text that can help answer a question | Local lexical baseline; Bedrock Knowledge Bases or OpenSearch is a later extension |
| Grounding | Connecting displayed claims to actual source evidence | Application validation plus evaluation; no service automatically proves it |
| Conditional write | Save only if the version is still the version you read | DynamoDB condition expression |
| Idempotency | Retrying the same logical operation adds no second committed effect | Stored request ID and conditional state transition |
| Quarantine | A terminal result needing a person to review the data | `REVIEW_REQUIRED` in DynamoDB; distinct from the SQS dead-letter queue |
| Dead-letter queue | Repeated infrastructure or malformed-message failures awaiting operator investigation | Amazon SQS DLQ |
| Release gate | A declared decision rule applied to measured evidence | Python evaluator + immutable S3 report + DynamoDB registry |

## Three environments, one contract

| Mode | Model | Persistence | What it can establish |
|---|---|---|---|
| Local fixture | Deterministic Python responses | SQLite + JSON objects | State transitions, authorization checks, retries, failure handling |
| AWS fixture | Same deterministic responses | DynamoDB + S3, with SQS worker | Your IAM, deployment, queue and storage integration work |
| AWS Bedrock | Your chosen supported model | Same AWS resources | Actual model behavior, measured on your test corpus |

Every AWS box in the project diagrams has its general role beneath its product name. An arrow means a real call or data movement. Dashed or separately labeled diagrams describe the follow-up architecture, not services secretly deployed by the template.

## Run your own requests with durable local state

```bash
cd examples/ai-systems
export AI_STATE=/tmp/ai-workbench
python3.12 app.py fixtures/put-document.json
python3.12 app.py fixtures/ask.json
python3.12 app.py fixtures/extract.json
python3.12 app.py fixtures/get-invoice.json
```

The response to `ask.json` includes `ANSWERED`, `refund-policy`, and the exact excerpt “Refunds are available within 30 days.” The state survives process restarts. `app.py` exits nonzero for invalid requests, conflicts, and model outages in workflows that need a retry. Read-only assistant failures return a visible status with an empty answer.

## Deploy the AWS implementation

Install AWS CLI v2 and AWS SAM CLI using their current official installation instructions. Configure a sandbox AWS profile with permission to create the template's resources. The template creates two Lambda functions, one DynamoDB table, a private S3 bucket, an SQS queue and DLQ, log groups, and a DLQ alarm. There is no public endpoint; invoke it with IAM-authorized AWS CLI or SDK calls.

```bash
cd examples/ai-systems
sam build --template-file template.json
sam deploy --guided
```

Choose a stack name such as `ai-project-workbench`. For the first deployment use `ModelMode=fixture`, `Tenant=team-a`, and `Subject=alice`; leave the model parameters at their defaults. Accept the described IAM role creation. After deployment:

```bash
aws cloudformation describe-stacks --stack-name ai-project-workbench \
  --query 'Stacks[0].Outputs' --output table
```

Copy the `OperatorFunction` output into `AI_FUNCTION`. Then run the cloud session:

```bash
python3.12 -m pip install -r requirements.txt
export AI_FUNCTION='paste-the-OperatorFunction-output-here'
python3.12 cloud_smoke.py assistant --function "$AI_FUNCTION"
python3.12 cloud_smoke.py agent --function "$AI_FUNCTION"
python3.12 cloud_smoke.py extraction --function "$AI_FUNCTION"
python3.12 cloud_smoke.py evaluation --function "$AI_FUNCTION"
```

These are real Lambda invocations and storage writes, even with the fixture model. The smoke runner adds a suffix to record IDs so immutable reports are not overwritten. The small document catalog is capped at 20 entries: use a fresh stack/tenant when repeated smoke runs reach the limit. Cloud sessions use the actual clock; compare stable statuses and amounts rather than expecting identical timestamps and hashes.

**Identity boundary:** the caller is a trusted sandbox operator. `AI_TENANT` and `AI_SUBJECT` are deployment configuration; request payloads cannot replace them. The operator can ingest/revoke documents and approve sandbox refunds. This is not an end-user authorization service. A product API must verify user identity and separate reader, administrator, proposer, and approver capabilities before calling these handlers. The model receives no AWS credentials and has no route to approve an action.

## Connect an actual Bedrock model

Pick an available, Converse-compatible **single-region model** and verify model access in your chosen region. Supply its model ID and exact model ARN as `ModelId` and `ModelResourceArn`. Re-run `sam deploy --guided` with `ModelMode=bedrock`. The template then permits `bedrock:InvokeModel` on that ARN only. Inference profiles need additional destination-model permissions; adapt the policy deliberately if you choose that extension.

The code sends a system instruction and a JSON payload through Converse, limits output to 400 tokens, uses a 20-second read timeout, and disables SDK inference retries. It accepts only JSON and a normal `end_turn` completion; application validators decide whether that JSON is meaningful. No repair loop silently spends more tokens. You can also run the real adapter locally with `AI_MODEL_MODE=bedrock` and `BEDROCK_MODEL_ID` set, after installing `requirements.txt` and configuring AWS credentials.

**Do not expect the fixture's accuracy from a real model.** A model can produce malformed JSON, select irrelevant sources, or misunderstand an invoice. The project pages show the resulting failure states. Structured output is an available optimization for supported models, but field correctness and authorization still need application checks.

## Try the asynchronous extraction path

Copy `JobsQueueUrl` into `AI_QUEUE_URL`, then submit a message:

```bash
export AI_QUEUE_URL='paste-the-JobsQueueUrl-output-here'
aws sqs send-message --queue-url "$AI_QUEUE_URL" \
  --message-body file://fixtures/extract.json
aws lambda invoke --function-name "$AI_FUNCTION" \
  --cli-binary-format raw-in-base64-out \
  --payload file://fixtures/get-invoice.json /tmp/invoice-result.json
cat /tmp/invoice-result.json
```

Immediately querying may return `NOT_FOUND`; query again after the worker has processed the message. The worker accepts only `invoice.extract` and reports failed message IDs. Its structured logs record a hashed message reference, failure category and retry decision. Transient failures retry; malformed jobs and ID conflicts also redrive to the DLQ for operator correction, not silent acknowledgment. The queue visibility timeout is 1,080 seconds against a 180-second Lambda timeout. Three failed receives route a message to the DLQ. A malformed invoice that was successfully processed becomes `REVIEW_REQUIRED` and does not loop through the queue.

## Observe, recover, and remove

- `sam logs --name Operator --stack-name ai-project-workbench --tail` shows handler errors and Bedrock usage metadata. Use `Worker` for extraction categories such as `provider_unavailable`, `id_conflict` and `invalid_input`; terminal `REVIEW_REQUIRED` is not an infrastructure retry. Worker logs omit raw source, exception text and model output. AWS tooling and retained artifacts still need your data retention policy.
- The DLQ alarm enters ALARM when visible failed messages exist. Attach an `AlarmActions` destination for notifications; the supplied alarm has no email subscription.
- For a `Conflict`, reload the authoritative record and make a new decision. Repeating a stale overwrite is not recovery.
- Monitor request failures, model-call duration, usage tokens, queue age, review rate, and rejected approvals. The supplied template creates logs and one DLQ alarm; richer dashboards are a follow-up exercise.
- Token limits and concurrency limits constrain individual work. They do not impose an account-wide dollar cap. Calculate cost from actual token usage, current model prices, retries, and storage; add a shared admission budget before exposing a public service.
- Run `sam delete --stack-name ai-project-workbench` after the lab. The artifact bucket is deliberately **retained**, including versions; explicitly remove the retained data and bucket when you no longer need it. Export your evidence before deleting the table.

## Inspect the actual implementation

The projects share infrastructure adapters so you can follow the state contract across all four workflows. Domain functions remain separately named inside the application.

<details>
<summary>Runtime and local/AWS adapters</summary>

[Application workflows](../../../examples/ai-systems/app.py)

[Persistence adapters](../../../examples/ai-systems/storage.py)

[Fixture and Bedrock models](../../../examples/ai-systems/models.py)

</details>

<details>
<summary>Deployment, test suite, and reproducible sessions</summary>

[AWS SAM template](../../../examples/ai-systems/template.json)

[Boundary tests](../../../examples/ai-systems/test_projects.py)

[Local session runner](../../../examples/ai-systems/demo.py)

[AWS session runner](../../../examples/ai-systems/cloud_smoke.py)

</details>

## Sources and decisions

Reviewed September 23, 2026. AWS documents the [Converse request and response contract](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html), [conditional writes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html), [Lambda/SQS delivery behavior](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html), and [SAM function resources](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-function.html). These establish the service mechanics. The four applications and their bounded contracts are original teaching implementations; the source material does not certify these applications as production deployments.
