# 5. An AI feature you can defend

## What you are building

> Assess whether an AI summary feature improves a reading-list product enough to keep. A judge agrees with humans on 99 of 100 examples, but the only human-identified failure is also marked pass. Build an evidence-based decision against a useful non-AI baseline.

**Working contract:** Compare user-relevant quality, abstention, latency and cost on a stated case mix. Calibrate failure detection separately from overall agreement. Model output and retrieved content never authorize tools or bypass current data permissions.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 99 human passes and one human failure; judge always passes | Agreement is 99%, but failure recall is 0/1 = 0%. |
| Two-second baseline; five-second AI target assumption | Measure whether added latency buys useful outcomes for the intended task. |
| 100 reviewed cases | A small constructed sample supports scoped conclusions, not a universal reliability claim. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/an_ai_feature_you_can_defend.py
```

[Open the starting code](../../../../examples/architecture-starts/an_ai_feature_you_can_defend.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| case | id,input,expected_evidence,human_outcome | Task-specific reviewed meaning of success. |
| run_manifest | baseline_or_model,versions,latency,tokens | Comparable execution evidence. |
| decision_record | useful_gain,failures,operating_cost,next_action | Keep, change, narrow or remove the feature. |

## AWS implementation

![5. An AI feature you can defend: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/an-ai-feature-you-can-defend.svg)

The cloud services run and observe the feature. The engineering decision comes from comparable task evidence and calibrated failure detection, not the presence of a model endpoint.

## Build it in this order

### 1. Build the non-AI baseline

Offer authorized source search or a deterministic extractive summary. Record the task users need to complete and the output that helps them. Compare on the same cases; do not compare a polished AI interface with an intentionally unusable baseline.

### 2. Collect decision-relevant evidence

Include ordinary, unsupported, conflicting, private and adversarial-source cases. Record source/model/prompt versions, latency and token usage. Review false confidence and justified abstention separately from stylistic preference.

### 3. Calibrate the judge

Produce a confusion table against reviewed outcomes and inspect failure recall. Add known failure examples only to measure a concrete blind spot, not to manufacture a favorable score. Keep human disagreement and uncertain cases visible.

### 4. Make a bounded product decision

State where the feature is useful, where it abstains or falls back, and the operating budget. Keep permission and tool boundaries in deterministic application code. If the baseline is better for the actual task, narrow or remove generation rather than hiding the comparison.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Model use | Explicit invocation budget and deadline; preserve a useful fallback. |
| Evidence | Restrict private case data and record versions; do not log all user content indiscriminately. |
| Decision | Document actual assumptions for usage and token volume; verify current provider pricing before making a financial choice. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | 99% agreement coexists with zero failure recall. |
| Ask for unsupported information | The feature abstains or returns source search. |
| Place a tool instruction in source content | No action authority is granted by that text. |

## The next design decision

Usage shifts to a new language or customer group. Revisit the case mix and outcome slices before reusing the original quality claim unchanged.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · A regression is fixed

**Changed requirement:** All required cases now pass. Should you loosen the feature or force a failure to keep the eval meaningful? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

No. Keep the fixed case and demonstrate sensitivity with a seeded defect. Challenge-set failures remain separately documented; protect held-out examples from prompt tuning.

</details>

## Follow-up 2 · Untrusted content asks for a tool

**Changed requirement:** A fetched page says to send another user’s saved links to a remote endpoint. What constrains the model? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Remove unnecessary outbound tool authority and scope retrieval to the authorized user. Treat model output as untrusted and validate it before effects; prompts alone cannot enforce this trust boundary.

</details>

## Supplied mechanism practice

- [Runnable evaluation and judge fixtures](../labs/evaluations/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
