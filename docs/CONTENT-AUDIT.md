# Learning-content audit — September 23, 2026

This records the instructional corrections from the supplied audit, originally
pinned to `61322f73a77b7653ea8f2a8d3e10f0326a524414`. The final scope is **lessons,
examples, practice contracts, diagrams and navigation**, not a new website or
production-deployment certification.

## What changed

| Area | Learning correction | Where to continue |
|---|---|---|
| Foundations and application correctness | Refactoring preserves observable contracts; test chronology is not an oracle; search boundaries, numeric overflow, input contracts, transaction safety and local draft ownership are explicit | [Curriculum](../curriculum/README.md), [coding bundles](../indexes/coding.md) |
| Design and operations | Explain the actual transaction, authorization, publication, retry and capacity boundaries rather than treating a service box, queue, cache or feature flag as a guarantee | [All design problems](../indexes/system-designs.md) |
| AI projects | Whole-field invoice validation; immutable bytes before result pointers; separate review/retry outcomes; distinct rollback history; checked candidate identity rather than a model name alone | [Route extracted invoices through validation and review](../curriculum/04-scale-and-evolution/03-ai-systems/projects/03-invoice-review.md), [Track AI evaluation evidence and serving versions](../curriculum/04-scale-and-evolution/03-ai-systems/projects/04-release-evidence.md) |
| Migrations | Test hard requirements safely, choose live exposure separately, reconcile counters and runtime evidence, distinguish intermediate benefits from retirement savings | [Lesson](../curriculum/04-scale-and-evolution/04-migrations/migration-method.md), [five exercises](../curriculum/04-scale-and-evolution/04-migrations/projects.md), [Migrate tags across data, clients and workers](../curriculum/04-scale-and-evolution/04-migrations/projects/the-migration-you-actually-finish.md) |
| Technical decisions | A supported approval may require no edits; strategy has multiple valid origins; staff roles are not universal; mentoring and sponsorship differ; timing data determines the bottleneck | [Decision writing](../curriculum/04-scale-and-evolution/05-technical-decisions/design-documents.md), [strategy](../curriculum/04-scale-and-evolution/05-technical-decisions/technical-strategy.md), [scope](../curriculum/04-scale-and-evolution/05-technical-decisions/scope-and-leverage.md), [effectiveness](../curriculum/04-scale-and-evolution/05-technical-decisions/engineering-effectiveness.md) |
| Practice and discovery | Remove contradictory requirements from linked migration/strategy exercises; distinguish assignments from runnable references; list current material rather than historical totals | [Project catalog](../indexes/projects.md), [continuing project](../projects/reading-list/README.md) |

Existing useful visual exercises were retained in the revised lessons. The
migration and strategy illustrations were corrected with their explanations;
the revised strategy SVG was rendered and inspected. This is not a claim that
every repository visual received a new full-size or cross-browser review.

## What was deliberately retained

A build brief remains an assignment unless code is explicitly supplied. The
bookmark-editor slice does not implement all five continuing-project stages.
Each coding problem keeps its supported input contract; a consistency suggestion
is not a reason to add needless production validation to every algorithm.

The [company studio](../companies/README.md), [evidence ledger](research/interview-evidence.md)
and [assessment instructions](../practice/README.md) already distinguish original
exercises, reported sightings, technical sources and public answer keys. Those
disclosures remain. No new question-frequency, hiring-probability or independent
mastery claim is made; external sources were not freshly reverified in this
learning-only finishing pass.

## Current learning inventory

Source-path checks found **18 subject chapters**, **42 coding bundles**, **49
project entries** and **41 design/architecture practice pages**. Each chapter is
reachable from the root and curriculum contents. Each current project/stage and
design page appears exactly once in its corresponding catalog.

The 49 project entries are 40 standalone build briefs, five continuing-project
stages and four runnable AI references. The 41 design pages are five longer worked
examples plus 36 focused briefs, including diagnostic and operational exercises.
These categories are not counts of deployed applications.

## Checks performed

`python scripts/check_curriculum.py --report /tmp/learning-test-results.json`
completed **57 isolated suites: 279 discovered tests, 275 executed successfully,
four skipped and zero failing suites**. The run included all 42 coding bundles,
the migration fixtures and AI reference tests. The four skips were optional
mocked AWS-adapter tests whose dependency stack was not installed in this run.

The code snapshot was acquired at `9e729984ae1b3b9f7667c489ce1bcc079d4995b9`;
these finishing changes modify instructional Markdown/SVG, not the tested Python
implementations. The local report records checkpoint
`1c211ea5347975cfa7ec4f8a740dc8453426f485`, Python 3.13.5 and SQLite 3.46.1.
AI release-demo output also confirmed promotion and rollback to release-1 at
revision 3. Counts are test methods, not assertions or proof of production safety.

Changed Markdown structure and local source links were checked. Catalog checks
compared exact source paths, not a minimum count. Real PostgreSQL sessions,
TypeScript/browser execution, live AWS, production model quality and fresh
external-source verification remain separate evidence categories.

This record describes the learning-content pass. The subsequent reader,
dependency-locking, publication and verification fixes are recorded in
[audit results](AUDIT-RESULTS.md). Neither record claims that optional live-cloud
or other external certification gates ran.
