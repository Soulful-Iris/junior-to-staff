# Scope and validation

Recorded **2026-09-22** for `feature/concept-first-curriculum`, reorganized from `4d4a42f` on `feature/visual-learning-interview-paths`. One curriculum contains four groups and 17 subject chapters. It preserves all **42 coding problems**, **45 project briefs** (40 standalone and five stages of one continuing project), all 21 original substantive lessons, practical labs, the local browser/API/SQLite slice, five system designs, five production cases and the existing research. Supplied reference code, build briefs and independent assessment remain distinct.

## Reorganization verification

After relocation, the integrated Python run passed **55 suites / 209 test methods**; the relocated coding registry passed **42 suites / 126 methods**. The application build, strict TypeScript check, five shared TypeScript tests and all **seven real HTTP/SQLite browser scenarios** passed at their new paths.

`python scripts/check_organization.py` compares the recorded source inventory with this branch: **477 source files accounted for, 42 complete problem bundles, 45 project briefs, all 105 source SVGs byte-identical and all 387 Mermaid blocks identical**. Non-Markdown source artifacts are unchanged except four reviewed path-dependent test/render helpers. Navigation and introductory scope/link prose were edited; this is not a new audit of technical claims. The source commit must be available locally to run this check.

The visual-rendering evidence later in this document belongs to the source branch. Unchanged visual bytes and diagram source were checked here; no new full rendering pass is claimed. PostgreSQL server execution and live AWS deployment remain unverified.


The [audit acceptance tracker](AUDIT-IMPLEMENTATION.md) links the exact F1–F14 corrections and limits. The evidence below verifies reference artifacts; no actual learner performance or hiring probability is inferred. The [independent implementation review](reviews/2026-09-22-implementation-review.md) records reproduced defects, fixes, and focused acceptance evidence.

## Integrated executable check

From the repository root:

```bash
python scripts/check_curriculum.py
```

**Actual result: 55 isolated suites, 209 test methods, zero failing suites.** The coding-only subset contains **42 suites and 126 methods**. The runner starts a fresh process for each test directory so repeated module names such as `solution.py` cannot accidentally import another lesson. Each suite has a 90-second bound; intentionally broken candidate starters are excluded from reference success.

```bash
python scripts/check_curriculum.py --coding-only
python scripts/check_curriculum.py --report /tmp/curriculum-test-results.json
```

| Executed Python coverage | Result / what was checked |
|---|---|
| 42 coding problems | 126 methods: contracts, edge cases, structural invariants, brute-force/oracle comparisons where appropriate, streams/parsing and blocking-queue transitions |
| Importer + applied PR review + held-back reference | 12 + 3 + 4 methods: exact money, transport budgets, durable SQLite checkpoints/restart, malformed-page rollback and deliberately regressing PR patches |
| Bounded executor | Seven methods: admission, cancellation, exceptions, shutdown, cooperative deadline and deterministic nested-work deadlock case |
| Cache/replica/revocation | Nine methods: coalescing scope, distinct-key expiry, exception/cancellation cleanup, outage limits, replica lag and warm/cold authorization boundaries |
| Recovery/migration | 12 methods: stale-owner fencing, actual SQLite intent/outbox transaction, provider uncertainty models, version/tombstone repair, rollback, history/region and DNS boundary models |
| API contract + preserved queue worker | Five + five methods: actual application response enforcement versus configured request validation; deterministic atomic-result queue protocol |
| Reliability + evaluations | Eight + six methods: incident CSV arithmetic, alarm transitions, capacity/retries; 20 regression cases with actual mutants, failure-class metrics and budgeted fake-provider fallback |
| Browser application's real HTTP/SQLite API | Five methods: owner/version enforcement, races, pagination, replay and validation |
| PostgreSQL retry helper | **Two methods only**; these do not execute PostgreSQL isolation or EXPLAIN schedules |
| Earlier shared algorithm module | Five preserved methods, including exhaustive small-input oracle checks |

Counts are unittest methods, not the number of assertions, fixture rows or independent production scenarios. Do not add the coding-only run to the integrated total: it is a subset.

## Browser, TypeScript and measured query evidence

The [bookmark editor](../curriculum/02-applications/03-frontend/labs/bookmark-editor/README.md) runs a real local HTTP server and a temporary SQLite database. **Seven Chromium scenarios passed**: save A preserves newer draft B; 409 preserves draft/focus; stale refetch cannot regress state; lost acknowledgment replays the same key once; disposal survives ignored abort; reversed search/empty/error/keyboard retry/pagination; failed new query cannot reuse an old cursor. Explicit response gates establish ordering rather than sleep-only races. A rendered draft-preservation screenshot was inspected.

The browser build and strict TypeScript check passed separately. Node's syntax stripping does not type-check. Reproduce using the setup in the application README; from its directory:

```bash
node build.mjs
node tests/browser.mjs
```

With a separately installed TypeScript compiler, from repository root:

```bash
tsc -p curriculum/02-applications/03-frontend/labs/bookmark-editor/tsconfig.json
```

The executed environment used Python 3.12.14, SQLite 3.53.1, Node 24.19.0, TypeScript 7.0.2, Playwright and packaged Chromium. Browser executable/library setup is environment-specific. Existing standalone TypeScript runtime tests and strict checking had also passed in the earlier validation pass; they are separate from the 209-method Python total.

