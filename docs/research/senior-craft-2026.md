# Research: senior craft in 2026 (read 2026-09-21)

Condensed from primary sources: the Google SRE Workbook, the AWS Builders'
Library, the Netflix tech blog, OpenTelemetry's own announcements, OWASP,
CISA, npm and PyPI documentation, DORA 2025, and engineering writing from
Pragmatic Engineer, Honeycomb and Cloudflare. Working notes in
[senior-craft-working-notes.md](senior-craft-working-notes.md).

## System design

The artefact has not changed: a design doc or RFC with motivation, constraints,
alternatives seriously considered, and trade-offs, reviewed by senior engineers.
What changed is the economics. Code generation got cheap, so **design judgment
became the scarce resource** and precise specification came back into fashion.

Telemetry from Faros AI on teams with heavy AI adoption: pull requests **51%
larger**, bugs per PR **up 54%**, median review time **up 441%**, and **31% more
PRs merged unreviewed**. DORA 2025 — renamed *State of AI-assisted Software
Development*, around 5,000 respondents — found AI now correlates positively with
throughput, a reversal from 2024, while still correlating with instability. AI
amplifies whatever the team already is.

The durable senior discipline is reasoning about failure: every scaling fix
trades one resource limit for a new failure class. Replicas buy reads and cost
staleness. Shards buy writes and cost routing and rebalancing.

## Reliability

SLOs with a **written error-budget policy** — tiered, with actual freeze rules —
and multi-window multi-burn-rate alerting (for example 1 hour plus 6 hours)
rather than static thresholds.

On retries, the AWS Builders' Library position: retry at **one layer only**,
because retries multiply across layers; prefer **token-bucket retry limiting to
circuit breakers**, which are modal, hard to test and slow to recover; never
retry a 4XX; require idempotency tokens before retrying anything with a side
effect; put jitter on all timers, not only on retries.

Graceful degradation's current reference is Netflix's prioritised load shedding:
requests bucketed CRITICAL / DEGRADED / BEST_EFFORT / BULK and shed by CPU
utilisation. After one outage, a 12x prefetch spike still left user-initiated
availability above 99.4%. Newer practice pushes shedding into the service layer
and sidecars, validated by continuous chaos load tests.

## Observability

OpenTelemetry graduated from the CNCF in **May 2026** and is the de facto
standard; traces, metrics and logs are stable across the major SDKs. A fourth
signal, **Profiles**, entered public alpha in **March 2026** — pprof-compatible
and trace-correlated, but not yet recommended for critical production.

The dominant story is cost. The "observability 2.0" argument is wide structured
events in one columnar store with metrics and traces derived at query time,
against the three-pillar model where a cardinality change can multiply a bill
overnight.

Practice worth teaching: written team instrumentation guidelines; head sampling
first; tail sampling (keep all errors, all slow requests, N% of the rest) via a
**two-layer collector with trace-ID affinity** — skipping that layer is the
commonest quiet failure; compute span metrics *before* sampling.

## Security

OWASP Top 10 **2025**: Broken Access Control at #1 (now absorbing SSRF),
Security Misconfiguration #2, and a new **A03 Software Supply Chain Failures**,
which surveyed experts voted their top concern.

The defining events are the npm worms: **Shai-Hulud** (September 2025, the first
self-propagating npm worm, credential harvesting and republishing via stolen
tokens, CISA alert 23 September) and **Shai-Hulud 2.0** (November 2025, around
796 packages, executing at preinstall).

Responses now standard: package **cooldowns** (pnpm 11 defaults to a 24-hour
`minimumReleaseAge`; the npm CLI still has none), committed lockfiles with
policy checks, **npm trusted publishing with OIDC** (GA July 2025, automatic
provenance — but a leftover classic token bypasses it, which is how the Axios
attack worked), PyPI attestations (PEP 740, Sigstore keyless, GA November 2024),
SLSA v1.2, and CISA's 2025 SBOM minimum elements.

Authentication: passkeys are mainstream (roughly 5 billion, 48% of the top 100
sites). **OAuth 2.1 is still an IETF draft, not a standard** — do not describe it
as one — though it is widely adopted in practice.

Secrets: the direction is eliminate rather than rotate, via OIDC workload
identity federation. GitGuardian found **64% of credentials leaked in 2022 were
still valid in January 2026**, and reports AI-assisted commits leaking roughly
twice as often.

## Delivery

GitHub Actions is the default CI (33% adoption against Jenkins at 28% in
JetBrains' 2025 survey). Merge queues are standard. Pipeline hardening canon: pin
actions to commit SHAs, use OIDC rather than static cloud keys, least-privilege
job permissions.

Feature flags decouple deploy from release; OpenFeature standardises the
interface; every flag needs an owner and a removal date.

Infrastructure as code: IBM closed the HashiCorp acquisition in February 2025,
Terraform remains BSL-licensed, and **OpenTofu has genuinely diverged** (state
encryption, provider-defined functions) at roughly 12% adoption.

## Data at scale

What breaks first is connection management, query shape, read pressure and
failover — not raw volume.

The order is: indexes, then cache, then replicas, then shard **last**. Cache
needs stampede protection (single-flight locks, stale-while-revalidate, TTL
jitter, probabilistic early refresh). PostgreSQL has no native sharding.

Kafka 4.0 (March 2025) **removed ZooKeeper entirely** — KRaft only. Exactly-once
ends at Kafka's boundary; the practice is at-least-once plus idempotent consumers
(unique constraints, manual offset commits) or the outbox pattern.

S3 conditional writes (2024) enable compare-and-swap, so coordination-free
architectures on object storage are now possible. Redis re-opened under AGPLv3 in
May 2025 after Valkey (BSD, Linux Foundation) became the cloud default.

## Performance and cost

Continuous profiling is mainstream: eBPF agents running always-on in production
at around 1% CPU overhead, with diff flame graphs between versions and some
teams failing deploys on regression thresholds. Profiles are also the
cost-attribution signal. FinOps now has a data standard (FOCUS), and cost
allocation is an engineering concern rather than a finance one.

## Commonly missing from roadmaps

The error-budget policy as a written organisational contract, not just the maths.
Retry-storm and metastable-failure mechanics. Tail-sampling *topology* (everyone
teaches the policy, nobody teaches the trace-ID-affinity collector layer).
Package cooldowns and lockfile policy. The classic-token-bypasses-provenance
failure. Cache stampede specifics. Cost attribution as a skill, with profiling as
its instrument. Reviewing AI output as a distinct senior skill with measured
failure modes.

## Stale advice

"Set up ZooKeeper for Kafka." "Exactly-once solves duplicates." "Terraform is the
neutral open-source default." "Redis is BSD" / "Redis is proprietary" — both
wrong now. "Publish with a long-lived npm token in CI." "S3 cannot do
compare-and-swap." "Profiling in production is too expensive." "More custom
metrics is better observability." "OWASP Top 10 2021" as current. "MFA via SMS or
TOTP is the end of the authentication conversation." And DORA 2024's finding that
AI hurt delivery performance, which the 2025 report reversed on throughput.

## Caveats from the research pass

OWASP 2025 is listed on owasp.org as the current release, but no explicit
final-publication date was confirmed; it began as a release candidate on
6 November 2025. OAuth 2.1 is a draft. Figures such as "20-30% compute waste" and
"40% downtime cost reduction" are practitioner or vendor claims that were not
independently verified.
