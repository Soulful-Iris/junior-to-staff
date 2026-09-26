# Capacity, performance and cost

Measure the bottleneck and defend an improvement with resource and cost evidence.

<section class="chapter-context" markdown="1">

## Measure the user’s delay and the cost of completed work

Speeding up a 40 ms helper inside a 900 ms request cannot make the page four times faster. Similarly, halving CPU use may leave a fixed-capacity bill unchanged. You will separate elapsed time, resource use, and billed units.

Identify a measured bottleneck, make one relevant change, and compare equivalent workloads. Use the deployment-headroom case to account for capacity temporarily removed during a rollout. Keep teaching numbers, local measurements, and cloud invoices clearly labeled.

The one-box lesson is a worked postmortem of a real experiment: the stack somebody actually used, the ten problems that came up in order, and the fix for each. Two of the results contradict the usual guess — a server that fails on latency with a zero error rate, and a load generator that flatters its own tail.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Data systems at scale](../01-data-at-scale/README.md)

Before measuring, know which layer can possibly be the cost: the memory / disk / network ladder in [Estimate request rates, storage, latency and availability](../../01-code/01-problem-solving/estimation-constants.md) separates the thousand-fold steps from the rounding errors.

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Find the bottleneck and measure cost per useful operation](measurement-and-cost.md) |
| 2 | [One small server: the stack, what broke, and what fixed it](one-box-ceiling.md) |
| 3 | [Reserve capacity for rollout, zone loss and backlog recovery](cases/deployment-headroom.md) |
| 4 | [Reject excess API work before queues grow without bound](problems/overload-shedding.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Production observability](../../03-production/04-observability/README.md) · [Data systems at scale](../01-data-at-scale/README.md).

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [AWS infrastructure](../../03-production/03-infrastructure/README.md).
