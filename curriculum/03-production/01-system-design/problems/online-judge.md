# Online judge: untrusted code gets a small box

> **Interviewer:** “Users submit code to a timed contest. Compile and run it against hidden tests, report results, and update a live leaderboard. Submissions are untrusted.”

This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 100,000 contest participants, 10,000 submissions/minute at peak and strict CPU, memory, and wall-time caps. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Infinite loop | Submission never exits | Worker kills it at deadline and frees the isolated sandbox. |
| Fork bomb | Code spawns many processes | Sandbox denies process/resource escalation. |
| Duplicate submit | Client retries after lost ACK | One submission ID returns one result state. |
| Hidden tests | User requests detailed failure output | Do not expose test input, secrets, or another user’s source. |

![The failure path and repaired design for Online judge](../../../../assets/design-interview/online-judge-before.svg)

## Think from the contract to the boxes

Persist a submission record, then enqueue compilation and execution. Run each language in a sandbox with no network, read-only base image, ephemeral filesystem, seccomp/container or microVM boundary, and hard CPU/memory/time limits. Workers are replaceable; results are versioned and idempotent. Treat compilation output and runtime output as hostile text before displaying it.

**First diagram:** Draw public API, durable submission state, queue, isolated compile/run pool, result checker, and leaderboard projection.

![AWS services named with their provider-neutral architectural roles](../../../../assets/design-interview/online-judge-aws.svg)

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon API Gateway** / submission entry | Authenticate, bound payload size and rate. | ALB + ECS for custom upload/stream behavior. |
| **Amazon S3** / source + test artifacts | Keep versioned packages away from worker images. | EFS for shared read-only test corpora with careful isolation. |
| **Amazon SQS** / execution queue | Buffer work and separate compile from run tiers. | Step Functions for explicit multi-language orchestration. |
| **Amazon ECS on AWS Fargate** / isolated task compute | Run ephemeral bounded tasks with per-task roles. | EC2 microVM or dedicated sandbox fleet for stronger isolation and lower cost at scale. |
| **Amazon DynamoDB** / submission/result state | Store state transitions and idempotent result IDs. | Aurora for relational contest/rank queries. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

![A focused failure, capacity, or state diagram for Online judge](../../../../assets/design-interview/online-judge-deep.svg)

## Pressure-test the design

**Follow-up: A language runtime must not read another submission’s files or reach internal network services. Draw the sandbox boundary and list capabilities denied by default.**

**Senior expectation:** A contest bursts at start time and leaderboard writes become hot. Partition execution by language/problem while aggregating rank updates asynchronously with visible freshness.

**Staff expectation:** A new language requires an untrusted runtime and supply-chain updates. Define image provenance, patch windows, emergency disable, isolation tests and acceptable blast radius.

**Practice artifact:** Draw public API, durable submission state, queue, isolated compile/run pool, result checker, and leaderboard projection. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists an online coding-judge design at Meta, Whatnot, Microsoft and other companies; individual dates are unavailable. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/coding-contest-platform/cm4szs6ae002w3g2e09amf982).
