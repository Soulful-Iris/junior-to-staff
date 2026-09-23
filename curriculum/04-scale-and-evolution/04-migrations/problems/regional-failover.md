# Regional failover: which acknowledged write survives?

> **Interviewer:** “A primary Region accepts a booking and returns 200. It goes dark before the asynchronous replica sees the write. Health checks route the customer to a second Region, where the booking is missing. What can the product honestly promise, and what do operators do next?”

Assume 3,000 writes/s, a 15-minute recovery-time target, and an *initial* proposal of zero lost acknowledged bookings. These are exercise constraints; derive whether the architecture actually supports both targets and where cost or latency changes.

| Event | Expected answer |
|---|---|
| Write v9 is acknowledged in Region A, then A dies | State whether v9 survives; asynchronous replication alone does not guarantee it |
| Customer retries booking in B | Preserve request identity, detect duplicate if v9 later returns |
| A comes back with unreplicated data | Do not blindly make A writer again; reconcile and fence old owners |
| Planned cutover while users remain active | Demonstrate read and write behavior during transition |

![A locally acknowledged write is missing after asynchronous regional failover](../../../../assets/design-practice/regional-failover-boundary.svg)

## Make RPO and RTO concrete

RPO bounds lost accepted data; RTO bounds service restoration. If an acknowledgment happens before the second durable copy commits, zero acknowledged-write loss is false under total regional loss. Options include cross-Region synchronous or strongly consistent commit at higher latency/availability cost, explicitly accepting nonzero RPO, or changing what 200 means. Draw the exact acknowledgement point and name the owner of writes in each Region. DNS or health checks change routing, not data durability.

![Version nine is acknowledged, disappears during failover, then returns with the old Region](../../../../assets/design-practice/regional-failover-trace.svg)

**Senior follow-up:** A is partitioned rather than destroyed; both Regions can reach some clients. Fence the old writer before promoting B and define behavior when fencing cannot be confirmed. Use an epoch or lease with write-time enforcement; observing a lease in a monitoring dashboard does not prevent a stale process writing.

**Staff follow-up:** Product asks for 99.99% availability, 15-minute RTO, zero acknowledged loss, and unchanged write P95. Use a small capacity/latency budget to show which constraints are in tension. Offer two defensible architectures and a failure exercise that could disprove each. Assign the reconciliation owner and rollback authority.

**Practice artifact:** A/B region boxes, timeline labeling last committed/replicated/acknowledged versions, decision memo on RPO/RTO, and a rehearsal of stale-owner fencing and return-to-primary.

**AWS translation:** DynamoDB global tables offer distinct replication/consistency modes with different write latency and durability consequences; do not label an eventually consistent cross-Region replica “zero RPO.” See [AWS global tables modes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.html). [Meta's June 2026 failure-readiness account](https://engineering.fb.com/2026/06/03/data-center-engineering/lights-out-systems-on-validating-instant-power-loss-readiness/) motivates practicing abrupt regional-equivalent failures; this booking scenario is constructed.
