# Measure whether existing checks detect real defects

## Application background

A multi-user bookmark service has checks that report success, but maintainers need to know which ownership and expiry mistakes those checks would notice. The task is to evaluate existing evidence.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** A sensitivity report linking deliberate behavioral changes to observed failures or coverage gaps in a disposable copy.

Review the evidence protecting a multi-user bookmark service. A green suite exists, but nobody knows whether it notices a missing owner filter or an off-by-one expiry check. Produce a short sensitivity report using the existing exercise code; use a disposable working copy for deliberate defects.

**Required behavior:** Distinguish meaningful behavior changes from equivalent edits. Report which selected defects are detected, which survive and which time out. A percentage over a small selected set is evidence about that set, not proof of all correctness.

The primary deliverable is the report or operational procedure named above, backed by a reproducible local demonstration. Build the smallest supporting code needed to make that evidence visible.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/01_the_suite_that_can_fail.py
```

**Supplied file:** [`examples/architecture-starts/01_the_suite_that_can_fail.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/01_the_suite_that_can_fail.py). You can also [read or download the source here](../../../../examples/architecture-starts/01_the_suite_that_can_fail.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
Selected semantic defects: 2
Detected: 1
Needs investigation: ['expiry boundary']
```

### Set up your implementation workspace

Create `work/01-the-suite-that-can-fail/` in your checkout (or use a separate repository). Copy the supplied mechanism into that directory as `mechanism.py`, then extract its state transitions into functions you can call from your implementation. The record and module names below describe what you must implement; they are not a promise that files with those names already exist. Keep a `README.md` beside your implementation with its exact run commands and observed results.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| mutation_record | edit_id,changed_behavior,scope | Why the edit is relevant to the contract. |
| observation | edit_id,input,outcome,elapsed | Reproducible evidence from an isolated run. |
| review_report | detected,survived,timed_out,excluded | Honest denominator and remaining uncertainty. |

## Implement the assignment

### 1. Choose the protected behavior

Open an existing ownership/expiry implementation and write its exact examples: Ben must not see Ana’s record; a record is expired at now >= expires_at. Keep the original program and environment fixed while changing one behavior at a time.

### 2. Classify candidate edits

Remove the owner predicate and change the expiry comparison independently. Exclude comments and equivalent renames from the semantic denominator. Inspect whether the edit is reachable and actually changes the contract before calling it a surviving defect.

### 3. Capture isolated outcomes

Run each selected version in a disposable directory with a fixed input and deadline. Record normal failure, timeout, execution error and survival separately. Keep the smallest input that exposes a missed behavior; do not manufacture a failure when the current evidence already catches the defect.

### 4. Write the engineering conclusion

Name the uncovered boundary and the evidence needed to protect it. Report sampled scope and limitations. Keep this as a learning exercise and review artifact; no CI requirement or automatic website-publishing check is introduced.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | The report uses two semantic candidates and names the surviving expiry boundary. |
| Use a comment-only edit | It is excluded rather than counted as a missed defect. |
| Make an edit loop forever | The outcome is timeout with its input retained, not an invented pass. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Four proposed edits | Missing owner filter and < changed to <= are semantic candidates; a comment change and a safe local rename are excluded. |
| Two relevant semantic candidates | One detected and one surviving means 50% of this selected set, not 25% of all four textual edits. |
| Ten-second execution deadline assumption | A hang is recorded separately from an assertion failure and a normal pass. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Measure whether existing checks detect real defects: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/01-the-suite-that-can-fail.svg)

The cloud version is a bounded experiment runner with durable evidence. S3 or ECS does not decide whether a mutation is meaningful; that judgment comes from the stated behavior contract.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local file, object fixture or exported payload | Amazon S3: versioned exercise inputs | Implement upload/download and metadata adapters, scoped access, object naming, retention and incomplete-upload cleanup. |
| Application or worker process | Amazon ECS: isolated experiment runner | Build a container and task definition; supply configuration, task roles and graceful shutdown behavior. |
| Local file, object fixture or exported payload | Amazon S3: outcome artifacts | Implement upload/download and metadata adapters, scoped access, object naming, retention and incomplete-upload cleanup. |
| Local diagnostic events | Amazon CloudWatch Logs: run diagnostics | Emit structured JSON from the deployed runtime and configure log delivery, retention and query permissions. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Local first | Use separate temporary directories and fixed inputs; cloud execution is optional for larger experiment batches. |
| Runner | No production credentials; CPU/memory/wall limits and cleanup after every run. |
| Artifacts | Store commit identity and selected edits with outcomes; exclude secrets and unrelated user data. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


All twenty selected defects are detected. Report that result and the sampled risks honestly; expand coverage only for a concrete uncovered behavior, not to meet a quota of failures.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · A mutant hangs

**Changed requirement:** One mutant creates an infinite loop. Does that count as a successful detection? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Record timeout separately and impose a runner deadline. If termination is part of the contract it is a detected harm, but it is not a passing assertion; retain the smallest hanging input.

</details>

## Follow-up 2 · All relevant mutants are caught

**Changed requirement:** The suite kills all twenty selected semantic mutants. Must you invent a current regression? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

No. Preserve the passing regressions and report the sampled scope. Add new challenge cases based on risks, not a quota of failures; a seeded defect demonstrates sensitivity even after its repair.

</details>

</details>
