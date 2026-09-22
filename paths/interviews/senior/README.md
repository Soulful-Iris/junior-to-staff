# Senior · Own the design and its failure behavior

Use the existing senior chapters as a diagnostic. If you can explain a concept and implement its critical mechanism, move to timed practice. Spend the most time on the constraints you cannot yet defend: consistency, overload, authorization, data access, recovery, and rollout. Keep coding in the rotation.

## Your route

1. Attempt a 45-minute design mock before reading its solution. Record your weakest dimensions.
2. Work through architecture concepts and the notification and file-sync designs. Recalculate their example workloads.
3. Run the queue lab; inject duplicate, conflicting, and poison messages. Show which writes actually happen.
4. Complete the Python set and TypeScript concurrency, cancellation, and LRU exercises; do the practical bug drill.
5. Build the full-stack exercise with optimistic updates and conditional writes.
6. Prepare six project stories and repeat two design mocks with a new constraint halfway through.

Start reading: [architecture](../architecture/designs.md) · [coding](../coding/README.md) · [AWS](../aws/README.md) · [full stack](../full-stack/README.md).

## Same question, deeper evidence

Practice prompt: **A notification platform.**

| Standard | What the answer demonstrates |
|---|---|
| Meets this practice level | Durable acceptance, bounded workers, retry policy, deduplication boundary, offline users, metrics, and a cost model. |
| Goes further | Demonstrate the crash-after-effect case; explain why a timeout does not prove a write failed. |
| Trap | A cache cannot protect the database if every request bypasses it during a cache outage. |

## Exit checks

- Explain every arrow and write in the design without reading notes.
- Implement the critical mechanism and make an intentionally broken version fail a test.
- State time and auxiliary space for coding; identify network, storage, and operational costs for architecture.
- Respond to a new requirement by changing the design, with a reason.
- Use [the rubric](../practice/README.md) to identify a concrete next exercise. A score is practice feedback, not a hiring prediction.

[Interview home](../README.md) · [Recent evidence](../research/README.md)
