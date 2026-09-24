# Run the reading-list API and choose an exercise

This is a small HTTP service you can run, call and change. Alice and Bob belong to one study group. They save documentation links to a shared list, edit their own notes and keep separate reading status. Saving a URL succeeds even when its title lookup times out.

The server uses Python's standard library and a SQLite file. It provides a concrete starting application for the backend, frontend and reading-list exercises. It is not the completed five-stage project: there is no browser UI, production login, request tracing, durable worker, cloud adapter or deployment configuration.

## Download the repository once

Install Python 3.12+ and Git. The request examples also use `curl`. No package installation or AWS account is needed.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 --version
```

Already have a checkout? Open a terminal in that checkout instead of cloning again. Commands throughout the projects assume this directory. Browse [the repository](https://github.com/Soulful-Iris/junior-to-staff) or [this application's source on GitHub](https://github.com/Soulful-Iris/junior-to-staff/tree/main/examples/reading-list-starter).

## Start the API in terminal 1

```bash
python3 examples/reading-list-starter/app.py --db /tmp/reading-list.sqlite3 --port 8080
```

Leave it running. It prints its address and database path. Stop with Ctrl+C. Restarting with the same path preserves saved bookmarks. Use a different database filename for a fresh exercise. If port 8080 is busy, pass `--port 8081` and change the request URLs below.

## Save and read a bookmark in terminal 2

```bash
curl -i http://127.0.0.1:8080/bookmarks \
  -H 'X-Demo-User: alice' -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/docs","title_mode":"timeout"}'

curl -s http://127.0.0.1:8080/bookmarks -H 'X-Demo-User: alice'
```

The first request returns **201**, an integer `id`, `title: null`, `title_status: "timeout"` and `version: 1`. The second returns that saved URL in `items`. The controlled timeout lasts about half a second. Use `"title_mode":"ok"` for a title of `"Example documentation"`. The fixture makes **no outbound HTTP request**. The submitted URL is stored as data.

Use the returned ID in the following commands. `1` assumes a new database:

```bash
curl -s -X PATCH http://127.0.0.1:8080/bookmarks/1 \
  -H 'X-Demo-User: alice' -H 'Content-Type: application/json' \
  -d '{"version":1,"note":"Read the storage section"}'

curl -s -X PATCH http://127.0.0.1:8080/bookmarks/1/read \
  -H 'X-Demo-User: bob' -H 'Content-Type: application/json' \
  -d '{"is_read":true}'
```

The edit returns `version: 2`. Repeating it with version 1 returns **409**. Bob can read the group's links and change his own reading status. Editing Alice's note as Bob returns **404**. Missing or unknown demo identity returns **401**. No delete, tags, pagination or individual `GET /bookmarks/{id}` endpoint is supplied.

## Find the code you will change

Read [app.py](app.py). These names exist in that file:

| Function or class | Supplied behavior | Typical exercise change |
|---|---|---|
| `Handler.dispatch()` | Routes HTTP requests and checks demo membership | Add request context, safe diagnostics and response IDs. |
| `Handler.reply()` | Writes JSON and status | Add the request ID header and a consistent error envelope. |
| `connect()` and `initialize()` | SQLite connection and tables | Introduce a repository interface before changing storage. |
| `lookup_title()` | Deterministic success or timeout fixture | Add a bounded public-URL fetcher, or move work into a durable queue. |
| Save transaction in `dispatch()` | Commits URL before title enrichment | Persist job intent in the same transaction for the durable-jobs exercise. |
| Conditional note update | Owner and version condition | Build a UI that preserves a draft after a 409 response. |

`X-Demo-User` is an explicit local shortcut, not authentication. Anyone who can call this server can select Alice or Bob. Keep it on loopback. A deployed version needs verified identity and a membership model. Do not expose this teaching server to the internet.

## How this code connects to AWS

**Nothing in this directory deploys or calls AWS.** The diagrams in the project pages describe the target after you build adapters. You keep the business rules but replace the process, identity and storage boundaries deliberately.

| Local component | Example AWS destination | Work you must do |
|---|---|---|
| `BaseHTTPRequestHandler` routes | API Gateway and a Lambda handler, or an ALB and a container | Translate the incoming event into application arguments. Package the handler or container. The Python HTTP handler is not a Lambda handler. |
| `X-Demo-User` | Cognito or another trusted identity provider | Validate issuer, audience and token lifetime. Map the subject to group membership. Never trust the demo header. |
| SQLite transactions | RDS PostgreSQL **or** a redesigned DynamoDB model | Write and exercise a storage adapter. SQLite SQL does not run unchanged on DynamoDB. Preserve owner/version conditions and atomic job intent. |
| In-process title lookup | SQS plus a separately deployed worker | Add an outbox, duplicate handling, leases and durable status. Queue creation alone does not provide these behaviors. |
| Local structured events you add | CloudWatch Logs | Configure log delivery, retention and scoped access. Keep request/job identity in the event schema. |

First complete the local assignment and record its visible result. Then use that page's AWS mapping and configuration as a separate extension. The [optional AWS foundation](../architecture-starts/infra/README.md) provisions only its documented resources. It does not deploy this API or connect it to a database.
