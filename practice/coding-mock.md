# Run an unfamiliar coding mock

You are practicing how to turn an unfamiliar contract into working code under a training timebox. Start with the [inventory event consumer](candidate/coding.md): repeated deliveries must not increase stock twice. Your output is an implementation, a narrated example, and an explanation of how it changes under a new requirement. The schedule below guides the session, not the algorithm.

Pick one unfamiliar variant from a completed topic. Close the reference files. Use the tools allowed in your target interview.

| Minutes | Do | Evidence |
|---|---|---|
| 0–5 | Clarify input, output, malformed input, mutation | One ordinary and one boundary example |
| 5–10 | Explain baseline and improvement | A precise invariant |
| 10–30 | Implement | Working code you can explain |
| 30–40 | Test and repair | Empty, duplicate, adversarial, and ordinary inputs |
| 40–45 | Explain cost; change one requirement | Correct time/space analysis and adaptation |

For a real assessed session, give another person the [assessor pack](assessor/coding.md) and open only the [candidate brief](candidate/coding.md). Record timing, hints, code and changed-constraint evidence in the [attempt record](attempt-record.md). A familiar prompt is retired for that candidate.

For self-practice, choose: return the longest unique substring (not its length); count subarray sums from a stream; add a cycle to prerequisites; change LRU capacity to bytes; or bound API fan-out with mixed failures.

**Practice evidence:** correct behavior, an explainable invariant, useful tests, accurate complexity, and a reasoned follow-up. A memorized implementation without these is unfinished practice. If stuck, record the exact missing concept and return to its lesson; do not restart the entire path.

Senior/staff extension: integrate the function into an API with a deadline and input bounds. Explain who owns overload, retries, and data correctness. Use the [production casebook](../indexes/production-cases.md) for concrete failure follow-ups.

[Back to the route](../curriculum/01-code/02-data-structures-algorithms/practice-sequence.md)
