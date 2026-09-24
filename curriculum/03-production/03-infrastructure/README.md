# AWS infrastructure

Map a mechanism to explicit infrastructure, permissions, and operational limits.

<section class="chapter-context" markdown="1">

## Connect code, credentials and resources deliberately

Running a local Python process does not create an AWS API, queue, or database. A deployment needs an application artifact, its configuration, resource definitions, and a runtime identity with the right permissions. Each has a separate owner and failure mode.

Begin with reproducible local execution and the service mapping. The conditional-write and upload labs provide commands. The queue lab supplies an AWS SAM template and worker. Each cloud exercise states setup, expected evidence, and cleanup.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Delivery and controlled rollouts](../02-delivery/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Build once and supply configuration safely at runtime](configuration-and-environments.md) |
| 2 | [AWS · translate a mechanism into infrastructure](aws/README.md) |
| 3 | [Use DynamoDB conditions to reject duplicate creates and stale edits](aws/lab-1-data.md) |
| 4 | [Upload private object bytes directly and finalize application metadata](aws/lab-2-upload.md) |
| 5 | [Process duplicate SQS jobs with one conditional DynamoDB result](aws/labs/job-pipeline/README.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Reliability and incident recovery](../05-reliability/README.md) · [Data systems at scale](../../04-scale-and-evolution/01-data-at-scale/README.md).

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Delivery and controlled rollouts](../02-delivery/README.md).
