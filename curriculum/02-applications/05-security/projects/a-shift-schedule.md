# Prevent overlapping shifts and enforce manager access

## Application background

A café uses a schedule to assign employees to locations and times. Managers can edit only locations they currently manage; an employee cannot work two overlapping shifts.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** Authorized schedule operations with an atomic overlap rule and a walkthrough of access revocation while a browser remains open.

Build a shift planner for a café with two locations. A manager assigns Ana from 09:00–12:00 while another manager assigns her 11:00–14:00. A former manager still has the schedule open in a browser after their access is revoked.

**Required behavior:** Only current managers may change a location’s schedule. An employee cannot hold overlapping active shifts across locations. Cached schedule visibility and stale browser sessions do not authorize new changes.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope; the cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/a_shift_schedule.py
```

**Supplied file:** [`examples/architecture-starts/a_shift_schedule.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/a_shift_schedule.py). You can also [read or download the source here](../../../../examples/architecture-starts/a_shift_schedule.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
409 overlapping shift
saved
403 revoked
```

### Set up your implementation workspace

Create `work/a-shift-schedule/` in your checkout (or use a separate repository). Copy the supplied mechanism into that directory as `mechanism.py`, then extract its state transitions into functions you can call from your implementation. The record and module names below describe what you must implement; they are not a promise that files with those names already exist. Keep a `README.md` beside your implementation with its exact run commands and observed results.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| shifts | employee,start_utc,end_utc,location,version | Authoritative occupancy and conditional edits. |
| manager_membership | subject,location,role,revision | Current write authorization. |
| audit_events | shift,actor,before,after,request_id | Who changed the schedule and why. |

## Implement the assignment

### 1. Model time and overlap

Store UTC instants plus the location timezone needed for display and recurring intent. Use half-open intervals and require end after start. In PostgreSQL, enforce employee/time exclusion in the write transaction; a prior availability query is only advisory.

### 2. Authorize the actual mutation

Resolve current manager membership for the target location and validate employee eligibility. Scope every query and update. If access changes during a long edit, the final save checks current authority and returns a clear denial without silently losing the draft.

### 3. Make concurrent changes visible

Require expected shift version for edits/cancellations. Show who changed the latest version and preserve the losing proposal. Commit an audit intent with the change so a crash cannot erase evidence of an accepted schedule edit.

### 4. Publish and recover schedules

Send notifications asynchronously after commit. A failed notification does not cancel a valid shift. Keep versioned export/print views and demonstrate recovery from backup while preserving accepted assignments and audit history.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | The overlap is rejected, the adjacent shift succeeds, and revoked m1 cannot assign Ben. |
| Two managers race for one employee | One authoritative transaction rejects the conflict. |
| Stop email delivery | The committed schedule remains correct and notification failure is visible. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 40 employees; two locations; four weeks visible | A small relational dataset; correctness matters more than distributed storage. |
| [09:00,12:00) and [11:00,14:00) | They overlap; [12:00,15:00) is a valid adjacent shift. |
| Immediate revocation for new writes | Recheck current membership at commit; token validity alone is insufficient. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Prevent overlapping shifts and enforce manager access: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/a-shift-schedule.svg)

A relational exclusion constraint directly expresses overlapping employee occupancy. Identity and cached UI state are inputs to the workflow, while current membership and the database write decide whether the change is allowed.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local static/media delivery path | Amazon CloudFront: schedule web interface | Configure an origin, cache policy and private-content access; distinguish cached bytes from current authorization. |
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: shift API | Create routes and an integration; translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: scheduling application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local records and transaction boundary | Amazon Aurora PostgreSQL: shift authority | Write PostgreSQL schema/migrations and a database adapter; configure credentials, connection limits and recovery. |
| Local pending-work collection | Amazon SQS: change notifications | Publish committed job intent, consume messages and persist deduplication/ownership state; add visibility, retry and dead-letter handling. |
| Local notification delivery fixture | Amazon SES: staff email transport | Implement email submission and provider outcome tracking with verified sender configuration and scoped credentials. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Database | Exclusion constraint by employee/time and short transactions; index location/date views separately. |
| Authorization | Current membership check for each mutation; no client-supplied manager role. |
| Notifications | Bounded retry and visible failure status without changing committed shift ownership. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Add recurring shifts across a daylight-saving transition. Keep local recurrence intent separate from UTC occurrences and define the policy for nonexistent or ambiguous local times.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · A link was cached

**Changed requirement:** You add CloudFront for static assets. What happens to the protected schedule route? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use a cache-disabled behavior for protected schedule data and no-store responses. Validate the token against the authoritative store for every new request; fail closed if it is unavailable. Static shell assets may remain cached.

</details>

## Follow-up 2 · Product accepts bounded revocation

**Changed requirement:** Product now allows up to 60 seconds before a revoked link stops working globally. What must be specified? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Choose and verify a bounded authorization propagation/cache policy; an object TTL alone is not necessarily the token-decision bound. Measure warm identical GETs across delivery locations and define fail-closed behavior. Signed expiry bounds access only under its actual expiry semantics.

</details>

## Supplied mechanism practice

- [Warm-cache revocation fixtures](../../../04-scale-and-evolution/01-data-at-scale/labs/cache-consistency/revocation.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
