# Working notes — 19 · Migrations projects (2026-09-22)

Scratch notes for `tiers/03-staff/19-migrations/projects.md` and
`assets/diagrams/shadow-read.svg`. Not part of the guide.

## AWS facts verified against docs.aws.amazon.com this session (2026-09-22)

- **ALB forward action, weighted target groups** — multiple target groups per
  forward action, weight 0–999, traffic distributed in proportion to weights.
  Caveat found: sticky sessions need target group stickiness (AWSALBTG cookie)
  or weight changes do not move cookied clients.
  Source: elasticloadbalancing/latest/application/rule-action-types.html
- **Route 53 weighted routing** — traffic share = weight / sum of weights;
  "If you want to stop sending traffic to a resource, change the weight for
  that record to 0." Reversal is still bounded by clients honouring TTL.
  Source: Route53/latest/DeveloperGuide/routing-policy-weighted.html
- **CodeDeploy** — predefined canary configs exist and are named as used in the
  text: `CodeDeployDefault.LambdaCanary10Percent5Minutes` (10% first increment,
  remaining 90% five minutes later), `CodeDeployDefault.ECSCanary10Percent5Minutes`.
  Automatic rollback "when a deployment fails or when a monitoring threshold
  you specify is met" (CloudWatch alarms on the deployment group).
  Sources: codedeploy/latest/userguide/deployment-configurations.html,
  deployments-rollback-and-redeploy.html
- **DMS** — "perform one-time migrations or replicate ongoing changes to keep
  sources and targets in sync"; "supports fully heterogeneous data migrations
  between the supported engines." Source: dms/latest/userguide/Welcome.html

No prices anywhere in the section, so nothing to date-stamp on cost.

## Decisions

- Five projects = one migration's apparatus, in order: awkward case → block →
  counter → shadow → finish. Counter is two-sided (static + runtime) so that
  project 5's "zero" is defined by project 3.
- Block is a ratchet (checked-in baseline that may only shrink), not a wall —
  a red build on day one gets the check deleted.
- Shadow-read triage taxonomy: new-path bug / old-path bug / comparator bug.
  Old-path bugs are the staff-register moment (preserve or fix is a decision).
- Distribution of the AWS patterns the task named: CloudTrail/Athena/X-Ray → p1;
  Config vs SCP, cfn-lint/Guard → p2; EMF, Athena vs Logs Insights, EventBridge
  Scheduler + Lambda + SNS → p3; metric filter, Kinesis vs SQS replay, Traffic
  Mirroring declined, dual-write reconciliation (EventBridge+Lambda+CloudWatch)
  → p4; ALB weights vs Route 53 weights, CodeDeploy canary, DMS vs read
  replica, snapshot expiry, Cost Explorer → p5.

## Diagram

`shadow-read.svg`, 760×400. One request forks at a junction; old path row
(green, serving) returns the answer to the user along the top line; new path
row (dashed, shadow) feeds only the comparator; comparator emits to DIFF LOG;
dashed warm stub with a stop bar marked "never returned". SMIL: request dot
rides both branches, old answer returns, diff drops into the log, 9 s loop,
no `begin` offsets; mid-cycle elements carry base `opacity="0"` so frame one
reads correctly in static renderers. Rendered in chromium and inspected.
