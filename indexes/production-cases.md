# Production architecture casebook

Start with a real failure. Explain why the original design allowed it, predict the changed state, and build a mechanism whose limits you can demonstrate. These cases serve both learning paths.

## Recent cases and reading order

| Case | Incident date | Learn | AWS translation |
|---|---|---|---|
| [1 · Configuration](../curriculum/03-production/02-delivery/cases/configuration-rollout.md) | GitHub · July 8, 2026 | Control plane, invariants, canaries, rollback | AppConfig, CloudWatch, immutable artifacts |
| [2 · Retry amplification](../curriculum/03-production/05-reliability/cases/retry-amplification.md) | GitHub · August 17, 2026 | Deadlines, budgets, uncertain outcomes | SDK policy, bounded Lambda/ECS callers |
| [3 · Deployment headroom](../curriculum/04-scale-and-evolution/02-performance-cost/cases/deployment-headroom.md) | GitHub Actions · August 6, 2026 | Capacity envelopes, readiness, recovery | ECS/Fargate, ALB, connection budgets |
| [4 · Stale job status](../curriculum/04-scale-and-evolution/01-data-at-scale/cases/status-projections.md) | GitHub · August 20, 2026 | Projections, outbox, replay, freshness | DynamoDB/Aurora, Kinesis, status API |
| [5 · Hot partitions](../curriculum/04-scale-and-evolution/01-data-at-scale/cases/hot-partitions.md) | GitHub Actions · July 9, 2026 | Key design, ordering, tenant fairness | DynamoDB keys and bounded fan-out |

Each lesson starts with a constructed interviewer brief, a workload/expected-behavior contract and an explicit method. It then supplies baseline, corrected and changed-requirement diagrams, the preserved mechanism-specific animation and still, worked calculations, and senior/lead follow-ups. Most implementation exercises are clearly labeled build briefs; the retry case links runnable arithmetic, not a cloud deployment. Numbers in our worked examples are deliberately small and reproducible, not company measurements.

## Use one case in 45 minutes

1. Read only the reported event and predict the first overloaded or invalid boundary.
2. Watch the comparison. Explain the state transition that changes the outcome.
3. Draw the AWS design and identify one shared dependency that could defeat it.
4. Work the arithmetic; then change one assumption.
5. Implement or specify the failure drill and say what evidence would falsify your design.

For AI-assisted practice: ask for a deliberately flawed implementation of one mechanism, review it, and produce a counterexample. For interview practice: explain it without tools before discussing AWS service names.

## Evidence ledger · checked 2026-09-22

| Primary source | Publication | Scope |
|---|---|---|
| [GitHub July report](https://github.blog/news-insights/company-news/github-availability-report-july-2026/) | August 12, 2026 | July 8 configuration and July 9 shard incidents |
| [GitHub August report](https://github.blog/news-insights/company-news/github-availability-report-august-2026/) | September 9, 2026 | August 6, 17, and 20 incidents |
| [Cloudflare remediation update](https://blog.cloudflare.com/code-orange-fail-small-complete/) | May 1, 2026 | Recent completed resilience work; motivating outages occurred in 2025 |

All five selected incidents are within March 22–September 22, 2026. Recent publication does not turn an old incident into a recent one. These reports describe provider observations; they do not establish interview frequency or independent causal proof. AWS mappings and numerical scenarios are curriculum designs, not claims about GitHub's infrastructure. Some source headings and impact-duration summaries disagree; we avoid converting those into precise outage-duration claims.

AWS technical documentation is official live guidance with publication age unknown; accessed 2026-09-22. It is not counted as recent dated engineering or interview evidence. Follow the links beside each service claim. No AWS resources were deployed for this casebook.

[Unseen incident with raw metrics](../curriculum/03-production/05-reliability/labs/reliability/incident.md) · [Budgeted AI evaluation](../curriculum/04-scale-and-evolution/03-ai-systems/labs/evaluations/README.md) · [Claim-level provenance](../docs/research/claim-ledger.md)

[Interview route](../practice/interview-guide.md) · [AI engineering route](../curriculum/01-code/01-problem-solving/ai-assisted-practice.md)
