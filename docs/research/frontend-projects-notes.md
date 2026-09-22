# Working notes — 03 frontend projects.md (2026-09-22)

Scratch for `tiers/01-junior/03-frontend/projects.md`. Not part of the guide.

## Verified this session (2026-09-22)

- **European Accessibility Act**: Directive (EU) 2019/882, applies since
  **28 June 2025**; applies to services sold into the EU regardless of where the
  business sits; microenterprise exemption (<10 staff, <EUR 2M turnover) is for
  services; transition for pre-existing products/services runs to 28 June 2030.
  Technical benchmark is EN 301 549 (the section README, checked 2026-09-21,
  covers the WCAG 2.2 AA / EN 301 549 v4.1.1 detail).
- **Core Web Vitals** (web.dev/articles/vitals, fetched 2026-09-22): LCP within
  2.5 s, INP 200 ms or less, CLS 0.1 or less, measured at the **75th
  percentile** of page loads, segmented mobile/desktop. All three "stable".
- **CloudFront Functions vs Lambda@Edge** (AWS docs comparison page via search,
  2026-09-22): Functions = JS only, viewer request/response only, sub-ms, no
  network or filesystem access, no request body; Lambda@Edge = Node.js/Python,
  all four events, seconds-long budgets, network access allowed, runs at
  regional edge caches not every edge location.
- **CloudWatch RUM** (docs.aws.amazon.com CloudWatch-RUM.html, fetched
  2026-09-22): app monitor generates a JS snippet; collects from a **percentage
  of real user sessions you choose**; page load, errors, sessions, device/geo
  breakdowns; 30-day retention unless copied to CloudWatch Logs; web client is
  open source (aws-rum-web).
- **Amplify Hosting vs S3+CloudFront** (AWS docs + comparisons, 2026-09-22):
  S3's own docs now recommend Amplify Hosting for static sites; Amplify is
  CloudFront underneath plus git-based deploys, branch previews, instant
  invalidation, SPA rewrites, managed certs. S3+CloudFront direct = full
  control, IaC-friendly, no build pipeline attached.

## Decisions

- No prices anywhere; free-ness stated qualitatively ("costs nothing extra",
  "the sampling percentage is the cost control"), matching the exemplar's
  hedging.
- Ordering: four states → state homes → keyboard pass → performance → hostile
  form. One screen → whole app → whole flow + law → real conditions → adversary.
- The "judge model-written UI" prompt sequence lives in project 3 (audit,
  classify by cause, fix with native elements); project 1's sequence also ends
  with a model-miss checklist since happy-path-only is the classic miss.
- SSRF note in project 5: P1's server fetches user-supplied URLs, so "validate"
  includes refusing private/metadata addresses. One sentence, junior register.
- Diagram: four mini screens (loading/empty/error/loaded), ring steps across
  them (SMIL discrete), frame one = ring on loading, loop returns to start.
  Warm accent only on the error frame. Verdict lines under each frame carry the
  "three are never designed" point; caption carries the fix.
