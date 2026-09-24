# Practice profiling, representative load and unit-cost decisions

[Chapter](README.md)

A reading-list page waits for its API, and a background worker enriches saved links. Performance work should improve a stated user outcome. Cost work should account for useful completed operations, including failures, retries, and allocated idle resources.

## Choose your starting code

Read [the measurement lesson](measurement-and-cost.md). Use the real [bookmark editor](../../02-applications/03-frontend/labs/bookmark-editor/README.md) for a local browser/API path. The [deployment headroom case](cases/deployment-headroom.md) supplies hypothetical capacity arithmetic for a separate workload.

![A distribution reveals slow requests that a single average can hide](../../../assets/diagrams/average-hides-it.svg)

<a id="1-the-profile-that-contradicts-you"></a>

## 1. Attribute the delay before choosing an optimization

A developer suspects formatting work, but the request may spend most of its time waiting for database calls.

**Your task.** Write a prediction, then capture an appropriate trace and profile. Distinguish CPU samples, allocation, and elapsed waiting. Inspect the critical path and query count instead of adding durations of overlapping spans.

**What to observe.** The report names the measured bottleneck and the limits of the instrument. A CPU profile with little activity does not prove a fast request.

**Changed requirement.** Two dependencies can overlap but share a small connection pool. Compare elapsed time and resource contention after adding bounded parallelism.

[Worked mechanism and implementation context](measurement-and-cost.md)

<a id="2-four-numbers"></a>

## 2. Compare the same workload before and after one change

An optimization can improve typical latency while worsening a slow tail or increasing failures.

**Your task.** Record dataset, offered rate, sample count, cache state, duration, and environment. Make one justified change and compare p50, p99, throughput, and errors under equivalent conditions. State uncertainty when the sample is too small for a stable tail estimate.

**What to observe.** Four latency numbers have the same units and measurement method. Improvement is allowed to be real, negligible, or negative. The exercise does not require one metric to worsen.

**Changed requirement.** The new implementation uses more memory. Include memory and saturation in the tradeoff instead of declaring victory from latency alone.

[Worked mechanism and implementation context](measurement-and-cost.md)

<a id="3-the-load-generator-that-lied"></a>

## 3. Compare closed-loop clients with scheduled arrivals

A client that waits for a response before sending again reduces its offered load when the service stalls. Real independent arrivals may continue during the same stall.

**Your task.** Run a bounded closed-loop scenario and a scheduled-arrival scenario with the same controlled pause. Record intended send time, actual send time, completion, backlog, and generator saturation. Preserve limits so the experiment remains contained.

**What to observe.** Explain why each generator represents a different workload. Account for missed scheduled work instead of silently discarding it from latency statistics.

**Changed requirement.** The generator itself cannot keep up. Report that limit and the unsent work before interpreting the service’s apparent capacity.

[Worked mechanism and implementation context](../../02-applications/04-testing/projects/04-the-load-test-that-finds-the-real-limit.md)

<a id="4-the-unit-cost-with-the-guesses-marked"></a>

## 4. Calculate cost per completed operation with assumptions visible

A thousand attempted title fetches produce eight hundred useful results. Per-attempt cost hides what retries and failures cost the product.

**Your task.** Choose a period and divide attributable compute, request, storage, transfer, and allocated idle costs by useful completions. Separate observed billing from estimates. Label shared-cost allocation and hypothetical prices explicitly.

**What to observe.** If the allocated total is $20 for 800 completed jobs, unit cost is $0.025/job. The $20 is a teaching input, not an AWS price quote.

**Changed requirement.** The fleet remains fixed-size after CPU use falls. Explain why additional headroom may not immediately reduce the invoice.

[Worked mechanism and implementation context](measurement-and-cost.md)

<a id="5-half-the-bill-same-p99"></a>

## 5. Reduce an attributed cost while preserving the service objective

The largest line item may be idle capacity, retained objects, or network transfer rather than the code path with the most CPU samples.

**Your task.** Choose one attributed cost and a relevant change. Compare cost, latency, errors, data durability, and recovery headroom on equivalent work. Record savings separately from deferred or transferred costs.

**What to observe.** The result reports a measured or estimated saving with its basis. No arbitrary 50% reduction is required, and a justified decision to keep capacity is valid.

**Changed requirement.** Demand grows 30% during a zone outage. Recalculate the capacity and recovery envelope before removing more spare capacity.

[Worked mechanism and implementation context](cases/deployment-headroom.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
