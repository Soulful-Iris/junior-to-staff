# Review the tag-suggestion release decision and cumulative task budget

Use this after the [tag-suggestion evaluation exercise](README.md). The feature proposes tags, and a separate judge tries to detect failures. Decide whether the supplied evidence supports the declared release scope. The worked values below explain why an overall agreement percentage can hide the most consequential missed failure.

The ordinary reference regressions may all pass. They have demonstrated sensitivity to three named mutants. That is positive evidence about the narrow contract, not proof of semantic tag quality or absence of security defects outside the fixture.

| Held-out fixture metric | Result |
|---|---|
| TP / TN / FP / FN | 3 / 14 / 2 / 1 |
| Agreement | 17/20 = 85% |
| Failure recall | 3/4 = 75% |
| Failure precision | 3/5 = 60% |
| Missed severity | 10; the sole missed failure is the most severe |

**Constructed release policy:** all required regressions pass; authorization mutants must be caught; no missed severity-10 failure; failure recall ≥90% on the declared labeled evaluation; no task exceeds 10 cents or 1,000 ms in the fake-provider scenarios; manual fallback works. These thresholds belong to this exercise, not to a provider or employer.

Decision: **block the proposed judge-controlled broad release**. Regression and simulated budget checks pass, but 75% recall and a missed severity-10 failure violate two declared gates. Correct the judge/feature boundary using development examples; then obtain a new independent evaluation. A restricted keyword-only manual-assist release can be considered only with an explicit owner, narrower supported contract, no delegation of authorization to the judge, and fresh evidence for that scope. Renaming the failed set does not cure a supported-use failure.

Cost and latency: outage errors at 100 ms cost 4 cents each; only two fit the budget, so fallback at 200 ms with 8 cents. Two 700 ms attempts consume 700+300 ms before the deadline, still 8 cents under the assumed billing rule. A 3-cent budget sends no call. Explain why a real provider may finish and bill a timed-out request; the mock does not prove cancellation behavior.

Score 0–2 each: (1) validates oracle with named mutants; (2) computes class-specific metrics and severity; (3) protects held-out labels and names sample/stochastic limits; (4) makes the stated gate decision; (5) traces cumulative cost/deadline and usable fallback; (6, lead) budgets concurrent tasks and owns drift/rollback/escalation. Senior practice target: 8/10 on first five, with no zero in gate decision or budget; lead target: 10/12. Thresholds are curriculum choices, not hiring predictions.
