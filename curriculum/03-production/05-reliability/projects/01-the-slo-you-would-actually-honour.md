# 1. The SLO you would actually honour

## What you are building

> Define a bookmark-save reliability objective with product and operations. Product asks for 99.9% successful eligible saves over thirty days. One failed minute contains a large traffic spike, so counting bad minutes gives a different answer from counting failed user requests.

**Working contract:** Write the eligibility rule, success definition, measurement point and reporting window. The request-based SLO uses summed good and total requests, including declared timeout/server-failure outcomes. Missing telemetry and zero traffic are explicit states.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 1,000,000 eligible requests; 10,000 failures | 99% observed success, not 99.9%. |
| 99.9% objective | Error budget is 1,000 failures; 10,000 failures consume ten times that budget. |
| Quiet interval 1/10 failures; busy interval 0/990 | Overall failure rate is 1/1,000 = 0.1%, not the mean of interval percentages. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/01_the_slo_you_would_actually_honour.py
```

[Open the starting code](../../../../examples/architecture-starts/01_the_slo_you_would_actually_honour.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| sli_event | operation,eligible,good,measurement_time | One agreed outcome per logical request. |
| slo_window | start,end,good,total,missing_coverage | Aggregated evidence and coverage. |
| budget_policy | objective,owner,response_actions | What the team changes when reliability degrades. |

## AWS implementation

![1. The SLO you would actually honour: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/01-the-slo-you-would-actually-honour.svg)

The database commit helps define durable success, while the request outcome determines what the user experienced. A CloudWatch ratio is only meaningful after those semantics are agreed.

## Build it in this order

### 1. Choose the user operation

Define save success as a durable accepted bookmark within the agreed latency bound. State how invalid input, authentication failure, duplicate retries and dependency timeouts count. Do not remove failures from the denominator merely because they are inconvenient.

### 2. Instrument at the outcome boundary

Emit good and eligible counts where the request’s visible result is known. Reconcile client timeouts and server completion according to the chosen user-facing definition. Record telemetry coverage; a missing counter interval is not automatically zero errors.

### 3. Calculate the rolling window

Sum counts across instances and intervals before dividing. Handle counter resets and late data explicitly. Show budget remaining and consumption rate with the raw denominator so small samples are not mistaken for strong evidence.

### 4. Agree on an actionable response

Name owners for reliability work, risky feature exposure and dependency remediation when the budget is exhausted. Keep the SLO as an operating decision for the application; this curriculum update does not add a publishing gate.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Metrics | Complete eligible counters with bounded labels and reset-aware aggregation. |
| Definition | Version changes to eligibility/latency rules; do not silently rewrite historical meaning. |
| Reporting | Explicit no-traffic and missing-data states; retain the counts behind percentages. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | One million requests and 10,000 failures show 99% success and 10× budget use. |
| Use unequal traffic intervals | Sum counts before calculating the ratio. |
| Observe zero traffic | Display no eligible traffic rather than 100% success. |

## The next design decision

Product instead wants 99.9% of one-minute windows to be usable. Define usable per window and the low-traffic rule; that is a different SLO with a different denominator.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · Traffic is uneven

**Changed requirement:** A quiet interval has 1/10 failures and a busy interval has 0/990. Is mean interval success 95%? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

No: total success is 999/1000=99.9%. Sum counts before dividing; averaging percentages gives the quiet interval unjustified weight.

</details>

## Follow-up 2 · Product wants a time SLO

**Changed requirement:** The requirement becomes “the service is usable in 99.9% of one-minute windows.” What changes? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Define a good window and its probing/traffic rule, then count eligible windows. Thirty days contain 43,200 minutes, yielding 43.2 bad-window minutes at 0.1%; state discrete rounding and no-traffic treatment.

</details>

## Supplied mechanism practice

- [Runnable reliability arithmetic and incident lab](../labs/reliability/README.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
