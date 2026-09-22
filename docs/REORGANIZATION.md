# Reorganization record

Source: [completed curriculum at 4d4a42f](https://github.com/Soulful-Iris/junior-to-staff/tree/4d4a42facc83a18556f4eed1696dbea807fd8763).
New branch: `feature/concept-first-curriculum`.

This is an organization pass over existing material. The original branch is preserved.
The machine-readable [source map](reorganization-map.json) accounts for all 477 files,
including lessons, code, fixtures, assessments, research, and every visual.
It records original hashes so preservation can be checked after the move.

## Agreed reading order

Four groups contain familiar domain chapters. System design precedes delivery and infrastructure.
Testing, authorization and verification are practiced from the first examples; their chapters provide deeper treatment.
AI-assisted work is a method used within lessons. AI systems is a separate technical subject.
Difficulty increases inside each lesson; seniority does not select a separate reading route.

| Group | Ordered chapters |
|---|---|
| Write correct code | Problem solving and AI-assisted engineering → Data structures and algorithms |
| Build a complete application | Backend and APIs → Databases and transactions → Frontend and full-stack integration → Testing, debugging, and code review → Security |
| Design, ship, and operate the application | System design → CI/CD and progressive delivery → Infrastructure as code and AWS → Observability → Reliability and incident response |
| Scale and evolve the system | Data at scale → Performance and cost → AI systems → Migrations and recovery → Technical decisions and engineering effectiveness |

## Preservation and verification

- Retain all 42 coding problem/reference/test bundles and all 45 project briefs.
- Place each substantive document in one canonical subject location; indexes link to it.
- Keep the five reading-list stages together under one project home.
- Preserve code behavior, fixtures, original explanations, follow-ups, and visual assets.
- Replace the two-path and tier navigation with one prerequisite-based sequence.
- Keep assessment depth in one reference and progressive questions within each problem.
- Update local links, code commands, test discovery, and path-dependent helpers.
- Verify content coverage, unchanged visual/diagram content, links and runnable references.
- Carry forward the unexecuted PostgreSQL and live-AWS verification limits.

## Completed move

The first pushed checkpoint recorded the source map. The structural checkpoint moves existing lessons and rebuilds the root, four group indexes, 17 subject indexes and reference indexes. The original source branch stays at its existing commit. Seniority is an assessment depth, and AI-assisted work is a practice mode within the curriculum.

After the move:

- All 477 source files have recorded destinations; all 42 problem bundles and 45 project briefs are present.
- All 105 SVGs and all 387 Mermaid blocks match the source exactly.
- 149 other non-Markdown artifacts are byte-identical. Four test/render helpers have reviewed path changes.
- The Python runner passed 55 suites / 209 methods; its coding subset passed 42 suites / 126 methods.
- Five shared TypeScript tests, strict application type checking, the build and seven browser scenarios passed.
- The link checker resolved 2,269 relative links; the learning checker passed 240 Markdown files, 76 mechanism SVGs and lab invariants. The provenance checker passed 13 claim IDs and 16 local links.

Reproduce preservation checks with `python scripts/check_organization.py`. Source hashes and destinations are recorded in the map above. The source commit must be fetched for comparison. See [validation](VALIDATION.md) for retained execution limits and the source branch's historical visual-rendering evidence.

Navigation prose, path references and scope labels were adapted to the new sequence. No algorithm implementation, technical diagram, research claim or supplied project specification was replaced with new material.
