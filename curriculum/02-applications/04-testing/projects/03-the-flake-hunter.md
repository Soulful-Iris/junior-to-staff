# Reproduce and remove order-dependent failures

## Application background

A bookmark application uses a shared store during development checks. One case leaves data behind and a later case incorrectly assumes the store is empty.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** A minimal order-dependent reproduction, a demonstrated isolation fix and a short cause-and-effect report.

Diagnose an intermittent failure in a shared-store exercise. A case that expects an empty store passes alone but fails after another case creates an item. Rerunning until green hides the dependency rather than explaining it.

**Required behavior:** Produce a minimal deterministic reproduction and a causal explanation. Distinguish shared state, timing, external dependency and resource collision. A retry is evidence of variability, not proof of repair.

The primary deliverable is the report or operational procedure named above, backed by a reproducible local demonstration. Build the smallest supporting code needed to make that evidence visible.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/03_the_flake_hunter.py
```

**Supplied file:** [`examples/architecture-starts/03_the_flake_hunter.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/03_the_flake_hunter.py). You can also [read or download the source here](../../../../examples/architecture-starts/03_the_flake_hunter.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
isolated False ['created', 'unexpected leftover'] ['empty', 'created']
isolated True ['created', 'empty'] ['empty', 'created']
```

### Set up your implementation workspace

Create `work/03-the-flake-hunter/` in your checkout (or use a separate repository). Copy the supplied mechanism into that directory as `mechanism.py`, then extract its state transitions into functions you can call from your implementation. The record and module names below describe what you must implement; they are not a promise that files with those names already exist. Keep a `README.md` beside your implementation with its exact run commands and observed results.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| reproduction | seed,order,environment,shared_resource | Minimal facts needed to reproduce. |
| fixture_lifecycle | allocate,reset,cleanup | Explicit ownership of state, files, ports and clocks. |
| incident_note | symptom,cause,repair,evidence | Explains why the variability disappeared. |

## Implement the assignment

### 1. Reduce the failure

Preserve the failing order and remove unrelated cases until the two-operation dependency remains. Record the initial store, process reuse and cleanup behavior. Avoid adding sleeps; they change timing without establishing ownership.

### 2. Give state a clear lifecycle

Allocate a fresh store per independent case, unique temporary paths and explicit cleanup. If sharing is intentional, synchronize it and name the shared contract. Reset fake clocks and randomness as deliberately as database rows.

### 3. Force a suspected race

When only parallel execution fails, use a barrier to overlap the relevant operations and capture the shared filename/port/key. Replace accidental shared resources with unique identities or proper synchronization; a hundred lucky reruns are weaker than one controlled explanation.

### 4. Record the bounded repair

Compare the minimal reproduction before and after isolation. Keep an owner and expiry for any temporary quarantine and state the evidence gap. Do not turn a flaky rerun loop into a requirement for publishing this website.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Shared state makes one order fail; fresh stores make both independent. |
| Reuse one file in parallel | The forced overlap exposes the collision. |
| Remove arbitrary sleeps | The repaired ownership still explains the result. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Two orderings: create→expect-empty and expect-empty→create | The same inputs produce different outcomes only when state leaks between cases. |
| Twenty parallel runs share one filename assumption | A resource collision can remain invisible in every sequential ordering. |
| One fixed seed and recorded order | Reproduction must retain both; a seed alone may not capture external scheduling. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Reproduce and remove order-dependent failures: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/03-the-flake-hunter.svg)

Cloud isolation can help reproduce resource collisions, but the first diagnosis is local and deterministic. Infrastructure cannot compensate for a fixture that silently shares mutable state.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local file, object fixture or exported payload | Amazon S3: reproduction evidence | Implement upload/download and metadata adapters, scoped access, object naming, retention and incomplete-upload cleanup. |
| Application or worker process | Amazon ECS: isolated reproduction tasks | Build a container and task definition; supply configuration, task roles and graceful shutdown behavior. |
| Local records and transaction boundary | Amazon RDS PostgreSQL: disposable state fixture | Write PostgreSQL schema/migrations and a database adapter; configure credentials, connection limits and recovery. |
| Local diagnostic events | Amazon CloudWatch Logs: execution timeline | Emit structured JSON from the deployed runtime and configure log delivery, retention and query permissions. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Isolation | Unique run identity in files, schema names and object prefixes; never point the exercise at shared production data. |
| Timing | Injectable clock and explicit barriers for controlled schedules; avoid arbitrary sleep-based repairs. |
| Cleanup | Run even after failure and record cleanup errors separately from the original symptom. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


The failure depends on a third-party API. Replace it with a controlled response timeline for diagnosis, then document which live integration behavior remains outside that local reproduction.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · Parallel execution fails

**Changed requirement:** Sequential shuffled runs pass, but concurrent runs fail. What experiment comes next? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use a barrier to overlap two operations on a shared resource. Give files/ports unique test identities or synchronize intentional sharing; preserve the forced overlap as a regression.

</details>

## Follow-up 2 · The fix will take a week

**Changed requirement:** The flaky test blocks every merge while a repair is underway. How do you quarantine it honestly? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Remove it from the blocking gate only with an owner, expiry and visible nonblocking execution. Its passing reruns must not be treated as repair evidence; track the protected behavior’s temporary coverage gap.

</details>

</details>
