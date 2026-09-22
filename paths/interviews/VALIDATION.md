# Scope and validation

This branch adds two-path navigation, junior/senior/staff interview routes, 12 architecture concept sections, five worked design exercises, Python and TypeScript reference implementations, full-stack exercises, three AWS labs, practice rubrics, and a dated research ledger.

All 21 original teaching chapters have two additional animations and a still storyboard. Total new assets: **57 animated SVGs and 27 still storyboards**. Shared interview mechanisms add further visuals. Animation source data and the SVG generator are committed for maintenance. Timelines depict logical teaching states, not measured AWS behavior.

## Validation status

- Python algorithm tests: passed, including exhaustive small-input oracle comparisons for prefix sums, two-sum, and sliding windows.
- TypeScript runtime tests: passed under Node 24, including concurrency limits, rejected work, stale responses despite ignored cancellation, and version reconciliation.
- Queue-worker protocol tests: passed against a deterministic fake store, including concurrent duplicates, lost acknowledgement, conflicting payload, poison input, and transient failures.
- Strict TypeScript type checking: passed with `tsc --noEmit --strict`, Node types, and `allowImportingTsExtensions`.
- AWS template: passed `cfn-lint`, including SAM transformation/schema checks.
- Local link and SVG/configuration checks: passed; reproduce with `python scripts/check_learning.py`.
- All 84 SVGs rendered to PNG; selected before/after, sequence, geometric, and still layouts were visually inspected. Text extents were checked for canvas overflow. Four-state samples were rendered for key mechanisms.
- Live browser playback and GitHub's image renderer were not verified in this environment: the browser binary download timed out. CSS uses discrete state changes and reduced-motion fallbacks; verify playback in your target reader.
- AWS resources were not deployed; live IAM, regional quotas, queue timing, alarms, and cleanup still require the learner's disposable-account validation.
- Interview research is a qualitative snapshot for March 22–September 22, 2026. See the explicit company/level gaps and excluded dates in [research](research/README.md). No statistically supported “most asked” ranking is claimed.

The full bookmark application, provider integrations, and staff extensions are learner exercises. The repository contains runnable snippets and the queue infrastructure/worker; it does not claim those exercise extensions are already built.

[Interview home](README.md)
