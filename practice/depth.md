# Depth within the same problem

These are assessment checkpoints for one curriculum. Foundation, operating constraints, and broader ownership are follow-ups within the same lesson; they are not separate reading paths. Use the [curriculum](../curriculum/README.md) for learning order. The preserved level expectations below are practice criteria, not company-wide hiring rules.

![One problem, a bookmark service, answered at three depths: foundation adds one API, one database, an ownership check, stable pagination and one justified index; operating constraints adds consistency, overload, authorization, data access, recovery and rollout; broader ownership adds scope, compatibility, a migration path, who else it breaks and what it costs to reverse](../assets/diagrams/same-problem-three-depths.svg)

<a id="junior"></a>

## Foundation

Start with HTTP, browser state, data modelling, indexes, validation, and tests. Draw where a request waits and who owns every piece of state. Learn arrays/maps, binary search, stack/queue, BFS/DFS, and basic dynamic programming. Junior design depth varies significantly by employer; use the recruiter packet to set the time split.

### Practice checkpoints

1. Review the coding foundations, then implement two-sum, a sliding window, binary search, and BFS.
2. Build the bookmark API and UI exercise in full stack. Include loading, empty, error, and success states.
3. Run AWS lab 1, then the queue lab at its foundation scope. Explain IAM roles versus user authentication.
4. Solve a 30-minute coding mock and a 25-minute small-feature design mock.
5. Prepare two true stories: a bug you owned and feedback that changed your implementation.

Related concepts: [architecture](../curriculum/03-production/01-system-design/mechanism-reference.md) · [coding](../curriculum/01-code/02-data-structures-algorithms/practice-sequence.md) · [AWS](../curriculum/03-production/03-infrastructure/aws/README.md) · [full stack](../curriculum/02-applications/03-frontend/full-stack-practice.md).

### Same question, deeper evidence

Practice prompt: **A bookmark service.**

| Standard | What the answer demonstrates |
|---|---|
| Meets this practice level | One API plus database, ownership checks, stable pagination, and one index justified by a query. |
| Goes further | Show an out-of-order response bug and fix it; test that a different user cannot access a bookmark. |
| Trap | Do not introduce microservices to avoid describing a schema. |

### Evidence to assess

- From a fresh contract, implement a small correct feature, including empty/error states and an ownership failure test.
- Draw browser, API, database and an index; explain each request and write without naming extra services to avoid the schema.
- Solve a maps/window/search/tree problem independently and give input-size and auxiliary-space bounds.
- Repeat a different [candidate exercise](candidate/coding.md) on a later occasion. Keep failed tests and repairs in the [attempt record](attempt-record.md); use the rubric to select a prerequisite, not predict a hiring result.

[Interview home](interview-guide.md) · [Recent evidence](../docs/research/interview-evidence.md)


<a id="senior"></a>

## Operating constraints

Use the deeper follow-ups within each subject as a diagnostic. If you can explain a concept and implement its critical mechanism, move to timed practice. Spend the most time on the constraints you cannot yet defend: consistency, overload, authorization, data access, recovery, and rollout. Keep coding in the rotation.

### Practice checkpoints

1. Attempt a 45-minute design mock before reading its solution. Record your weakest dimensions.
2. Work through architecture concepts and the notification and file-sync designs. Recalculate their example workloads.
3. Run the queue lab; inject duplicate, conflicting, and poison messages. Show which writes actually happen.
4. Complete the Python set and TypeScript concurrency, cancellation, and LRU exercises; do the practical bug drill.
5. Build the full-stack exercise with optimistic updates and conditional writes.
6. Prepare six project stories and repeat two design mocks with a new constraint halfway through.

Related concepts: [architecture](../indexes/system-designs.md) · [coding](../curriculum/01-code/02-data-structures-algorithms/practice-sequence.md) · [AWS](../curriculum/03-production/03-infrastructure/aws/README.md) · [full stack](../curriculum/02-applications/03-frontend/full-stack-practice.md).

### Same question, deeper evidence

Practice prompt: **A notification platform.**

| Standard | What the answer demonstrates |
|---|---|
| Meets this practice level | Durable acceptance, bounded workers, retry policy, deduplication boundary, offline users, metrics, and a cost model. |
| Goes further | Demonstrate the crash-after-effect case; explain why a timeout does not prove a write failed. |
| Trap | A cache cannot protect the database if every request bypasses it during a cache outage. |

### Evidence to assess

- Implement the [importer](../curriculum/02-applications/04-testing/labs/importer/README.md) against unseen pages and explain replay, conflicts, deadlines and crash recovery.
- Demonstrate save A/type B and lost acknowledgments in the [editor](../curriculum/02-applications/03-frontend/labs/bookmark-editor/README.md); draw the changed state and write predicates.
- During an unfamiliar [design session](candidate/design.md), calculate capacity, identify the consistency authority, and adapt when a worker crashes after an external effect.
- Complete two independent unfamiliar occasions using [dimension gates](README.md). A severe invariant failure cannot be averaged away by polished presentation. Preserve assessor observations and corrected artifacts.

[Interview home](interview-guide.md) · [Recent evidence](../docs/research/interview-evidence.md)


<a id="staff"></a>

## Broader technical ownership

Staff preparation adds scope, sequencing, and influence to hands-on correctness. Start with the operating-constraint checks above; do not use strategy language to hide an unexplained data path. Treat disagreements and organisational constraints as design inputs. This is a practice rubric, not a claim that every employer runs a special staff round.

### Practice checkpoints

1. Complete the operating-constraint diagnostic and maintain weekly timed coding practice.
2. Work the multi-tenant migration design. Identify service owners, contracts, and data invariants before components.
3. Extend the AWS lab with tenant quotas and a regional recovery design; document what is implemented and what is only proposed.
4. Write a two-page decision memo: options, cost assumptions, smallest experiment, ownership, milestones, and cancellation criteria.
5. Run a 60-minute design mock: change a business requirement at minute 25 and remove a dependency at minute 40.
6. Prepare stories about cross-team disagreement, a strategy you changed, an incident, and an initiative you stopped or simplified.

Related concepts: [architecture](../indexes/system-designs.md) · [coding](../curriculum/01-code/02-data-structures-algorithms/practice-sequence.md) · [AWS](../curriculum/03-production/03-infrastructure/aws/README.md) · [full stack](../curriculum/02-applications/03-frontend/full-stack-practice.md).

### Same question, deeper evidence

Practice prompt: **Move a shared platform between data models.**

| Standard | What the answer demonstrates |
|---|---|
| Meets this practice level | Compatibility across independently deployed clients, backfill, reconciliation, staged adoption, rollback, and retirement ownership. |
| Goes further | Quantify migration load and duplicate costs; distinguish reversible routing from irreversible data loss. |
| Trap | “We aligned stakeholders” needs the actual disagreement, your intervention, evidence, and outcome. |

### Evidence to assess

- Meet the senior implementation gates, including hands-on coding and a failure reproduction; a strategy memo does not replace them.
- Draw independent producer/consumer rollouts, old/new data ownership, backfill plus tombstones, and a repair path. State when rollback stops being safe.
- Quantify regional recovery capacity and data-loss limits; assign owners, compatibility tests, stop conditions and retirement evidence across teams.
- Adapt to two staged constraint changes in the [design assessor pack](assessor/design.md). Use the [fictional scored lead example](assessor/scored-examples.md) to calibrate evidence, then record two independently assessed unfamiliar occasions of your own.

[Interview home](interview-guide.md) · [Recent evidence](../docs/research/interview-evidence.md)
