# Projects by engineering subject

The current catalog contains **49 project entries**: **40 standalone build briefs**,
**five stages of one continuing reading-list project**, and **four runnable AI
references**. Choose a brief after its chapter; its baseline and deeper follow-ups
stay together. A build brief is an assignment, not a claim that its application
is already implemented. The historical 45-brief count excludes the four later AI references.

[Continue one system through five stages](../projects/reading-list/README.md)

## Problem solving and AI-assisted engineering

- [Specify tag behavior for independent implementers](../curriculum/01-code/01-problem-solving/projects/ai-assisted/01-the-spec-that-survives-a-stranger.md)
- [Evaluate generated rate-limiter code with a simple reference](../curriculum/01-code/01-problem-solving/projects/ai-assisted/02-the-verification-you-could-not-have-written-yourself.md)
- [Build reusable AI instructions and evaluate transfer](../curriculum/01-code/01-problem-solving/projects/ai-assisted/03-the-prompt-library.md)
- [Collect evidence about changed behavior and affected callers](../curriculum/01-code/01-problem-solving/projects/ai-assisted/04-the-review-harness.md)
- [Record and revisit uncertain engineering decisions](../curriculum/01-code/01-problem-solving/projects/ai-assisted/05-the-honest-log.md)
- [Rewrite private commit history to explain a change](../curriculum/01-code/01-problem-solving/projects/change-loop/01-the-history-a-stranger-can-debug-from.md)
- [Split a tagging feature into runnable changes](../curriculum/01-code/01-problem-solving/projects/change-loop/02-the-change-small-enough-to-judge.md)
- [Demonstrate CI enforcement in a disposable repository](../curriculum/01-code/01-problem-solving/projects/change-loop/03-the-pipeline-that-can-refuse.md)
- [Automate deterministic review rules and retain human judgment](../curriculum/01-code/01-problem-solving/projects/change-loop/04-the-review-you-automate-away.md)
- [Check the combined behavior of independently valid changes](../curriculum/01-code/01-problem-solving/projects/change-loop/05-two-greens-that-make-a-red.md)

## Backend and APIs

- [Trace requests through a bookmark API](../curriculum/02-applications/01-backend/projects/01-the-request-you-can-trace-end-to-end.md)
- [Enforce a single deadline across API dependencies](../curriculum/02-applications/01-backend/projects/02-the-three-second-budget.md)
- [Build an SSRF-resistant link preview fetcher](../curriculum/02-applications/01-backend/projects/03-the-fetch-that-cannot-be-aimed-inward.md)
- [Evolve tag responses without breaking old clients](../curriculum/02-applications/01-backend/projects/04-the-api-that-does-not-break-its-callers.md)
- [Move title lookup into restartable background jobs](../curriculum/02-applications/01-backend/projects/05-the-job-that-survives-a-restart.md)
- [Build a link monitor with durable history and change alerts](../curriculum/02-applications/01-backend/projects/a-link-rot-watcher.md)
- [Build duplicate-safe form submission and CSV export](../curriculum/02-applications/01-backend/projects/a-public-form.md)

## Databases and transactions

- [Store receipts with reviewable extraction and corrections](../curriculum/02-applications/02-databases/projects/a-receipt-tracker.md)

## Frontend and full-stack integration

- [Build a shared reading-list UI with private reading state](../curriculum/02-applications/03-frontend/projects/a-shared-reading-list.md)

## Testing, debugging, and code review

- [Measure whether existing checks detect real defects](../curriculum/02-applications/04-testing/projects/01-the-suite-that-can-fail.md)
- [Protect API response types, units and compatibility](../curriculum/02-applications/04-testing/projects/02-the-contract-nobody-breaks-by-accident.md)
- [Reproduce and remove order-dependent failures](../curriculum/02-applications/04-testing/projects/03-the-flake-hunter.md)
- [Measure API capacity with controlled arrival rates](../curriculum/02-applications/04-testing/projects/04-the-load-test-that-finds-the-real-limit.md)
- [Design and run a synthetic reading-list journey](../curriculum/02-applications/04-testing/projects/05-the-test-that-runs-in-production-forever.md)

