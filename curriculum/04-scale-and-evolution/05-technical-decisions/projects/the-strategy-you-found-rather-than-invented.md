# 2. The strategy you found rather than invented

## What you are building

> Write a data-platform decision policy from five concrete team decisions. Billing, inventory and permissions require transactions; event processing requires replay; analytics needs an independent reporting workload. The goal is to shorten the next decision without pretending one datastore fits all five.

**Working contract:** The memo cites the constructed decision records, states the shared constraint, proposes a default and names evidence-based exceptions. It includes operating ownership and a review trigger when relevant capabilities or requirements change.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Five decisions: three transactional, one replay, one reporting | The majority supports a transactional default, not a universal ban on other storage. |
| Three teams maintaining separate stacks assumption | Include on-call, backup, expertise and migration effort in the comparison. |
| Six-month capability review trigger | A product or service change can invalidate the old deciding constraint; review is an explicit decision, not an installed recurring task. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/the_strategy_you_found_rather_than_invented.py
```

[Open the starting code](../../../../examples/architecture-starts/the_strategy_you_found_rather_than_invented.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| decision_record | id,workload,invariant,choice,cost,owner | Evidence for why a team chose its design. |
| policy_memo | default,exceptions,consequences,revisit_trigger | Half-page usable guidance for the next team. |
| exception_case | unmet_requirement,measured_gap,alternative | A concrete counterexample to the default. |

## AWS implementation

![2. The strategy you found rather than invented: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/the-strategy-you-found-rather-than-invented.svg)

The diagram shows one concrete composition that preserves the three different workload needs. It is evidence for the policy discussion, not a claim that every team should deploy the whole stack.

## Build it in this order

### 1. Write the five source decisions

Record D1 billing atomicity, D2 inventory ownership, D3 permission/audit transaction, D4 independently replayable events and D5 reporting isolation. Include rejected options and their actual constraint, not merely which technology the team preferred.

### 2. Extract the common default

Propose PostgreSQL for transactional application records when its measured capacity and access patterns fit. Explain existing expertise, backup/restore and operating cost. A count of three choices is a clue; the transaction requirement is the reason.

### 3. State explicit exceptions

For D4, retain an event log/archive with replay identity and retention. For D5, isolate expensive analytical scans through a projection or warehouse. Name ownership, lag and reconciliation costs introduced by each exception.

### 4. Make the next decision easier

Give teams a short decision path: required guarantee, existing default fit, measured gap, smallest exception and owner. Revisit when a named workload or service capability changes. Avoid universal slogans that erase the concrete replay and reporting counterexamples.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Decision scope | This is an evaluated option, not an instruction to provision every box. |
| Ownership | Name backup/restore, schema evolution and incident owners for each chosen service. |
| Revisit evidence | Verify current service capabilities from official documentation when they become a deciding factor; preserve the original assumption and date. |

For this decision project, provision resources only if a bounded implementation spike needs them; the diagram is also usable as the concrete option being evaluated. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The five records remain visible and the exceptions survive the summary. |
| Propose always one database | D4 and D5 provide specific counterexamples to examine. |
| Change a relevant managed-service capability | Reopen the deciding constraint rather than defending an obsolete technology rule. |

## The next design decision

A team requests a new datastore for developer preference alone. Ask for the unmet guarantee or measured operating improvement, then compare it against the additional ownership burden without treating novelty as either sufficient or forbidden.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · A new workload breaks the default

**Changed requirement:** A team needs independently replayable events rather
than current row state. Should enforcement block the design?

<details>
<summary>Expected reasoning and diagram</summary>

Route it through a documented exception review that names the mismatched
constraint and maintenance owner. Do not make a default impossible to challenge;
measure exception recurrence as feedback on the policy.

</details>

## Follow-up 2 · The evidence expires

**Changed requirement:** A managed service changes a relevant capability six
months later. Which part of the memo changes?

<details>
<summary>Expected reasoning and diagram</summary>

Separate stable invariants from dated capability/cost observations. Reverify the
source, update the constraint and rerun the decision comparison. A recent access
date does not make an old study recent evidence. A rule can also remain valid
when the changed capability does not affect its rationale.

</details>

</details>
