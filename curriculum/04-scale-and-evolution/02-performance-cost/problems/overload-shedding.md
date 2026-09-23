# Overload: protect the requests that can finish

> **Interviewer:** “An API receives 40,000 requests/s after a partner retry storm. At 20,000/s its database already saturates. Paid writes, free reads, and internal health checks share one worker pool. What happens in the next minute?”

**Your contract.** Keep paid writes available where capacity permits; shed work early with a stable policy; reserve enough capacity for health and recovery. Define an admission signal that does not wait for every caller to time out. Constructed scenario and workload.

| Load and failure | Expected behavior |
|---|---|
| 12k/s paid writes, 8k/s free reads | Accept within measured safe capacity; report tail latency by class |
| Free reads spike to 30k/s | Shed or cache free reads before they starve paid writes |
| Database slows to half capacity | Reduce admission, expose 429/503 with bounded retry guidance |
| Every client retries after 1 second | Jitter/backoff and budgets prevent retry traffic from multiplying overload |

![A shared pool lets low-value retries crowd out work that could finish](../../../../assets/design-next/overload-shedding-before.svg)

## Calculate the queue before choosing an autoscaler

At 40k/s arriving and 20k/s service capacity, backlog grows by **20k requests per second** if admission does nothing. A 100k-request buffer fills in five seconds; a bigger queue raises latency rather than increasing throughput. Reserve per-class concurrency and cap queue waiting against each deadline. Shed low-priority work at the gateway, set a retry budget with randomized backoff, and measure accepted work, dropped work, p99, and recovery time. Autoscaling cannot instantly repair a constrained database or hot key.

![AWS architecture with edge controls, separate budgets, and a measurable bottleneck](../../../../assets/design-next/overload-shedding-aws.svg)

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| Amazon API Gateway (edge admission) | Reject coarse excess early and authenticate clients | Application Load Balancer plus app-owned prioritization for finer classes |
| Amazon ElastiCache (cache) | Serve safe repeatable reads without hitting the database | CloudFront (CDN) for public cacheable content nearer users |
| Amazon ECS (application compute) | Implement per-class concurrency limits, deadlines, and shedding | AWS Lambda with reserved concurrency if request shape and saturation permit |
| Amazon RDS (database) | Own durable writes; monitor its real service capacity | Amazon DynamoDB for key-value access patterns and a compatible model |
| Amazon CloudWatch (telemetry) | Observe queue age, p99 by class, and rejected work | Existing tracing/metrics system with same per-class evidence |

A cache is only a substitute for database reads that may legally be stale. API Gateway throttling alone does not encode the business priorities; the service still needs admission budgets. State what you shed and what you never drop.

![Queue area and deadlines show why larger buffers can worsen outcomes](../../../../assets/design-next/overload-shedding-detail.svg)

**Senior follow-up:** Health checks succeed while users time out. Build an overload signal from useful work and queue delay; show a 60-second incident trace.

**Staff follow-up:** Three products share a data tier. Set per-tenant and per-product budgets, equitable borrowing, and a governance process for changing priority without silently starving a smaller customer.

**Practice artifact:** Compute backlog under three loads, draw priority lanes and degradation response, then describe how to test shedding safely under a load ramp.

**Source boundary:** Original scenario. [Meta's September 2026 shared proxy account](https://engineering.fb.com/2026/09/03/core-infra/zgateway-proxy-zippydb-meta/) discusses overload protection; the [AWS Builders' Library on retries](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) describes retry amplification. Neither is an interview-question report.
