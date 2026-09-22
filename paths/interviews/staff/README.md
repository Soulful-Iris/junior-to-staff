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

- Explain every arrow and write in the design without reading notes.
- Implement the critical mechanism and make an intentionally broken version fail a test.
- State time and auxiliary space for coding; identify network, storage, and operational costs for architecture.
- Respond to a new requirement by changing the design, with a reason.
- Use [the rubric](../practice/README.md) to identify a concrete next exercise. A score is practice feedback, not a hiring prediction.

[Interview home](../README.md) · [Recent evidence](../research/README.md)
