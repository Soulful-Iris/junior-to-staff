# 5. The thing you decided not to build

## What you are building

> Decide whether to build a custom export scheduler for a team currently producing two exports a month. The proposed platform takes six engineer-weeks plus a day each month to maintain. A three-day script may satisfy the actual need, but the decision must include comparable behavior and operating cost.

**Working contract:** Produce a concrete build/buy/simplify/defer decision with assumptions, required behaviors, ownership and a trigger for reconsideration. A decision not to build still includes a usable smaller solution and evidence that it meets today’s need.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Custom: six five-day engineer-weeks + one day/month | Forty-two engineer-days over a year under these assumptions. |
| Script: three days + 0.25 day/month maintenance assumption | Six engineer-days/year; include this explicit maintenance assumption in the comparison. |
| Two exports/month | Twenty-four annual exports; current demand does not by itself justify a general scheduling platform. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/the_thing_you_decided_not_to_build.py
```

[Open the starting code](../../../../examples/architecture-starts/the_thing_you_decided_not_to_build.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| requirements | export_format,access,frequency,retry,audit | The same required behavior for every option. |
| option_estimate | build_days,maintenance_days,service_cost,uncertainty | Comparable horizon and explicit unknowns. |
| decision | choice,owner,small_solution,revisit_trigger | Actionable result with a reversible next step. |

## AWS implementation

![5. The thing you decided not to build: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/the-thing-you-decided-not-to-build.svg)

The optional AWS path is deliberately smaller than a custom scheduling platform. Scheduling can be added when demand requires it; no periodic export or monitor is created by this curriculum update.

## Build it in this order

### 1. Observe the actual export task

Sit with the operator, record inputs, recipients, file size, access checks and recovery steps. Distinguish scheduling from transformation, delivery and auditing. Two monthly exports may need a reliable command more than a platform.

### 2. Build the smallest useful spike

Implement one authorized export with a stable run ID, deterministic file naming and a visible success/failure record. Include retry and cleanup behavior. Time the real operator task before and after; do not make a polished platform mockup the only evidence.

### 3. Compare equal requirements

Put script, managed service and custom system against the same permissions, audit, frequency and recovery needs. Include maintenance/on-call and verify current provider pricing only if it will decide the choice. Label uncertain estimates instead of converting them into false precision.

### 4. Record the decision and trigger

Choose the small solution if it meets current needs, name its owner and document how to run/repair it. Revisit if three teams need daily audited exports, required guarantees change or measured operator cost crosses the stated threshold. A competitor feature alone is not evidence of your customers’ demand.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Initial choice | A local/operator-invoked script may be sufficient; the AWS diagram is a small managed alternative to evaluate. |
| Access | Restrict source reads and export downloads; record the operator and run identity. |
| Cost | Compare one maintenance horizon and verify current prices before treating a managed-service cost as decisive. |

For this decision project, provision resources only if a bounded implementation spike needs them; the diagram is also usable as the concrete option being evaluated. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The constructed annual estimates are 42 engineer-days versus 6. |
| Run the small export twice with one identity | The operator gets one logical artifact/result. |
| Change demand to daily audited exports for three teams | Revisit the old decision against the new requirements. |

## The next design decision

The script becomes business-critical while its author is unavailable. Treat ownership, documentation and recovery as part of the small solution; small code does not mean zero operating responsibility.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · Demand changes

**Changed requirement:** Three teams now each need daily exports with an audit trail. Does the old no remain binding? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Reopen because the specified trigger occurred. Reuse the original analysis, update workload and support costs, and evaluate whether the smaller intervention still meets the contract.

</details>

## Follow-up 2 · A competitor launches it

**Changed requirement:** A competitor advertises a similar feature, but your customers have not asked. Is that enough? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Treat it as new evidence to investigate, not proof of your demand. Seek user behavior and contract gaps, then bound a reversible experiment. State which downside cannot be recovered if you wait.

</details>

</details>
