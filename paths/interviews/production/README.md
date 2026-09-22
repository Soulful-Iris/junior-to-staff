# Production architecture casebook

Start with a real failure. Explain why the original design allowed it, predict the changed state, and build a mechanism whose limits you can demonstrate. These cases serve both learning paths.

## Recent cases and reading order

| Case | Incident date | Learn | AWS translation |
|---|---|---|---|
| [1 · Configuration](01-config.md) | GitHub · July 8, 2026 | Control plane, invariants, canaries, rollback | AppConfig, CloudWatch, immutable artifacts |
| [2 · Retry amplification](02-retries.md) | GitHub · August 17, 2026 | Deadlines, budgets, uncertain outcomes | SDK policy, bounded Lambda/ECS callers |
| [3 · Deployment headroom](03-headroom.md) | GitHub Actions · August 6, 2026 | Capacity envelopes, readiness, recovery | ECS/Fargate, ALB, connection budgets |
| [4 · Stale job status](04-status.md) | GitHub · August 20, 2026 | Projections, outbox, replay, freshness | DynamoDB/Aurora, Kinesis, status API |
| [5 · Hot partitions](05-hot-keys.md) | GitHub Actions · July 9, 2026 | Key design, ordering, tenant fairness | DynamoDB keys and bounded fan-out |

Each lesson has a mechanism-specific animation, a static alternative, a topology or state diagram, a worked calculation, an implementation exercise, and junior/senior/staff follow-ups. Numbers in our worked examples are deliberately small and reproducible, not company measurements.

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

AWS technical documentation is checked for present behavior and may have an older publication date. Follow the links beside each service claim. No AWS resources were deployed for this casebook.

[Interview route](../README.md) · [AI engineering route](../../ai-engineering/README.md)
