# 4. The paved road

## What you are building

> Build a service template for three teams that keep forgetting log retention. New services should get fourteen days by default, while an approved thirty-day case remains easy to express. Existing deployed services can drift after creation, so the template alone cannot establish current compliance with the team policy.

**Working contract:** The generated infrastructure includes an explicit supported retention value and a discoverable override. The default reduces setup work. A separate on-demand inventory compares deployed values with intended policy; no recurring check or deployment gate is added to this repository.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Three services omit retention | Solve the repeated configuration task once and observe whether a new user can complete it unaided. |
| Default fourteen days; approved alternative thirty days | Keep policy choices explicit rather than enforcing one value for every workload. |
| Existing service with indefinite retention | Creation-time defaults cannot detect later console changes. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/the_paved_road.py
```

[Open the starting code](../../../../examples/architecture-starts/the_paved_road.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| service_spec | name,retention_days,owner | Small supported input contract with defaults. |
| rendered_template | AWS::Logs::LogGroup properties | Concrete configuration the user can inspect. |
| policy_exception | resource,reason,owner,expiry | Discoverable bounded alternative, not a hidden bypass. |

## AWS implementation

![4. The paved road: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/the-paved-road.svg)

CloudFormation supplies repeatable creation; current CloudWatch configuration is the deployed truth. An on-demand comparison reveals drift that a correct template cannot prevent by itself.

## Build it in this order

### 1. Generate the concrete resource

Turn the starting function into a small template command that accepts service name, owner and optional retention. Output inspectable CloudFormation or your team’s existing IaC format. Keep defaults near the input documentation and show the exact generated resource.

### 2. Observe a first-time user

Ask another engineer to create a service from the instructions, noting unclear steps and manual edits. Measure completion time and missing information. Improve the interface where they stumble instead of adding a ritual acknowledgment that the policy exists.

### 3. Support legitimate variation

Accept the documented thirty-day setting and explain when a separately reviewed exception is needed. Record reason, owner and review date for an unusual archive. Do not force a security archive into the same retention policy as ordinary diagnostic logs.

### 4. Inspect deployed state on demand

Use describe-log-groups or the corresponding IaC drift view to compare actual RetentionInDays with intended values. An absent value means indefinite retention, not the fourteen-day default. Report the discrepancy with resource ownership and a concrete repair command; scheduling that inventory is a separate decision.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Template | Explicit RetentionInDays and ownership tags; no silent indefinite-retention fallback. |
| Inventory | Read-only resource inspection by default; a repair targets a named resource and desired value. |
| Exceptions | Preserve reason/owner/review date and distinguish diagnostic logs from retained evidence archives. |

For this decision project, provision resources only if a bounded implementation spike needs them; the diagram is also usable as the concrete option being evaluated. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The default template contains fourteen days; thirty days is accepted; missing deployed retention is flagged for review. |
| Create a service from the instructions | The engineer can find the default and override without reading generator internals. |
| Remove retention after creation | The next explicit inventory shows the discrepancy. |

## The next design decision

The template grows fifty optional switches. Revisit the common service path and split genuinely different products instead of exposing every implementation detail as another mandatory choice.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · An existing service drifts

**Changed requirement:** A manual console edit removes retention after deployment. What notices? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Compare actual resources against the declared policy on a schedule or relevant event. Report ownership and remediation; do not claim a repository template makes all future console changes impossible.

</details>

## Follow-up 2 · A legitimate exception exists

**Changed requirement:** A security archive needs a different retention policy. Does your check block useful work? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Support a reviewed, expiring exception with reason and owner. Validate the exception itself; count repeated exceptions to discover whether the default is wrong.

</details>

</details>