## Security

- [Prevent overlapping shifts and enforce manager access](../curriculum/02-applications/05-security/projects/a-shift-schedule.md)

## CI/CD and progressive delivery

- [Deploy from main and roll back compatible artifacts](../curriculum/03-production/02-delivery/projects/twenty-deploys-a-day.md)

## Observability

- [Diagnose a reading-list incident from existing telemetry](../curriculum/03-production/04-observability/projects/debuggable-at-three-in-the-morning.md)

## Reliability and incident response

- [Define and calculate a user-facing save SLO](../curriculum/03-production/05-reliability/projects/01-the-slo-you-would-actually-honour.md)
- [Implement burn-rate alert and incident state rules](../curriculum/03-production/05-reliability/projects/02-the-alert-that-fires-when-it-matters-and-not-before.md)
- [Bound retries across browser, API and SDK layers](../curriculum/03-production/05-reliability/projects/03-the-retry-storm-you-build-on-purpose.md)
- [Prioritize API work within a fixed capacity budget](../curriculum/03-production/05-reliability/projects/04-shedding-the-right-thing.md)
- [Recover a service trapped in expired work and retries](../curriculum/03-production/05-reliability/projects/05-the-failure-that-will-not-recover.md)
- [Keep bookmark saves usable when title lookup fails](../curriculum/03-production/05-reliability/projects/degrade-do-not-stop.md)
- [Rehearse detection, rollback and service recovery](../curriculum/03-production/05-reliability/projects/the-incident-you-caused-on-purpose.md)

## Data at scale

- [Build ingestion with bounded backlog and explicit rejection](../curriculum/04-scale-and-evolution/01-data-at-scale/projects/the-flood.md)

## AI systems

The first four projects include runnable references in `examples/ai-systems`;
the fifth is a separate build assignment. Local fixtures do not certify real-model
quality or live AWS deployment.

- [Build evidence-backed answers with permission rechecks](../curriculum/04-scale-and-evolution/03-ai-systems/projects/01-evidence-desk.md)
- [Require exact human approval before agent actions](../curriculum/04-scale-and-evolution/03-ai-systems/projects/02-approval-desk.md)
- [Route extracted invoices through validation and review](../curriculum/04-scale-and-evolution/03-ai-systems/projects/03-invoice-review.md)
- [Track AI evaluation evidence and serving versions](../curriculum/04-scale-and-evolution/03-ai-systems/projects/04-release-evidence.md)
- [Decide whether an AI feature improves a reading list](../curriculum/04-scale-and-evolution/03-ai-systems/projects/an-ai-feature-you-can-defend.md)

## Migrations and recovery

- [Migrate tags across data, clients and workers](../curriculum/04-scale-and-evolution/04-migrations/projects/the-migration-you-actually-finish.md)

## Technical decisions and engineering effectiveness

- [Build a service template with overridable defaults](../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-paved-road.md)
- [Write a data-platform policy from concrete decisions](../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-strategy-you-found-rather-than-invented.md)
- [Compare a small export script with a custom platform](../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-thing-you-decided-not-to-build.md)

## Continuing reading-list project: five build stages

These are assignments that evolve one application, not five supplied completed
applications. The bookmark editor is a bounded reference slice, not the whole
P1–P5 implementation.

| Stage | Responsibility |
|---|---|
| [Stage 1: Build the shared reading-list application](../projects/reading-list/stages/01-it-works/README.md) | Persisted ownership and one end-to-end user action |
| [Stage 2: Deploy, back up and recover the reading list](../projects/reading-list/stages/02-it-survives/README.md) | Delivery, observability and recovery |
| [Stage 3: Add durable jobs and bounded caching](../projects/reading-list/stages/03-under-load/README.md) | Measured load, overload and duplicate handling |
| [Stage 4: Add optional AI tag suggestions](../projects/reading-list/stages/04-it-reasons/README.md) | An evaluated AI feature with a safe manual path |
| [Stage 5: Migrate the reading list to stable tag IDs](../projects/reading-list/stages/05-it-changes/README.md) | Compatibility, migration, rollback and retirement |
