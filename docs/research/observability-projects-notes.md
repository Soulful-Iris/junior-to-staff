# Working notes — 10-observability projects.md (written 2026-09-22)

Verification log for facts stated in `tiers/02-senior/10-observability/projects.md`.
Everything below checked 2026-09-22 unless noted.

## OpenTelemetry / CNCF

- OpenTelemetry moved to CNCF **Graduated** maturity 2026-05-11; announced
  2026-05-21 at the Observability Summit, Minneapolis. Sources: cncf.io
  announcement (2026-05-21), opentelemetry.io/blog/2026/otel-graduates/.
  Matches the section README's claim (which was checked 2026-09-21).
- Profiles signal was promoted to alpha around graduation — still not stable.

## AWS X-Ray SDK → OpenTelemetry

- AWS announced (Cloud Operations Blog, 2025-10-29) that the **X-Ray SDKs and
  daemon enter maintenance mode 2026-02-25** and reach **end-of-support
  2027-02-25**. AWS's recommended instrumentation path is OpenTelemetry
  (ADOT or upstream SDKs). The X-Ray *service* continues — OTLP endpoint,
  W3C trace ids, semantic conventions.
- Transaction Search: spans ingest as structured logs into the `aws/spans`
  log group; you can ingest **100% of spans**; a percentage is indexed as
  trace summaries in X-Ray; CloudWatch Logs features (metric filters,
  Insights) work on spans. Source: docs.aws.amazon.com CloudWatch
  Transaction Search pages.
- Application Signals is the APM/SLO layer over the same spans.

## ADOT tail sampling topology

- ADOT collector ships `groupbytrace` + `tail_sampling` (GA since May 2023).
- Official ADOT "advanced sampling" doc recommends a gateway layer running
  the **loadbalancing exporter** (default `routing_key: traceID`) in front of
  a processing layer running groupbytrace + tail_sampling. Confirms the
  two-layer picture in the diagram.
- Advanced sampling is **not available in ADOT Lambda layers** (batch span
  processor requirement).
- loadbalancing exporter resolvers: `static`, `dns`, `k8s`, `aws_cloud_map`
  (ECS; returns max 100 hosts). One OTLP exporter per endpoint; queue/retry
  resiliency options off by default.
- tail_sampling processor: `decision_wait` default **30s**, `num_traces`
  default **50,000**. Memory sizing ≈ new-traces-per-sec × decision_wait.

## CloudWatch / X-Ray pricing (us-east-1, checked 2026-09-22)

- Custom metrics, tiered per metric-month: first 10,000 at **$0.30**, next
  240,000 at **$0.10**, next 750,000 at **$0.05**, over 1M at **$0.02**.
  Prorated hourly; billed only in hours the combination receives data.
  Each unique dimension combination is its own metric. First 10 free.
- Logs: ingestion **$0.50/GB** Standard (Infrequent Access $0.25/GB),
  storage **$0.03/GB-month**, Logs Insights **$0.005/GB scanned**.
  (One WebFetch of the pricing page mis-summarised Insights as $0.12/GB —
  cross-checked against four 2026 pricing guides, all say $0.005/GB.)
- Standard alarm **$0.10 per alarm metric per month**.
- X-Ray: perpetual free tier **100,000 traces recorded/month** (+1M
  retrieved/scanned); **$5.00 per million recorded** beyond.
- Synthetics: 100 canary runs/month in the always-free tier.
- Log group retention default: never expire.

## Cardinality arithmetic used in project 3

Base metric from the README's diagram: 4 methods × 20 routes × 5 status
classes = 400 series → 400 × $0.30 = **$120/month**.
Add `user_id` with 10,000 values → 4,000,000 combinations. At CloudWatch
tiers, if every combination stayed active all month:
10,000×0.30 + 240,000×0.10 + 750,000×0.05 + 3,000,000×0.02
= 3,000 + 24,000 + 37,500 + 60,000 = **$124,500/month**.
Hourly proration means the real bill scales with *active* combinations —
lower, and still absurd. Stated with that hedge.

## Diagram

`assets/diagrams/tail-sampling-topology.svg` — two panels: round-robin
fragmenting one trace across two collectors (policy runs on fragments,
keeps a one-span stump), versus a stateless layer routing by trace id so
the whole trace reaches one sampler. Animated dots; frame one shows dots
at origin (base cx/cy = path start, opacity animations start and end at 1).
