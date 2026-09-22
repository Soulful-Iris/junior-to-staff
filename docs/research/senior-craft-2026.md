# Senior craft research: corrected evidence snapshot

Reviewed 2026-09-22. This replaces the former “condensed from primary sources” summary: organization names and search excerpts were not claim-level citations. See the [claim ledger](claim-ledger.md) for exact URLs, date basis, role/sample, source status and limits; [withdrawn assertions](senior-craft-working-notes.md) remain explicit.

## Retained mechanisms

Reliability claims C01–C03 support user-facing ratios, careful retry semantics and recovery feedback. The teaching arithmetic is constructed: a million eligible requests with ten thousand failures produces 99% success and consumes ten 99.9% request budgets, regardless of a short outage duration. Three total attempts at three layers gives 27 leaf attempts; three retries after the original gives 64. The [runnable reliability lab](../../curriculum/03-production/05-reliability/labs/reliability/README.md) verifies those countermodels and adds an unfamiliar incident with raw metrics.

Recent primary incident reports C04–C06 supply [production case](../../indexes/production-cases.md) context. They document operator observations, not hiring frequency, universal safe settings, or independent causal proof. AWS service mappings, workloads, diagrams of proposed designs and acceptance thresholds are curriculum constructions.

For data/observability, C11–C13 support narrow version-specific semantics. Conditional object writes do not grant a multi-object transaction. PostgreSQL heap layout does not follow every primary-key choice. SDK/specification stability must be checked per component. Exact market shares, overhead guarantees and “default” platforms have been removed rather than promoted from untraceable notes.

## Curriculum decisions, not research findings

We teach a design by naming the operation, invariant, workload and failure boundary; drawing a simple baseline; breaking it with a counterexample; then calculating the improved design's cost and recovery behavior. Caches, replicas and shards are possible choices after measuring the bottleneck, not an unconditional sequence every system must follow.

A senior practice answer should connect evidence to a reversible mitigation, an explicit budget and the next observation that could change the decision. Cross-team ownership and recovery authority form the lead extension. These are declared teaching standards, not statistical claims about a hiring market.
