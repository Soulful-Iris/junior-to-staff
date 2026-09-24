# 5. The test that runs in production, forever

## What you are building

> Design a synthetic user journey for a reading-list service: sign in as a dedicated probe account, create a marker link, read it and remove it. The exercise begins with a single manual run; no recurring monitor is installed in this repository.

**Working contract:** A run succeeds only when every required step succeeds. Dependent steps skipped after failure are reported as skipped. Cleanup is attempted independently, and missing runs are distinct from successful runs.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| One-minute interval in the proposed deployed design | 1,440 runs/day and at least 4,320 create/read/delete operations before authentication and absence checks. |
| Three missing intervals | A separate heartbeat policy detects a stopped runner; no result is not a healthy result. |
| Dedicated synthetic namespace | Probe data must not appear in real users’ lists, analytics or billing. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/05_the_test_that_runs_in_production_forever.py
```

[Open the starting code](../../../../examples/architecture-starts/05_the_test_that_runs_in_production_forever.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| journey_run | run_id,started_at,location,step_outcomes | One complete execution with explicit skipped states. |
| synthetic_resource | run_id,owner,created_at | Cleanup identity and expiry fallback. |
| heartbeat | runner,last_started,last_completed | Scheduler health independent of application outcome. |

## AWS implementation

![5. The test that runs in production, forever: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/05-the-test-that-runs-in-production-forever.svg)

The journey measures the user path; heartbeat evidence measures whether the journey ran. The proposed scheduler is part of the lesson architecture, not a change to this website’s publishing behavior.

## Build it in this order

### 1. Build one manual journey

Use a dedicated account and run identity. Follow the real public DNS/TLS/application path, create a unique marker and verify its content after reading. Run it on demand first and inspect every step’s visible result.

### 2. Make cleanup independent

Keep the created resource ID as soon as it is known. Attempt deletion in a finally-style cleanup path even after a read failure, and record cleanup failure separately. Add expiry-based cleanup for abandoned synthetic data without letting it hide a failing journey.

### 3. Model missing and skipped outcomes

A create failure means read is skipped, not passed. Emit the run result and heartbeat separately. If a future scheduler is configured, monitor freshness from an independent path so a dead runner does not report its own absence as success.

### 4. Define regional interpretation

A probe inside the application VPC does not exercise public DNS and routing. Use a second location when that distinction matters, and retain location-specific evidence. A single-location failure is a useful signal, not automatic proof of a global outage.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Execution | A manually invoked runner is enough for this exercise; scheduling is an explicit later infrastructure choice. |
| Identity | Probe account has only synthetic-data permissions; credentials never enter logs. |
| Cleanup | Finite runtime and orphan-retention policy; cap synthetic data volume even if deletion repeatedly fails. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Failed create plus skipped read is not success; an absent runner becomes stale. |
| Fail the read after creation | Cleanup still attempts deletion and records its own outcome. |
| Stop the optional runner | The freshness signal detects absence independently of application errors. |

## The next design decision

A probe passes while real users fail because its account has special permissions. Compare its identity, data size and routing with the user population and remove privileges that bypass the behavior being measured.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · The scheduler stops

**Changed requirement:** No probe result arrives for three intervals. Is that equivalent to success? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

No. Monitor heartbeat freshness separately from journey outcome; distinguish no eligible data from missing instrumentation. Alert on the absent run with the monitor’s owner and last successful timestamp.

</details>

## Follow-up 2 · A regional path fails

**Changed requirement:** The probe in the application VPC passes, but public DNS fails for a region. What changes? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Probe the actual public entry path from a second location and keep region-specific outcomes. Do not automatically collapse a single-location failure into global outage; correlate it with other evidence.

</details>

</details>
