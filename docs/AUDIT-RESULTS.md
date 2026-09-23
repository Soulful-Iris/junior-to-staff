# Audit implementation and verification

The supplied audit targets `61322f73a77b7653ea8f2a8d3e10f0326a524414`.
Corrections were delivered as separate chapter/problem commits to `main`.
The [content record](CONTENT-AUDIT.md) summarizes the instructional changes;
this record also includes the reader and verification-tool corrections.

## What to trust

A build assignment is not a finished service. An executable local reference is
not a cloud deployment. The catalog distinguishes **18 chapters, 42 coding
bundles, 49 project entries and 41 design/architecture pages**. The project entries
are 40 build assignments, five continuing-project stages and four runnable AI
references. Tests do not demonstrate a learner's independent mastery.

| Audit area | Implemented correction / retained boundary | Current check |
|---|---|---|
| PS-01–04, DS-01–04 | Contract-based review; valid unchanged approval; binary-search boundaries; numeric overflow and supported inputs | Coding references and their regression tests |
| BE-01–04, DB-01–02, FE-01–03 | Atomic decisions, cancellation limits, database-specific semantics, draft ownership and input validation | Python API tests; separate TypeScript and real HTTP/browser checks |
| TE-01–04 | Registered suites; structured execution/skip results; failing omission/empty-suite controls; historical membership separate from current correctness | Runner regressions, catalog and preservation reports |
| SE-01–04, DA-01–03 | Server-side authority, bounded authorization freshness, sandbox separation, ordering and redelivery distinctions | Focused references plus explicit design failure traces; no live security certification |
| SY-01–06, DE-01–02 | Honest artifact scope, atomic assignment/booking/replay, cache expiry, admission versus recovery and stable rollout salt | Corrected design contracts; executable rollout example; diagram review |
| IN-01–02, OB-01–04, RE-01–03, PE-01–03 | Configuration contracts, supported metrics components, causal links, dimensional bounds, retry budgets, fenced result pointers, scheduler catch-up and measured performance | Lessons and failure traces, reference suites, checked arithmetic |
| AI-01–05 | Whole-field amounts, immutable published bytes, review versus retry, distinct rollback history, evaluated-candidate identity | AI reference and mocked-adapter tests; mocks are not AWS |
| MI-01–02, TD-01–04 | Safe hard-case rehearsals, justified live pilots, staged benefits, valid approval without edits, evidence-based strategy and role expectations | Corrected lessons and linked project rubrics |
| SITE-01–08 | Atomic publication, retained old assets, validated storage, locked dependencies, render-aware cache, exact content checks and usable contextual links | Publication failure tests; reader build, links, browser and completeness checks |
| META-01–02, VIS-01 | Exact current catalogs, commit-scoped evidence, explicit inspected-versus-pending visual status | Catalog, Python, reader and visual manifests; no universal green certification |
| EVID-01–02 | Original practice versus interview sightings; unknown dates remain unknown; public assessor keys are procedural separation | Existing source/exposure disclosures retained; no fresh online verification claimed |
| IN-03 | Local/mocked status remains separate from live cloud verification | [AWS workbench](../curriculum/04-scale-and-evolution/03-ai-systems/aws-project-workbench.md); explicit account authorization required |

## Reproduce the repository checks

From the root, with the documented dependencies installed:

```sh
python scripts/check_catalog.py --report /tmp/catalog.json
python scripts/check_organization.py --report /tmp/preservation.json
python scripts/check_visuals.py --report /tmp/visuals.json
python docs/check-links.py
python scripts/check_curriculum.py --report /tmp/python-results.json
python -m unittest discover -s scripts/tests -v
```

The catalog report identifies each current source path and its hash. The Python
report records source commit, committed tree, dirty-worktree status, runtime,
commands, executed methods, skips and failures. A dirty-worktree result must not
be represented as a test of the clean recorded commit. Missing/empty required
suites fail rather than disappearing from the total.

The preservation report checks that the **472 distinct destinations of 477
historical source mappings** remain present; several navigation sources were
intentionally merged. Additions are allowed. Changed bytes are listed, not
certified correct. `check_organization.py --historical` retains the original
reorganization-only equality experiment; run it at the original reorganization
checkout with the baseline Git objects available, not as a current-content gate.

## Recorded reader run

At `63f663f49c87257c1c887167ba7bceb875dddde7`,
[Actions run 35931170248](https://github.com/Soulful-Iris/junior-to-staff/actions/runs/35931170248)
completed the reader build and tests before publication:

- 16 site regression methods passed, including publish failures and corrupt storage.
- 403 Mermaid diagrams rendered with zero failures; 320 content pages built.
- 108,958 local references across 322 HTML outputs resolved.
- 131 linked code files and all 292 source SVGs were checked in the output.
- 19 Chromium scenarios passed, including keyboard/touch prerequisite round trips.

These are the numbers for that exact run, not thresholds for future builds.
Later code, content or renderer changes require the corresponding gate again.
The generated `content-inventory.json` maps source pages to hashes, required
diagrams, linked code and assets; it rejects missing required content even when
an unrelated total remains large enough. Reference fixtures also verify that
an empty output and missing headings/assets fail.

## Visual evidence

Fifteen comparison diagrams had truncated text and vertical arrows suggesting
that independent cases were sequential. Their repaired renders were inspected
as three contact sheets; each row now reads **failure → repair** with complete
labels. The retry diagram was inspected separately at full size: three total
attempts per layer permit up to 27 leaf calls, not three retries and not a claim
of 27 simultaneous calls. The exact inspected bytes are in
[visual-review.json](visual-review.json).

`check_visuals.py` gives **every** tracked SVG and Mermaid block an explicit
status. A changed inspected SVG invalidates that inspection. Unlisted diagrams
remain `semantic-review-pending`; successful parsing/rendering and unchanged
bytes do not silently turn them into reviewed diagrams. Animated visuals retain
a separate playback/static-equivalence gate. These labels describe evidence,
not a claim that pending visuals are defective.

## Separate gates and limits

The verification workflow reports Python references, reader/browser/TypeScript,
and real PostgreSQL experiments separately, with logs tied to its commit SHA.
Read the individual job results; a completed job name alone is not evidence that
a different gate ran. The reader artifact includes the exact content/visual
manifests, rendered browser screenshots and command output.

No live AWS resources or production model evaluations were run for this audit.
Cloud IAM, regional availability, quota/cost behavior, notification destinations
and versioned-resource cleanup still require the authorized disposable-account
exercise. Do not infer them from mocks or static templates. No new hiring
probability, interview-frequency ranking, all-browser guarantee or independent
learner score is asserted. This is an implementation record, not blanket
certification that every one of the audit's optional external gates has run.
