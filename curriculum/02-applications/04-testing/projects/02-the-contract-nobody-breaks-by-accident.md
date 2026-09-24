# 2. The contract nobody breaks by accident

## What you are building

> Protect a preview API used by two separately deployed applications. It returns title and durationMs; a provider refactor changes durationMs from 12 to "12", and another changes the unit to seconds without changing the JSON type.

**Working contract:** The provider and consumers agree on field presence, runtime types, units and error shapes. Static language declarations do not validate bytes received over HTTP. Compatibility is demonstrated with the supported old consumer behavior.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Two consumers released independently | A provider rollout cannot assume simultaneous consumer upgrades. |
| 12 milliseconds versus "12" | The latter violates the numeric runtime contract even if a permissive caller coerces it. |
| 0.012 seconds in durationMs | Type-valid but semantically wrong; units belong in the contract and examples. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/02_the_contract_nobody_breaks_by_accident.py
```

[Open the starting code](../../../../examples/architecture-starts/02_the_contract_nobody_breaks_by_accident.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| response_schema | title:string,durationMs:number >= 0 | Runtime validation plus documented units. |
| consumer_examples | supported client version and input/output | Actual decoding and usage behavior. |
| error_contract | status,code,message,request_id | Stable failure interpretation across versions. |

## AWS implementation

![2. The contract nobody breaks by accident: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/02-the-contract-nobody-breaks-by-accident.svg)

The gateway handles a configured request boundary. Provider response validation and consumer decoding are separate application responsibilities.

## Build it in this order

### 1. Write the wire contract

Use the existing request/response boundary lab as the starting application. Document exact JSON, content type, required fields, units and error responses. Keep successful and failed examples for each supported consumer.

### 2. Validate the runtime boundary

Parse and validate received data before domain logic uses it. Check booleans separately when the language treats them as numbers. Gateway request validation, where configured, does not automatically validate provider responses or semantic units.

### 3. Exercise old and new consumers directly

Send the numeric response and then the string response through the actual decoding path. Add an optional field and observe whether each supported client tolerates it; do not assume every decoder ignores unknown fields.

### 4. Evolve with an explicit adapter

Introduce a new field/version for changed units or meaning, preserve the old representation during the support window, and derive both from one canonical value. Record owner and retirement evidence without coupling the guide’s deployment to new checks.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Gateway | Configure body models/content-type handling deliberately; validate domain formats in the handler. |
| Versioning | Store schemas and supported consumer examples with the implementation commit. |
| Diagnostics | Log safe schema error paths, not entire sensitive request/response bodies. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Numeric 12 is accepted; string "12" is rejected. |
| Change milliseconds to seconds without renaming | The semantic example reveals the incompatible meaning. |
| Send an unexpected content type | The API follows the documented reject/parse policy instead of silently bypassing validation. |

## The next design decision

Add a strict consumer that rejects unknown fields. Decide whether an additive response change requires a version for that supported client, and document the evidence behind the decision.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · The request content type differs

**Changed requirement:** A caller sends `text/plain` and a malformed numeric query parameter. Which gateway checks apply? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

REST basic validation checks required parameter presence/nonblank values, not numeric formats. Body validation requires a matching model or a deliberate `$default`/reject policy. Validate domain types in the handler.

</details>

## Follow-up 2 · The provider evolves

**Changed requirement:** Add an optional field while an old consumer remains deployed. What should fail? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

The compatible addition should pass agreed consumer tolerance checks. Removing a required field or changing its meaning must fail. Include strict-consumer behavior explicitly instead of assuming all additions are harmless.

</details>

## Supplied mechanism practice

- [Executable request/response boundary lab](../../01-backend/labs/api-contract/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