The [query measurement](../curriculum/02-applications/03-frontend/labs/bookmark-editor/VALIDATION.md) used 100,000 rows, skewed owner distribution, tied timestamps and equal-result assertions. Median local query time changed from **19.855 ms** with a scan/temp sort to **0.030 ms** with the matching composite index over 15 warm runs. These are recorded local measurements, not AWS performance or measured end-to-end browser latency. Substring-search cost remains a separate scaling consideration.

## PostgreSQL execution gate

**Not executed: real PostgreSQL 18 schedules and query plans.** `psql`, `postgres` and Docker were unavailable in the execution environment. The [PostgreSQL lab](../curriculum/02-applications/02-databases/labs/postgresql/README.md) supplies schema/seeds, lost-update, write-skew, serializable retry and deadlock schedules, plus small/large/skewed `EXPLAIN (ANALYZE, BUFFERS)` exercises and an assessor worksheet. Runner syntax and the two retry-helper methods passed. Official PostgreSQL documentation supports the heap/index/HOT correction; it does not substitute for running these experiments.

Complete the lab's disposable PostgreSQL 18 setup and run its documented commands to close that gate. Do not count SQLite API tests or retry-unit tests as evidence that PostgreSQL schedules ran. No predetermined planner choice or fabricated EXPLAIN timing is claimed.

## Links, provenance and diagrams

```bash
python docs/check-links.py
python scripts/check_learning.py
python docs/research/check_claims.py
```

Before reorganization, the source-branch local-link check resolved **1,460 relative links**, and its learning checker passed **219 Markdown files, 76 mechanism SVGs and lab invariants**. Both checks were rerun on the reorganized curriculum; see the [reorganization record](REORGANIZATION.md) for the new navigation counts. Local-link, source/asset and provenance-structure checks are distinct from source truth, rendered appearance and runtime tests. The claim checker validates 13 retained claim IDs and required provenance structure; exact source pages were inspected separately. Unsupported original research claims are explicitly withdrawn in the [ledger](research/claim-ledger.md).

Visual review used the repository's [Mermaid renderer](../scripts/render_mermaid.cjs) with a real browser. With its documented tooling dependencies available, reproduce into a temporary directory:

```bash
node scripts/render_mermaid.cjs /tmp/mermaid-review
```

- All **145 diagrams in the 45 project pages** rendered successfully. Thirteen contact sheets were visually reviewed, selected full-size images inspected, ten focused diagram corrections made, and affected pages rerendered; all revised diagrams received full-size review.
- The integrated **362-diagram snapshot** exposed syntax errors that were corrected and rerendered. The completed inventory contains **387 Mermaid diagrams across 219 Markdown files**. A final **37-diagram batch across 16 files** covering late coding/practical/production changes rendered and was visually reviewed. That review caught semicolons producing stray state nodes in the bookmark-editor diagram despite successful parsing; the source was corrected, all three editor blocks rerendered successfully, and the changed state diagram was inspected at full size with the stray nodes removed. An additional **12 assessment diagrams** rendered and were all visually reviewed. These are overlapping validation batches, **not numbers to sum into a unique-diagram total**.
- The 21 original subject lessons retain their illustrations and now explain a concrete initial problem, worked values, a method and changed requirements. **All 97 original SVG byte hashes are unchanged.**
- Four new mechanism-specific SVG animation/still pairs were checked in real Chromium using 43 sampled frames in the completed check, causal state assertions and visual review. Reduced-motion and print renderings matched their still alternatives pixel-for-pixel in the tested environment. This verifies the sampled mechanisms and fallbacks, not every browser.
- The earlier 34 mechanism-specific native SVG animations and 34 still alternatives retain their earlier rendering/playback evidence. The earlier browser pass sampled 28 frames per animation at commit `3a03171`, roughly 1.6–1.8 seconds per study, with changing pixels and selected geometry reviewed. That historical check is not a new full-loop or cross-browser run for this remediation.

Contact-sheet inspection establishes overall layout; selected full-size review checks detailed labels/boundaries. Neither guarantees every Markdown host's rendering. Final publication and remote commit confirmation belong to the integrated release record, not a claim that every browser was tested.

## Remaining scope boundaries

No AWS resources were deployed. Earlier `cfn-lint`/SAM transformation checks on the queue template passed, but live IAM, regional quotas, provider timing, alarms and cleanup remain disposable-account exercises. Cache/fleet quotas, provider effects, replication and region failover use explicit deterministic models where stated. A fake provider or store is not a live distributed-system test.

The local bookmark slice deliberately uses demonstration authentication and loopback hosting; production login, TLS/CSRF deployment controls, offline mutations and enrichment are excluded. Keyboard/focus/live-region scenarios were checked, not a full screen-reader usability audit. Cooperative cancellation cannot force arbitrary running user code or an already committing database transaction to stop.

Assessment candidate/assessor materials and scored examples are supplied. Public keys are procedurally held back; an already viewed variant must be replaced. Reference tests do not demonstrate an actual candidate's independent ability.

Interview evidence uses the **2025-09-22 lower boundary**, preferably **2026-03-22 or later**, and separates publication from event dates. Undated live official technical guidance has publication age unknown and is not counted as a recent interview report. The [research ledger](research/interview-evidence.md) preserves company/level/geographic gaps; no statistical “most asked” ranking or universal senior/lead threshold is claimed.

[Interview home](../practice/interview-guide.md) · [Audit acceptance](AUDIT-IMPLEMENTATION.md)
