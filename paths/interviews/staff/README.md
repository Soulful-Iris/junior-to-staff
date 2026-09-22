# Staff · Make technical direction executable across teams

Staff preparation adds scope, sequencing, and influence to hands-on correctness. Start with the senior exit checks; do not use strategy language to hide an unexplained data path. Treat disagreements and organisational constraints as design inputs. This is a practice rubric, not a claim that every employer runs a special staff round.

## Your route

1. Complete the senior diagnostic and maintain weekly timed coding practice.
2. Work the multi-tenant migration design. Identify service owners, contracts, and data invariants before components.
3. Extend the AWS lab with tenant quotas and a regional recovery design; document what is implemented and what is only proposed.
4. Write a two-page decision memo: options, cost assumptions, smallest experiment, ownership, milestones, and cancellation criteria.
5. Run a 60-minute design mock: change a business requirement at minute 25 and remove a dependency at minute 40.
6. Prepare stories about cross-team disagreement, a strategy you changed, an incident, and an initiative you stopped or simplified.

Start reading: [architecture](../architecture/designs.md) · [coding](../coding/README.md) · [AWS](../aws/README.md) · [full stack](../full-stack/README.md).

## Same question, deeper evidence

Practice prompt: **Move a shared platform between data models.**

| Standard | What the answer demonstrates |
|---|---|
| Meets this practice level | Compatibility across independently deployed clients, backfill, reconciliation, staged adoption, rollback, and retirement ownership. |
| Goes further | Quantify migration load and duplicate costs; distinguish reversible routing from irreversible data loss. |
| Trap | “We aligned stakeholders” needs the actual disagreement, your intervention, evidence, and outcome. |

## Exit checks

- Meet the senior implementation gates, including hands-on coding and a failure reproduction; a strategy memo does not replace them.
- Draw independent producer/consumer rollouts, old/new data ownership, backfill plus tombstones, and a repair path. State when rollback stops being safe.
- Quantify regional recovery capacity and data-loss limits; assign owners, compatibility tests, stop conditions and retirement evidence across teams.
- Adapt to two staged constraint changes in the [design assessor pack](../practice/assessor/design.md). Use the [fictional scored lead example](../practice/assessor/scored-examples.md) to calibrate evidence, then record two independently assessed unfamiliar occasions of your own.

[Interview home](../README.md) · [Recent evidence](../research/README.md)
