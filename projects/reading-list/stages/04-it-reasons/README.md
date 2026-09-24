# P4 · it reasons, provably

## What you are building

> Add optional tag suggestions to the same reading list. The allowed taxonomy is databases, frontend and reliability. A model suggests an unsupported tag, or source text tells it to call a tool. Users must still be able to tag links manually when generation fails.

**Working contract:** Model output is a proposal, not confirmed user data. Validate a closed tag set, preserve source/model versions and require explicit user acceptance. Manual save/list/tagging remains usable without a model response.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../../curriculum/01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Three allowed tags | Validate exact normalized enum membership; a plausible fourth tag is still outside this contract. |
| 200 new links/day; 25% suggestion use assumption | Fifty model-assisted cases/day provides a bounded initial scope and review workload. |
| Two-second optional suggestion budget | On timeout, show manual tagging; do not delay the already committed link. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/reading_list_it_reasons.py
```

[Open the starting code](../../../../examples/architecture-starts/reading_list_it_reasons.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| tag_suggestion | link_id,source_version,model,prompt,proposed_tags | Unconfirmed, provenance-bearing output. |
| confirmed_tags | link_id,user_revision,tag_ids | User-authorized application state. |
| suggestion_outcome | accepted,rejected,invalid,unavailable | Useful product evidence beyond generation success. |

## AWS implementation

![P4 · it reasons, provably: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/reading-list-it-reasons.svg)

The model adds a proposal path beside the existing user-owned state. Keeping separate records makes it impossible for a retry or late answer to masquerade as a user-confirmed tag.

## Build it in this order

### 1. Keep the manual workflow complete

Add a tag picker backed by the closed taxonomy and conditional user revision. Save a link and tag it with the model disabled. This is the fallback and comparison baseline, not an unfinished error screen.

### 2. Generate a versioned proposal

Queue optional suggestion work with link/source identity. Pass only authorized bounded content to the model and record model/prompt versions. Treat retrieved instructions as content and expose no effectful tools for this task.

### 3. Validate and present suggestions

Parse the structured response, reject unknown tags and limit count/duplicates. Display the proposal distinctly from confirmed tags. A user action commits selected allowed tags against the current link revision; a late proposal cannot overwrite a manual choice.

### 4. Measure whether it helps

Record acceptance, correction, invalid-output rate, latency and usage assumptions. Review examples where a confident suggestion was wrong. Keep privacy and deletion behavior consistent with the earlier stages, including warmed suggestion caches.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Model access | Suggestion worker can invoke the selected model and write proposals, not perform unrelated tools. |
| Validation | Closed enum, bounded input/output and source-version checks before showing a proposal. |
| Fallback | Manual tagging remains available when queue, model or parsing fails. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | finance is rejected, and suggestions do not populate confirmed tags automatically. |
| Disable model access | Manual tagging still works. |
| Change the link while generation runs | The old source-version proposal is not applied to the new content. |

## The next design decision

Continue to stage 5 by migrating the tag representation while old browsers, queued jobs and model prompts still refer to the previous contract.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · All regressions pass

**Changed requirement:** A bug was fixed and all required cases now pass. What should the release record show? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Keep those passing regressions. Demonstrate that a seeded wrong-tag or cross-user-data mutation is caught, report challenge coverage and stochastic variability separately, and do not tune on held-out labels.

</details>

## Follow-up 2 · Budget expires mid-task

**Changed requirement:** Two attempts consume the task budget before a valid suggestion arrives. What gets committed? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Persist a visible exhausted/no-suggestion outcome without changing confirmed tags. Reserve budget before calls, bound attempts and elapsed time, and measure time-to-usable-suggestion; first-token latency is only relevant if streaming is actually shown.

</details>

## Supplied mechanism practice

- [Runnable evaluation and judge fixtures](../../../../curriculum/04-scale-and-evolution/03-ai-systems/labs/evaluations/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
