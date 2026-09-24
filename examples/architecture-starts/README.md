# Architecture starting code

These files are small, runnable **mechanism demonstrations**, not complete services. Each corresponding project page explains the application, the local assignment and the code/adapters needed to reach its AWS diagram. Running one of these programs creates no cloud resources.

For an actual HTTP application to extend, start with the [reading-list API and request walkthrough](../reading-list-starter/README.md). For the durable link-monitor CLI, use the [link-watcher reference](../link-watcher/README.md). The [AI workflow code on GitHub](https://github.com/Soulful-Iris/junior-to-staff/tree/main/examples/ai-systems) contains four local workflows with fixture providers.

Download the [repository](https://github.com/Soulful-Iris/junior-to-staff) once:

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
```

Then run the command in the project's page. Python 3.12+ is sufficient for these standard-library demonstrations. The printed output is a first observation. Completing the assignment requires the additional implementation and failure walkthroughs named on that page.


| Project | Starting program |
|---|---|
| [Build a private bookmark API with ownership and version checks](../../curriculum/03-production/01-system-design/problems/bookmark-service.md) | [bookmark_service.py](bookmark_service.py) |
| [Build short links with unique aliases and safe redirects](../../curriculum/03-production/01-system-design/problems/url-shortener.md) | [url_shortener.py](url_shortener.py) |
| [Enforce API quotas across concurrent gateways](../../curriculum/03-production/01-system-design/problems/api-quota.md) | [api_quota.py](api_quota.py) |
| [Build checkout that recovers from uncertain payments](../../curriculum/03-production/01-system-design/problems/checkout-payment.md) | [checkout_payment.py](checkout_payment.py) |
| [Record permission changes with durable audit evidence](../../curriculum/02-applications/05-security/problems/audit-trail.md) | [audit_trail.py](audit_trail.py) |
| [Enforce tenant access in APIs, caches and exports](../../curriculum/02-applications/05-security/problems/tenant-isolation.md) | [tenant_isolation.py](tenant_isolation.py) |
| [Build restartable CSV export jobs](../../curriculum/03-production/05-reliability/problems/durable-jobs.md) | [durable_jobs.py](durable_jobs.py) |
| [Schedule reports without duplicate logical runs](../../curriculum/03-production/05-reliability/problems/job-scheduler.md) | [job_scheduler.py](job_scheduler.py) |
| [Erase account data across stores and in-flight work](../../curriculum/04-scale-and-evolution/04-migrations/problems/erasure-workflow.md) | [erasure_workflow.py](erasure_workflow.py) |
| [Migrate tenant data with a resumable backfill](../../curriculum/04-scale-and-evolution/04-migrations/problems/multi-tenant-migration.md) | [multi_tenant_migration.py](multi_tenant_migration.py) |
| [Design and rehearse regional write failover](../../curriculum/04-scale-and-evolution/04-migrations/problems/regional-failover.md) | [regional_failover.py](regional_failover.py) |
| [Reserve rooms and handle recurring local times](../../curriculum/03-production/01-system-design/problems/calendar-availability.md) | [calendar_availability.py](calendar_availability.py) |
| [Reserve concert seats with expiring holds](../../curriculum/03-production/01-system-design/problems/ticket-inventory.md) | [ticket_inventory.py](ticket_inventory.py) |
| [Assign drivers safely with expiring offers](../../curriculum/03-production/01-system-design/problems/rideshare-dispatch.md) | [rideshare_dispatch.py](rideshare_dispatch.py) |
| [Build chat with durable messages and reconnect recovery](../../curriculum/03-production/01-system-design/problems/realtime-chat.md) | [realtime_chat.py](realtime_chat.py) |
| [Build a versioned shared document editor](../../curriculum/03-production/01-system-design/problems/collaborative-editor.md) | [collaborative_editor.py](collaborative_editor.py) |
| [Deliver notifications with preferences and priority](../../curriculum/03-production/01-system-design/problems/notification-platform.md) | [notification_platform.py](notification_platform.py) |
| [Deliver signed webhooks with retries and replay](../../curriculum/03-production/01-system-design/problems/webhook-delivery.md) | [webhook_delivery.py](webhook_delivery.py) |
| [Build restaurant discovery and authoritative checkout](../../curriculum/03-production/01-system-design/problems/food-delivery-marketplace.md) | [food_delivery_marketplace.py](food_delivery_marketplace.py) |
| [Build a following feed with current access checks](../../curriculum/03-production/01-system-design/problems/social-feed.md) | [social_feed.py](social_feed.py) |
| [Collect news feeds with freshness and deduplication](../../curriculum/03-production/01-system-design/problems/news-aggregator.md) | [news_aggregator.py](news_aggregator.py) |
| [Process uploads and publish complete video renditions](../../curriculum/03-production/01-system-design/problems/video-processing.md) | [video_processing.py](video_processing.py) |
| [Build resumable uploads and authorized video playback](../../curriculum/03-production/01-system-design/problems/video-streaming-platform.md) | [video_streaming_platform.py](video_streaming_platform.py) |
| [Run programming submissions inside isolated workers](../../curriculum/03-production/01-system-design/problems/online-judge.md) | [online_judge.py](online_judge.py) |
| [Build versioned API routing and admission policies](../../curriculum/03-production/01-system-design/problems/api-gateway-platform.md) | [api_gateway_platform.py](api_gateway_platform.py) |
| [Ingest events with durable acceptance and replay](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/event-ingestion.md) | [event_ingestion.py](event_ingestion.py) |
| [Aggregate click events with late arrivals and reconciliation](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/ad-click-aggregator.md) | [ad_click_aggregator.py](ad_click_aggregator.py) |
| [Compute trending topics from duplicate and late events](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/trending-counts.md) | [trending_counts.py](trending_counts.py) |
| [Protect a database with versioned cache fills](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-cache.md) | [distributed_cache.py](distributed_cache.py) |
| [Implement replicated writes and fenced leadership](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-key-value-store.md) | [distributed_key_value_store.py](distributed_key_value_store.py) |
| [Search documents without leaking revoked content](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/document-search.md) | [document_search.py](document_search.py) |
| [Build typeahead with stale-response protection](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/typeahead-search.md) | [typeahead_search.py](typeahead_search.py) |
| [Synchronize files with resumable uploads and conflicts](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/file-synchronization.md) | [file_synchronization.py](file_synchronization.py) |
| [Build a durable crawler with per-host limits](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/web-crawler.md) | [web_crawler.py](web_crawler.py) |
| [Release invoice changes with stable cohorts and rollback](../../curriculum/03-production/02-delivery/problems/feature-rollout.md) | [feature_rollout.py](feature_rollout.py) |
| [Find database-pool waiting in slow API requests](../../curriculum/03-production/04-observability/problems/slow-request.md) | [slow_request.py](slow_request.py) |
| [Ingest and query metrics with bounded cardinality](../../curriculum/03-production/04-observability/problems/metrics-platform.md) | [metrics_platform.py](metrics_platform.py) |
| [Reject excess API work before queues grow without bound](../../curriculum/04-scale-and-evolution/02-performance-cost/problems/overload-shedding.md) | [overload_shedding.py](overload_shedding.py) |
| [Build a document assistant with current permissions](../../curriculum/04-scale-and-evolution/03-ai-systems/problems/knowledge-assistant.md) | [knowledge_assistant.py](knowledge_assistant.py) |
| [Draft support replies without granting tool authority](../../curriculum/04-scale-and-evolution/03-ai-systems/problems/support-assistant.md) | [support_assistant.py](support_assistant.py) |
| [Serve recommendations with safe fallback ranking](../../curriculum/04-scale-and-evolution/03-ai-systems/problems/personalized-ranking.md) | [personalized_ranking.py](personalized_ranking.py) |
| [Trace requests through a bookmark API](../../curriculum/02-applications/01-backend/projects/01-the-request-you-can-trace-end-to-end.md) | [01_the_request_you_can_trace_end_to_end.py](01_the_request_you_can_trace_end_to_end.py) |
| [Enforce a single deadline across API dependencies](../../curriculum/02-applications/01-backend/projects/02-the-three-second-budget.md) | [02_the_three_second_budget.py](02_the_three_second_budget.py) |
| [Build an SSRF-resistant link preview fetcher](../../curriculum/02-applications/01-backend/projects/03-the-fetch-that-cannot-be-aimed-inward.md) | [03_the_fetch_that_cannot_be_aimed_inward.py](03_the_fetch_that_cannot_be_aimed_inward.py) |
| [Evolve tag responses without breaking old clients](../../curriculum/02-applications/01-backend/projects/04-the-api-that-does-not-break-its-callers.md) | [04_the_api_that_does_not_break_its_callers.py](04_the_api_that_does_not_break_its_callers.py) |
| [Move title lookup into restartable background jobs](../../curriculum/02-applications/01-backend/projects/05-the-job-that-survives-a-restart.md) | [05_the_job_that_survives_a_restart.py](05_the_job_that_survives_a_restart.py) |
| [Build duplicate-safe form submission and CSV export](../../curriculum/02-applications/01-backend/projects/a-public-form.md) | [a_public_form.py](a_public_form.py) |
| [Store receipts with reviewable extraction and corrections](../../curriculum/02-applications/02-databases/projects/a-receipt-tracker.md) | [a_receipt_tracker.py](a_receipt_tracker.py) |
| [Build a shared reading-list UI with private reading state](../../curriculum/02-applications/03-frontend/projects/a-shared-reading-list.md) | [a_shared_reading_list.py](a_shared_reading_list.py) |
| [Prevent overlapping shifts and enforce manager access](../../curriculum/02-applications/05-security/projects/a-shift-schedule.md) | [a_shift_schedule.py](a_shift_schedule.py) |
| [Measure whether existing checks detect real defects](../../curriculum/02-applications/04-testing/projects/01-the-suite-that-can-fail.md) | [01_the_suite_that_can_fail.py](01_the_suite_that_can_fail.py) |
| [Protect API response types, units and compatibility](../../curriculum/02-applications/04-testing/projects/02-the-contract-nobody-breaks-by-accident.md) | [02_the_contract_nobody_breaks_by_accident.py](02_the_contract_nobody_breaks_by_accident.py) |
| [Reproduce and remove order-dependent failures](../../curriculum/02-applications/04-testing/projects/03-the-flake-hunter.md) | [03_the_flake_hunter.py](03_the_flake_hunter.py) |
| [Measure API capacity with controlled arrival rates](../../curriculum/02-applications/04-testing/projects/04-the-load-test-that-finds-the-real-limit.md) | [04_the_load_test_that_finds_the_real_limit.py](04_the_load_test_that_finds_the_real_limit.py) |
| [Design and run a synthetic reading-list journey](../../curriculum/02-applications/04-testing/projects/05-the-test-that-runs-in-production-forever.md) | [05_the_test_that_runs_in_production_forever.py](05_the_test_that_runs_in_production_forever.py) |
| [Deploy from main and roll back compatible artifacts](../../curriculum/03-production/02-delivery/projects/twenty-deploys-a-day.md) | [twenty_deploys_a_day.py](twenty_deploys_a_day.py) |
| [Diagnose a reading-list incident from existing telemetry](../../curriculum/03-production/04-observability/projects/debuggable-at-three-in-the-morning.md) | [debuggable_at_three_in_the_morning.py](debuggable_at_three_in_the_morning.py) |
| [Define and calculate a user-facing save SLO](../../curriculum/03-production/05-reliability/projects/01-the-slo-you-would-actually-honour.md) | [01_the_slo_you_would_actually_honour.py](01_the_slo_you_would_actually_honour.py) |
| [Implement burn-rate alert and incident state rules](../../curriculum/03-production/05-reliability/projects/02-the-alert-that-fires-when-it-matters-and-not-before.md) | [02_the_alert_that_fires_when_it_matters_and_not_before.py](02_the_alert_that_fires_when_it_matters_and_not_before.py) |
| [Bound retries across browser, API and SDK layers](../../curriculum/03-production/05-reliability/projects/03-the-retry-storm-you-build-on-purpose.md) | [03_the_retry_storm_you_build_on_purpose.py](03_the_retry_storm_you_build_on_purpose.py) |
| [Prioritize API work within a fixed capacity budget](../../curriculum/03-production/05-reliability/projects/04-shedding-the-right-thing.md) | [04_shedding_the_right_thing.py](04_shedding_the_right_thing.py) |
| [Recover a service trapped in expired work and retries](../../curriculum/03-production/05-reliability/projects/05-the-failure-that-will-not-recover.md) | [05_the_failure_that_will_not_recover.py](05_the_failure_that_will_not_recover.py) |
| [Keep bookmark saves usable when title lookup fails](../../curriculum/03-production/05-reliability/projects/degrade-do-not-stop.md) | [degrade_do_not_stop.py](degrade_do_not_stop.py) |
| [Rehearse detection, rollback and service recovery](../../curriculum/03-production/05-reliability/projects/the-incident-you-caused-on-purpose.md) | [the_incident_you_caused_on_purpose.py](the_incident_you_caused_on_purpose.py) |
| [Build ingestion with bounded backlog and explicit rejection](../../curriculum/04-scale-and-evolution/01-data-at-scale/projects/the-flood.md) | [the_flood.py](the_flood.py) |
| [Decide whether an AI feature improves a reading list](../../curriculum/04-scale-and-evolution/03-ai-systems/projects/an-ai-feature-you-can-defend.md) | [an_ai_feature_you_can_defend.py](an_ai_feature_you_can_defend.py) |
| [Migrate tags across data, clients and workers](../../curriculum/04-scale-and-evolution/04-migrations/projects/the-migration-you-actually-finish.md) | [the_migration_you_actually_finish.py](the_migration_you_actually_finish.py) |
| [Build a service template with overridable defaults](../../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-paved-road.md) | [the_paved_road.py](the_paved_road.py) |
| [Write a data-platform policy from concrete decisions](../../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-strategy-you-found-rather-than-invented.md) | [the_strategy_you_found_rather_than_invented.py](the_strategy_you_found_rather_than_invented.py) |
| [Compare a small export script with a custom platform](../../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-thing-you-decided-not-to-build.md) | [the_thing_you_decided_not_to_build.py](the_thing_you_decided_not_to_build.py) |
| [Stage 1: Build the shared reading-list application](../../projects/reading-list/stages/01-it-works/README.md) | [reading_list_it_works.py](reading_list_it_works.py) |
| [Stage 2: Deploy, back up and recover the reading list](../../projects/reading-list/stages/02-it-survives/README.md) | [reading_list_it_survives.py](reading_list_it_survives.py) |
| [Stage 3: Add durable jobs and bounded caching](../../projects/reading-list/stages/03-under-load/README.md) | [reading_list_under_load.py](reading_list_under_load.py) |
| [Stage 4: Add optional AI tag suggestions](../../projects/reading-list/stages/04-it-reasons/README.md) | [reading_list_it_reasons.py](reading_list_it_reasons.py) |
| [Stage 5: Migrate the reading list to stable tag IDs](../../projects/reading-list/stages/05-it-changes/README.md) | [reading_list_it_changes.py](reading_list_it_changes.py) |

## AWS foundation

Use the [provisioning and wiring guide](infra/README.md) for a deployable state-table, queue and private-object foundation, concrete IAM responsibilities, inspection commands and cleanup. It states exactly which application adapters remain to build.

## Existing complete AI workflows

The four AI project pages retain their existing local reference implementation:

```bash
python3 examples/ai-systems/demo.py assistant
python3 examples/ai-systems/demo.py agent
python3 examples/ai-systems/demo.py extraction
python3 examples/ai-systems/demo.py evaluation
```

These commands use local fixtures and temporary storage. They do not invoke paid model APIs or deploy cloud resources.
