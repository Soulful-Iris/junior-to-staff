# Practice · turn understanding into visible evidence

## Design mocks

Use [the worked designs](../architecture/designs.md) as prompts before reading their solutions. Record the session or keep a timestamped outline. At minute 25, introduce a changed constraint: ten times the burst, offline clients, stricter consistency, a failed region, or half the budget. Ask the candidate to revise the design, not merely name another service.

| Level | Exercise | Evidence to collect |
|---|---|---|
| Junior | 25-minute bookmark feature design + 30-minute coding | Complete request path, ownership check, correct code, edge-case test |
| Senior | 45-minute notification/file-sync design + 40-minute practical task | Quantified assumptions, deep failure analysis, implemented critical mechanism |
| Staff | 60-minute platform/migration design + decision memo | Cross-team contracts, sequencing, recovery, cost, uncertainty, retirement ownership |

Times are training choices, not promised company round lengths.

## Behaviorally anchored rubric

Score each dimension 0–3. Use dimensions individually; a total is not a hiring prediction.

| Dimension | 0 · absent/incorrect | 1 · with prompting | 2 · independent and sound | 3 · deeper evidence |
|---|---|---|---|---|
| Clarification | Solves a different problem | Clarifies obvious inputs | Establishes constraints/non-goals | Spots a hidden product conflict and resolves it |
| Correctness | Violates a core invariant | Fixes an obvious defect with help | Handles stated cases and boundaries | Finds a counterexample to a plausible alternative |
| Architecture | Unconnected service names | Basic flow with gaps | Full data flow and state ownership | Explains bottleneck, scale, and failure interactions |
| Implementation | Cannot run/explain code | Partial implementation | Working code with meaningful tests | Adapts safely when a requirement changes |
| Tradeoffs | Absolute slogans | Names a disadvantage | Compares viable options using constraints | Defines a measurement that would change the decision |
| Operations/security | Ignores failure or access | Adds generic logging/auth | Defines recovery, metrics, and authorization | Tests uncertain outcomes and cross-boundary failures |
| Communication | Unexplained leaps | Understandable after questions | Clear, paced, invites clarification | Prioritizes the most consequential uncertainty |
| Ownership/influence | No personal contribution | Describes team work vaguely | Explains own decisions and outcomes | Changes cross-team direction with evidence and follow-through |

For junior practice, establish correctness and a complete small flow first. For senior, expect independent failure/tradeoff reasoning. For staff, add cross-team scope and executable sequencing while retaining technical correctness. Do not demand staff scope from a junior candidate.

## Behavioral and project deep dives

Prepare real stories, not invented metrics. Use this sequence: context → constraint → your action → alternatives → evidence/outcome → reflection. Distinguish “I” from “we.” If you do not know a historical number, state the uncertainty and use a verifiable qualitative outcome.

| Story | First question | Follow-up that tests depth |
|---|---|---|
| Ownership | What ambiguous problem did you take responsibility for? | What did you decide without waiting for instructions? |
| Disagreement | When did a colleague prefer another approach? | Explain their reasoning fairly. What changed the decision? |
| Incident | What failed and what did users experience? | Which mitigation did you choose, and how did you know it worked? |
| Migration | How did you change a running system? | How did old/new clients coexist? When did rollback become difficult? |
| Mentoring | How did someone become more effective through your help? | What did they do independently afterward? |
| Failure | Which decision would you change? | What evidence was available then, and what did you miss? |
| Staff direction | How did you influence several teams? | Who disagreed, who owned delivery, and what work did you stop? |

A worked **fictional** example: a team wants a cache for a slow endpoint. You measure the query, discover a missing owner/time index, and propose an index rollout. Compare read improvement, write overhead, and the avoided invalidation work. A strong story includes what you measured and who accepted the tradeoff. Replace this with a true project; do not present the fictional story as your experience.

## A useful practice week

Choose three sessions: one concept + implementation, one coding/practical mock, one design + project-story mock. Spend the next session on the weakest observed dimension. Repeat the failed exercise with a changed input after a day, then a week. Adjust session lengths to your schedule; do not equate pages read with readiness.

## Feedback log

```text
Date / target role / prompt:
Round mode: independent | AI allowed
Assumptions stated:
Invariant and implementation:
Counterexample or failure found:
Weakest rubric dimension, with evidence:
Next exercise and success criterion:
Revisit date:
```

[Interview home](../README.md) · [Evidence behind this path](../research/README.md)
