# Bookmark slice validation

Recorded 2026-09-22. Python 3.12.14, SQLite 3.53.1, Node 24.19.0.

| Check | Evidence / scope |
|---|---|
| Python HTTP tests | 5 passing methods against a real local HTTP server and temporary SQLite file; concurrent conditional writers, owner isolation, tied cursor, durable idempotent replay, validation |
| Browser build | `node build.mjs` succeeds; Node strips TypeScript syntax, which does not verify types |
| Strict TypeScript | Separate `tsc -p tsconfig.json` succeeds with strict checking, DOM/ES2022 types and no emit |
| Real browser | 7 Chromium scenarios pass against actual HTTP + SQLite: A/B race, conflict/focus, old refetch, idempotent retry, ignored-abort disposal, search/empty/error/retry, and failed new search cannot reuse an old cursor |
| Query measurement | 100,000 rows, 90% Alice, timestamp ties of ten, 50-row page, 15 warm queries; before median 19.855 ms, after 0.030 ms |
| Before query plan | `SCAN bookmarks`; `USE TEMP B-TREE FOR ORDER BY` |
| After query plan | `SEARCH bookmarks USING INDEX bookmarks_owner_created_id (owner_id=? AND (created_at,id)<(?,?))` |

The query experiment checks equal results before/after the index. Timing varies by
machine and cache; this is local query evidence, not measured browser interaction
latency. Browser response fixtures use explicit promise gates. A saved screenshot was
visually inspected: the server shows Edit A, input retains Edit B, and the status
announces that the newer draft is unsaved. Tests regenerate this screenshot locally.

Independent review found and reproduced two browser/API defects before this evidence
was finalized: failed search could reuse an old query's cursor, and whitespace-padded
titles could pass validation but violate SQLite length constraints. Both were repaired
with regressions. The query/cursor state resets together; API validation counts the
exact title that is stored and rejects oversized version integers.

No AWS deployment, production login, full screen-reader evaluation, offline mutation
queue or background enrichment is claimed. The real store is SQLite; API tests do not
substitute an in-memory fake for it. Strict `tsc` checking requires an additional
TypeScript installation; the check above used a separately installed compiler, without
adding it as an application runtime dependency. Chromium used a packaged executable
with system fonts in this execution environment; normal local Playwright installation
instructions are in the README.
