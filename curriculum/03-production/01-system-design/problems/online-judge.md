# Online judge: untrusted code gets a small box

## What you are building

> Build a programming-contest judge for 100,000 participants. Submissions may loop forever, fork processes, read files or attempt network access. The service must keep the contest responsive while treating every submitted program as hostile.

**Working contract:** POST /submissions durably accepts source and language under a request identity. Execution occurs in an isolated sandbox with CPU, memory, process, output and wall-clock limits. Results identify compiler/runtime versions and hidden-case bundle version.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 10,000 submissions/minute | About 167 submissions/s; at five seconds average execution, roughly 835 occupied execution slots before headroom. |
| 256 MiB and two CPU seconds per case as exercise limits | Wall-clock timeout is separate; sleeping or blocked programs must still terminate. |
| 100,000 participants | Apply per-user admission limits and contest priority before expensive compilation. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/online_judge.py
```

[Open the starting code](../../../../examples/architecture-starts/online_judge.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| submissions | submission_id,user,source_hash,language,state | Durable intent and reproducible toolchain selection. |
| judge_runs | submission_id,attempt,sandbox_id,limits | One isolated execution attempt. |
| results | submission_id,bundle_version,verdict,evidence | Published verdict; hidden input/output stays private. |

## AWS implementation

![Online judge: untrusted code gets a small box: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/online-judge.svg)

EC2 is the host for an isolation design you must implement; naming EC2 or Fargate does not itself prove safe execution of hostile code. The local program demonstrates only wall-clock termination.

## Build it in this order

### 1. Accept before compiling

Validate language and source-size limits, store source privately and commit a submission record plus dispatch intent. Return a status URL. Duplicate client requests return the original submission rather than spending another execution slot.

### 2. Design the isolation boundary

Use a dedicated sandbox fleet with microVM or equivalent hardened isolation, no instance credentials and no external network access for submitted code. A normal subprocess or ordinary application container is not the promised hostile-code boundary. Keep the broker outside the untrusted execution environment.

### 3. Run reproducibly with limits

Select a pinned compiler/runtime image and case bundle. Enforce CPU, memory, process count, writable filesystem, output bytes and an independent wall deadline. Destroy the sandbox after use; never let a prior submission’s files contaminate the next one.

### 4. Publish bounded evidence

Store verdict, resource usage and safe compiler output. Do not reveal hidden cases in public logs. Conditionally publish the winning run and keep retries linked to the same submission. Separate infrastructure failure from wrong answer or time limit exceeded.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Sandbox hosts | Dedicated role and network boundary; submitted processes receive neither host credentials nor metadata access. |
| Queue admission | Cap outstanding submissions per participant and total waiting time; expose queue age. |
| Artifact handling | Enforce source/output size limits and scrub compiler diagnostics of private paths or hidden-case content. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The infinite loop is terminated at the wall deadline. |
| Submit a program that reads prior files | A fresh sandbox contains no previous submission artifacts. |
| Crash a judge host | The submission retries with the same identity and publishes at most one current verdict. |

## The next design decision

Allow third-party language runtimes. Define the image admission process, patch ownership, version retirement and how old submissions remain reproducible without keeping vulnerable hosts publicly reachable.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 100,000 contest participants, 10,000 submissions/minute at peak and strict CPU, memory, and wall-time caps. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Infinite loop | Submission never exits | Worker kills it at deadline and frees the isolated sandbox. |
| Fork bomb | Code spawns many processes | Sandbox denies process/resource escalation. |
| Duplicate submit | Client retries after lost ACK | One submission ID returns one result state. |
| Hidden tests | User requests detailed failure output | Do not expose test input, secrets, or another user’s source. |

## Think from the contract to the boxes

Persist the submission and its outbox record together; a relay enqueues its ID.
The trusted broker obtains artifacts and starts a **separate untrusted execution
domain**. Compilation is untrusted too. Results use the submission/version key,
and output is bounded and treated as hostile text before display.

The program must see the input it computes on; it must not mount the whole hidden
test corpus, expected outputs, another submission, a Docker socket or cloud
credentials. The trusted checker decides what limited feedback can leave.

| Boundary | Required enforcement / negative test |
|---|---|
| Identity and network | No execution-role credentials; deny egress including metadata/credential endpoints; probe only a fake endpoint in a disposable test |
| Files and processes | Read-only runtime, isolated size-bounded scratch space, non-root identity, dropped capabilities, bounded process count; test cross-submission reads and controlled process exhaustion |
| CPU, memory, wall time | Enforced outside the submitted process; terminate the whole execution domain, not only its parent PID |
| Output and cleanup | Cap stdout/stderr bytes and disk writes; truncate safely, reap descendants and discard the domain before reuse |

**Implementation gate:** this is a design brief, not a supplied or cloud-verified
sandbox. Choose a runtime whose documented controls satisfy this table and run
loop/process/output/disk/credential-isolation fixtures in a disposable environment.
Do not assume every seccomp, capability, process or network control is configurable
on every managed container runtime. No malicious-program execution or live-cloud
isolation result is claimed here.

**First diagram:** Draw public API, durable submission state, queue, isolated compile/run pool, result checker, and leaderboard projection.

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon API Gateway** / submission entry | Authenticate, bound payload size and rate. | ALB + ECS for custom upload/stream behavior. |
| **Amazon S3** / source + test artifacts | Keep versioned packages away from worker images. | EFS for shared read-only test corpora with careful isolation. |
| **Amazon SQS** / execution queue | Buffer work and separate compile from run tiers. | Step Functions for explicit multi-language orchestration. |
| **Amazon ECS on AWS Fargate** / trusted orchestration | Can host the broker; its artifact role must never reach submitted code. A task role alone is not a hostile-code sandbox. | Separately controlled VM/microVM sandbox fleet after validating the required isolation controls. |
| **Amazon DynamoDB** / submission/result state | Store state transitions and idempotent result IDs. | Aurora for relational contest/rank queries. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

## Pressure-test the design

**Follow-up: A language runtime must not read another submission’s files or reach internal network services. Draw the sandbox boundary and list capabilities denied by default.**

**Senior expectation:** A contest bursts at start time and leaderboard writes become hot. Partition execution by language/problem while aggregating rank updates asynchronously with visible freshness.

**Staff expectation:** A new language requires an untrusted runtime and supply-chain updates. Define image provenance, patch windows, emergency disable, isolation tests and acceptable blast radius.

**Practice artifact:** Draw public API, durable submission state, queue, isolated compile/run pool, result checker, and leaderboard projection. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists an online coding-judge design at Meta, Whatnot, Microsoft and other companies; individual dates are unavailable. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/coding-contest-platform/cm4szs6ae002w3g2e09amf982).

</details>
