# 3. The incident you caused on purpose

## What you are building

> Run one controlled incident exercise in a disposable staging service. A valid JSON configuration routes every title job to an unavailable host. Record when users are affected, when the responder detects it, when rollback happens and when useful work actually recovers.

**Working contract:** The drill has a named owner, bounded scope, observable stop condition and independently available rollback path. It produces a factual timeline and one completed repair. No recurring fault injection or production action is installed.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Inject 10:00:00; first impact 10:00:05; alert 10:01:00 | Detection after first impact is 55 seconds. |
| Rollback 10:02:00; backlog clear 10:03:30 | Mitigation after alert is 60 seconds; recovery after first impact is 205 seconds. |
| Maximum five-minute exercise window assumption | Stop earlier if the scoped impact or emergency-access condition is violated. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/the_incident_you_caused_on_purpose.py
```

[Open the starting code](../../../../examples/architecture-starts/the_incident_you_caused_on_purpose.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| drill_plan | environment,owner,fault,stop_condition,rollback | Concrete bounded action and independent exit. |
| timeline_event | monotonic_elapsed,wall_time,evidence_ref | Observed milestones, not reconstructed guesses. |
| repair_record | cause,change,owner,observed_result | One implemented improvement with evidence. |

## AWS implementation

![3. The incident you caused on purpose: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/the-incident-you-caused-on-purpose.svg)

The exercise separates injection, detection, mitigation and recovery. A control plane that shares the failure can block rollback, so the recovery path needs its own availability assumptions.

## Build it in this order

### 1. Prepare a bounded staging drill

Name the exact configuration field, affected worker pool and synthetic workload. Save the previous configuration and verify emergency access before injecting anything. Define the stop condition in observable terms such as oldest-job age or an unexpected environment identifier.

### 2. Inject one fault and record evidence

Change only the selected staging route to an unavailable fixture host. Record the applied configuration version, first failed job, alert delivery and responder action. Do not add simultaneous failures that make cause and effect impossible to separate.

### 3. Mitigate and follow the backlog

Restore the prior valid configuration through the independent path. Confirm the version actually applied, then watch useful completions and oldest age until recovery. A successful rollback command is not proof that waiting users have recovered.

### 4. Complete one repair

Fix the discovered weakness: semantic configuration validation, independent rollback credentials, bounded retries or clearer evidence. Re-run only the relevant bounded scenario to see whether the repair changes the measured outcome. Keep the factual timeline and remaining limits.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Environment | Explicit staging resource IDs and synthetic data; finite drill duration and named stop owner. |
| Recovery | Credentials and rollback instructions available independently of the failing application/configuration path. |
| Evidence | Record applied version and actual useful recovery; retain a redacted timeline with timestamps. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Detection is 55 s, mitigation after alert 60 s and full recovery 205 s. |
| Make the normal dashboard unavailable | The independent stop/restore path remains usable. |
| Improve only alert delivery | Report faster detection, while backlog recovery may remain unchanged. |

## The next design decision

The drill exposes a repair that cannot be completed immediately. Name the temporary operating limit and owner, and preserve the evidence rather than declaring the exercise successful solely because the service eventually recovered.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · The normal control plane fails

**Changed requirement:** You cannot reach the deployment dashboard. How do you stop the drill? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use pre-authorized independent recovery access and a time-bounded failure injection. Test its credentials and dependencies beforehand; a stop button inside the failed system is not an independent stop mechanism.

</details>

## Follow-up 2 · The fix changes only the alert

**Changed requirement:** The page arrives sooner, but users still wait the same time for backlog drain. What improved? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Detection improved, recovery did not. Report both. Choose a separate repair such as bounded retries or gradual admission, then measure net drain rather than claiming an earlier page solved capacity.

</details>

## Supplied mechanism practice

- [Raw incident evidence exercise](../labs/reliability/incident.md) — includes its own run command, fixtures and validation limits.

These exercises verify specific boundaries; completing their reference tests does not implement or assess the full project.

</details>
