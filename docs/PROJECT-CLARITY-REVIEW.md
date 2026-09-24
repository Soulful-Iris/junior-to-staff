# Project clarity: feedback, changes and reader walkthrough

## Feedback being addressed

The reader could not tell what application the exercise described, what to build, which code already existed, where to find it, or how a local Python example related to the AWS diagram. Project and chapter names did not reliably describe the skill. Adding more engineering detail had not fixed the reading order.

Scope: all 90 engineering project/design briefs: 41 design problems, 34 application/operations projects including the approved link watcher, ten AI-assisted/change-workflow projects, and five continuing reading-list stages. The 18 chapter titles and incoming navigation labels were updated without changing published page paths.

## The new reading order

1. Application background: product, users and normal input/output behavior.
2. Your assignment: named deliverable and required behavior.
3. Code access: repository link, prerequisites, command, example output and explicit supplied/missing behavior.
4. Local implementation: working directory, records/interfaces and ordered changes.
5. Completion: a successful operation, a failure and observable state or decision.
6. Capacity: constructed workload assumptions after the basic application is understood.
7. AWS: proposed deployment, local-to-service mapping, adapter work, provisioning and cleanup.
8. Extensions: changed requirements after the baseline works.

Workflow/decision projects explicitly name their document or comparison as the deliverable. They do not imply that every exercise requires an AWS deployment. The approved watcher retains its local and cloud checkpoints.

## Simulated junior reader: no previous conversation

This is an editorial walkthrough performed during the revision, not a claim that external engineers reviewed the course.

| Reader question | Where the answer now lives | Gap found and corrected |
|---|---|---|
| What does this application do? | Application background on every brief | Added a product/user journey before the incident or assignment. |
| What am I handing over? | The Deliver sentence and completion section | Distinguished applications, mechanisms, operational procedures and decision reports. |
| Where is the code? | Early GitHub source links, clone command and downloadable source | The site previously replaced source links with text. Downloads now remain visible alongside inline source. |
| Why does running the script not start an API? | Explicit mechanism-demo description | Separated 75 small demonstrations from four local AI workflows and the full link-monitor CLI. |
| What is app.py, and where do I edit it? | New reading-list starter and its function map | Added an actual standard-library HTTP/SQLite application and pointed tracing instructions to Handler.dispatch, Handler.reply and lookup_title. |
| What should I see first? | Captured demo output and HTTP request walkthrough | Added save/list/edit/read examples, expected status codes and title timeout behavior. |
| Is trace_request.py already supplied? | Tracing implementation step 3 | Explicitly made the support CLI a deliverable with its intended arguments. |
| Am I supposed to have completed earlier stages? | Reading-list project home and stages 2–5 | State that readers continue their own preceding-stage application; the starter is not five completed stages. |

The request-tracing walkthrough starts the API, saves a URL during a controlled title timeout and sees 201 with a persisted record. The learner then adds response IDs and operation events and creates the support command. Queued-job propagation is labeled as an optional extension so it does not obscure the first deliverable.

## Simulated senior reader: implementation and operating boundaries

| Reader question | Clarification |
|---|---|
| Is the AWS architecture implemented? | No: every architecture page labels the local/deployment boundary and names remaining adapters and resource wiring. |
| Can I upload app.py to Lambda unchanged? | No: the starter's cloud mapping distinguishes its HTTP handler from a Lambda event handler. |
| Does SQLite become DynamoDB automatically? | No: schema/key design, conditional writes and storage adapters are explicit work. |
| Does SQS provide the application's job correctness? | No: committed intent, deduplication, ownership/fencing and outcome state remain application responsibilities. |
| Is the stated scale a measured capability? | No: the workload section labels constructed inputs and local-demo limits. |
| Does a successful local model establish an actual regional failover or hostile-code sandbox? | No: the assignment and AWS mapping identify the separate runtime/isolation/recovery work. |
| Are fixture identities production authentication? | No: the local server binds to loopback, calls its header X-Demo-User and describes the verified-identity/membership replacement. |
| What evidence finishes the task? | Captured commands and outcomes, persisted state or decision artifact, declared simulated dependencies, and the specific failure/recovery behavior. |

## Direct execution and publication constraints

The revision adds no automated test suite, scheduled check or publishing gate. Main remains the publication source. Existing deployment workflows and deployment scripts are unchanged.

All 75 mechanism programs and four existing AI workflows were executed while writing their output examples. The new HTTP application was run with actual requests: save during title timeout (201), list (200), owner edit (200), stale edit (409), non-owner edit (404), per-member read state (200), and missing identity (401). Restarting the process with the same database retained the saved record and note. These are local observations, not AWS deployment evidence.

The site was built and its representative project pages inspected at mobile and desktop widths. Review includes the tracing page, a design problem, a workflow brief, a continuing stage and the starter instructions. This document records the editorial review and observed local behavior; it adds no CI requirements.
