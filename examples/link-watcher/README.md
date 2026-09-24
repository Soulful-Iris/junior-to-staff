# Link-watcher local reference

Start with the [Build a link monitor with durable history and change alerts](../../curriculum/02-applications/01-backend/projects/a-link-rot-watcher.md).
This directory supplies the first two checkpoints: a durable state machine and a
controlled HTTP check. The guide specifies the scheduler, distributed workers,
notification delivery, and monitoring that you add next.

Python 3.12+; standard library only. Run from the repository root:

```bash
python3 examples/link-watcher/watcher.py --db /tmp/link-watcher-demo.sqlite3 demo
```

The demo records four observations and two notification intents in SQLite.
Rerunning it against the same database leaves the counts unchanged. It does not
send email. `outbox` is the list of notifications waiting to be delivered.

For live HTTP checks, start the supplied origin in a separate terminal:

```bash
cd examples/link-watcher
python3 fixture_server.py
```

Then follow checkpoint 2 in the guide. The HTTP adapter is deliberately restricted
to this loopback server. It disables redirects and proxies, caps the response at
64 KiB, and uses a two-second socket timeout. A socket timeout is **not** a total
wall-clock deadline against a server that slowly trickles bytes; the cloud fetcher
must enforce a total deadline and public-address policy before internet use.

| File | Responsibility |
|---|---|
| `watcher.py` | `classify` interprets responses; `record` commits observations, current state, transitions and pending notifications atomically; CLI prints durable state. |
| `fixture_server.py` | Reads `state.json` on each request, letting you reproduce status changes, content changes, throttling and delay. |
| `infra-foundation.json` | Deployable CloudFormation storage, queues and alarm foundation. **No application workers or scheduler are included.** |

The database and fixture-state files are ignored by git. Use a different database
filename for an independent experiment; keep the same filename to test restarts.

## Infrastructure foundation

The template creates encrypted SQS work/dead-letter queues, a DynamoDB table with
point-in-time recovery and TTL cleanup, and a dead-letter alarm. Supply an existing
SNS topic ARN for alarm actions. It creates no subscriptions or email identities.
The guide defines the worker code, IAM policies and event-source wiring to add.

```bash
aws cloudformation validate-template --template-body file://examples/link-watcher/infra-foundation.json
aws cloudformation deploy --template-file examples/link-watcher/infra-foundation.json \
  --stack-name learning-link-watcher \
  --parameter-overrides AlertTopicArn="$ALERT_TOPIC_ARN"
aws cloudformation describe-stacks --stack-name learning-link-watcher --query 'Stacks[0].Outputs'
# After the exercise, delete these disposable resources and their practice data:
aws cloudformation delete-stack --stack-name learning-link-watcher
aws cloudformation wait stack-delete-complete --stack-name learning-link-watcher
```

Set `ALERT_TOPIC_ARN` in your own sandbox account before deployment. This foundation
is a starting implementation exercise, not a deployed or fully connected watcher.
