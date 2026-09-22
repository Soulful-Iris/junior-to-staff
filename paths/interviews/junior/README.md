# Junior · Build and explain one complete feature

Start with HTTP, browser state, data modelling, indexes, validation, and tests. Draw where a request waits and who owns every piece of state. Learn arrays/maps, binary search, stack/queue, BFS/DFS, and basic dynamic programming. Junior design depth varies significantly by employer; use the recruiter packet to set the time split.

## Your route

1. Read concepts 1–4, then implement two-sum, a sliding window, binary search, and BFS.
2. Build the bookmark API and UI exercise in full stack. Include loading, empty, error, and success states.
3. Run AWS lab 1, then the queue lab at its junior tier. Explain IAM roles versus user authentication.
4. Solve a 30-minute coding mock and a 25-minute small-feature design mock.
5. Prepare two true stories: a bug you owned and feedback that changed your implementation.

Start reading: [architecture](../architecture/concepts.md) · [coding](../coding/README.md) · [AWS](../aws/README.md) · [full stack](../full-stack/README.md).

## Same question, deeper evidence

Practice prompt: **A bookmark service.**

| Standard | What the answer demonstrates |
|---|---|
| Meets this practice level | One API plus database, ownership checks, stable pagination, and one index justified by a query. |
| Goes further | Show an out-of-order response bug and fix it; test that a different user cannot access a bookmark. |
| Trap | Do not introduce microservices to avoid describing a schema. |

## Exit checks

- Explain every arrow and write in the design without reading notes.
- Implement the critical mechanism and make an intentionally broken version fail a test.
- State time and auxiliary space for coding; identify network, storage, and operational costs for architecture.
- Respond to a new requirement by changing the design, with a reason.
- Use [the rubric](../practice/README.md) to identify a concrete next exercise. A score is practice feedback, not a hiring prediction.

[Interview home](../README.md) · [Recent evidence](../research/README.md)
