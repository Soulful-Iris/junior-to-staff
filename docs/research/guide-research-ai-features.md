# AI-feature research: evidence and teaching decisions

Reviewed 2026-09-22; replaces the unlinked “consensus” working note. Exact sources, dates and limitations are in [C07–C08 of the claim ledger](claim-ledger.md). The former fixed retrieval recipe, judge/attack percentages, cost ratios, latency targets and agent-architecture consensus are withdrawn; no exact statistics are retained without traceable original support.

Airbnb's 2026-07-28 engineering report supports combining programmatic, judge and human methods. Anthropic's 2025-09-29 vendor article supports considering context retrieval, compaction and notes. These publications describe engineering approaches; they do not establish interview frequency, universal sample sizes, fixed chunk counts or deployment thresholds.

Our corrected curriculum requires a task-specific oracle, passing required regressions that detect seeded faults, separate challenge/held-out sets, class-specific judge metrics, severity analysis and independent cost/latency/security gates. These are curriculum recommendations and mathematical counterexamples. In particular, 99 human passes plus one failure against an always-pass judge gives 99% agreement and 0% failure recall; a fixed regression suite may validly pass every case.

The [evaluation lab](../../paths/interviews/evaluations/README.md) implements actual faulty taggers, cumulative budget and deadline fixtures, a publicly visible but separately owned held-out exercise, and a scored release decision. It is a deterministic stand-in, not a measured real-model benchmark. Real release evaluation still needs representative data, repeated runs, label review and model/version provenance.
