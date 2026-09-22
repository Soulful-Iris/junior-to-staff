# Scope and validation

This branch adds two-path navigation, junior/senior/staff interview routes, 12 architecture concept sections, five worked design exercises, Python and TypeScript reference implementations, full-stack exercises, three AWS labs, practice rubrics, and a dated research ledger.

The original chapter diagrams remain intact. The repeated text-slide additions have been retired. Their replacements are **18 mechanism-specific native SVG animations and 18 static diagrams**, plus Mermaid diagrams. The coding entry point now provides a 12-step route and ten focused Python lessons; reference detail is on a separate page.

## Validation status

- Python algorithm tests: passed, including exhaustive small-input oracle comparisons for prefix sums, two-sum, and sliding windows.
- TypeScript runtime tests: passed under Node 24, including concurrency limits, rejected work, stale responses despite ignored cancellation, and version reconciliation.
- Queue-worker protocol tests: passed against a deterministic fake store, including concurrent duplicates, lost acknowledgement, conflicting payload, poison input, and transient failures.
- Strict TypeScript type checking: passed with `tsc --noEmit --strict`, Node types, and `allowImportingTsExtensions`.
- AWS template: passed `cfn-lint`, including SAM transformation/schema checks.
- Local link and SVG/configuration checks: passed; reproduce with `python scripts/check_learning.py`.
- Motion redesign: all 18 animations and 18 static alternatives rebuilt. Persistent labels replace rotating captions; each mechanism has its own continuous timeline. Static contact-sheet review and native timeline checks passed.
- Browser playback of this motion redesign: awaiting published-branch checks. Static rendering alone is not counted as playback verification.
- AWS resources were not deployed; live IAM, regional quotas, queue timing, alarms, and cleanup still require the learner's disposable-account validation.
- Interview research is a qualitative snapshot for March 22–September 22, 2026. See the explicit company/level gaps and excluded dates in [research](research/README.md). No statistically supported “most asked” ranking is claimed.

The full bookmark application, provider integrations, and staff extensions are learner exercises. The repository contains runnable snippets and the queue infrastructure/worker; it does not claim those exercise extensions are already built.

[Interview home](README.md)

## Production casebook addition

Five July/August 2026 incidents now have AWS implementation exercises, worked arithmetic, level-specific criteria, five distinct mechanism animations, five static alternatives, and five Mermaid diagrams. The AWS mappings and toy numbers are our teaching designs. Source facts and dates are attributed separately.
