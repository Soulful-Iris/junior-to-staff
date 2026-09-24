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

## Follow-up: introduce meaning before technical shorthand

The next reading feedback showed that the first revision still assumed too much. “Commits the URL” could be mistaken for a Git commit. “Display title,” “timeout,” “save” and “reconstruct one caller's request” appeared before the page had shown what anyone sent, stored or received.

All 90 project openings now begin with a concrete user action, explain the normal outcome and then introduce the failure. Each includes an example walkthrough or request/result view. Terms such as reconciliation, lease, cache fill, time series, backfill and prompt injection are explained in the scenario where the reader needs them. Assignment sentences now describe actions to perform rather than lists of technical nouns. The redundant earlier scenario paragraphs were removed.

For request tracing, the opening shows a bookmark-save request, the relevant response fields and the meaning of 201 Created. It explains where a page title comes from, why a slow website can cause a timeout, and why the saved URL should remain. It then distinguishes a bookmark ID from a request ID and shows why interleaved diagnostic records need that request ID. The supplied title lookup is clearly identified as a local simulation.

The editorial check asks: who acts, what do they send, what does the application store or return, what failure changes that result, and what must the learner build? Product examples describe intended behavior. Supplied-server examples identify what actually runs. Prose semicolons were removed while code syntax was preserved.

The revision adds no tests, recurring checks or publication requirements. Main remains the publication source.

## Follow-up: choose introductory evidence for each problem

The further guidance is to use interview-style sizing vocabulary, current-flow animation, small code excerpts, API contracts and diagnostic evidence only when they improve that particular introduction. The [90-page evidence review](INTRODUCTION-EVIDENCE-REVIEW.md) records the choices and deliberate omissions.

Four focused animations explain the existing bookmark save flow, a lost payment reply, connection-pool waiting and a worker returning after ownership changes. Each has an authored still and uses the existing motion controls. Small-screen layouts keep these narrow diagrams within the reading width.

Selected pages now introduce concrete API responses, real excerpts from supplied local code, actual local-model output or explicitly illustrative incident records. No illustrative record is described as a production capture. Sizing appears early only when its calculation changes the design discussion. Several workflow/decision introductions use prose alone because extra diagrams or large traffic numbers would not help.

The estimation reference also needed a correction: 30,000 reads/s multiplied by 100 microseconds is three accumulated seconds of waiting per second, not thirty. This does not alone establish disk saturation because I/O can overlap. The page now distinguishes latency from throughput, states rounding and peak assumptions, and separates request-based reliability from time-based availability.

## Follow-ups and complete-course review — September 24, 2026

The reader approved the tracing lesson's introduction and assignment as the quality benchmark. New feedback: follow-ups need equally careful explanation, substantial architecture changes where requirements justify them, and actual revised diagrams when a section promises one. Reviewed all 90 briefs and expanded 133 worked scenarios. See [the per-page follow-up record](FOLLOW-UP-DESIGN-REVIEW.md).

The next authorized work extends beyond projects: distinguish parts, chapters, lessons and in-page sections in the table of contents, then review every remaining lesson individually. UI lessons need visible interface examples. Select screenshots, diagrams, animations, code, API examples, logs and sizing only where they improve the particular explanation. Preserve automatic publication from main. Do not add tests or scheduled publishing checks.
