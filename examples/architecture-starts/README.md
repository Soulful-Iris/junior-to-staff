# Architecture starting code

These small Python programs demonstrate one critical mechanism per project. They do not provision AWS or supply the completed service. Open the linked project for its scenario, interfaces, build sequence, infrastructure and observable outcomes.

Run a program from the repository root with `python3 examples/architecture-starts/<name>.py`. Python 3.12+; standard library only. Each uses local fixture data.

| Project | Starting program |
|---|---|
| [Bookmark service](../../curriculum/03-production/01-system-design/problems/bookmark-service.md) | [bookmark_service.py](bookmark_service.py) |
| [URL shortener: who owns the code?](../../curriculum/03-production/01-system-design/problems/url-shortener.md) | [url_shortener.py](url_shortener.py) |
| [API quota: which request spends the last token?](../../curriculum/03-production/01-system-design/problems/api-quota.md) | [api_quota.py](api_quota.py) |
| [Checkout: paid twice, ordered once?](../../curriculum/03-production/01-system-design/problems/checkout-payment.md) | [checkout_payment.py](checkout_payment.py) |
| [Audit trail: who changed this permission?](../../curriculum/02-applications/05-security/problems/audit-trail.md) | [audit_trail.py](audit_trail.py) |
| [Tenant isolation: an ID in the URL is not authority](../../curriculum/02-applications/05-security/problems/tenant-isolation.md) | [tenant_isolation.py](tenant_isolation.py) |
| [Durable jobs: the queue drained, the work did not](../../curriculum/03-production/05-reliability/problems/durable-jobs.md) | [durable_jobs.py](durable_jobs.py) |
| [Job scheduler: fire once on time, recover after a crash](../../curriculum/03-production/05-reliability/problems/job-scheduler.md) | [job_scheduler.py](job_scheduler.py) |
| [Data erasure: one request, nine copies](../../curriculum/04-scale-and-evolution/04-migrations/problems/erasure-workflow.md) | [erasure_workflow.py](erasure_workflow.py) |
| [Multi-tenant migration](../../curriculum/04-scale-and-evolution/04-migrations/problems/multi-tenant-migration.md) | [multi_tenant_migration.py](multi_tenant_migration.py) |
| [Regional failover: which acknowledged write survives?](../../curriculum/04-scale-and-evolution/04-migrations/problems/regional-failover.md) | [regional_failover.py](regional_failover.py) |
| [Calendar: reserve time without hiding conflicts](../../curriculum/03-production/01-system-design/problems/calendar-availability.md) | [calendar_availability.py](calendar_availability.py) |
| [Ticket inventory: one seat, two buyers](../../curriculum/03-production/01-system-design/problems/ticket-inventory.md) | [ticket_inventory.py](ticket_inventory.py) |
| [Ride sharing: one driver, one accepted ride](../../curriculum/03-production/01-system-design/problems/rideshare-dispatch.md) | [rideshare_dispatch.py](rideshare_dispatch.py) |
| [Realtime chat: reconnect without losing the conversation](../../curriculum/03-production/01-system-design/problems/realtime-chat.md) | [realtime_chat.py](realtime_chat.py) |
| [Collaborative editor: two people edit the same sentence](../../curriculum/03-production/01-system-design/problems/collaborative-editor.md) | [collaborative_editor.py](collaborative_editor.py) |
| [Notification platform](../../curriculum/03-production/01-system-design/problems/notification-platform.md) | [notification_platform.py](notification_platform.py) |
| [Webhook delivery: a timeout is not a rejection](../../curriculum/03-production/01-system-design/problems/webhook-delivery.md) | [webhook_delivery.py](webhook_delivery.py) |
| [Food delivery: quote the right nearby options](../../curriculum/03-production/01-system-design/problems/food-delivery-marketplace.md) | [food_delivery_marketplace.py](food_delivery_marketplace.py) |
| [Social feed: a popular author changes the shape](../../curriculum/03-production/01-system-design/problems/social-feed.md) | [social_feed.py](social_feed.py) |
| [News aggregator: freshness without a write storm](../../curriculum/03-production/01-system-design/problems/news-aggregator.md) | [news_aggregator.py](news_aggregator.py) |
| [Video processing: accept once, publish when ready](../../curriculum/03-production/01-system-design/problems/video-processing.md) | [video_processing.py](video_processing.py) |
| [Video streaming: keep playback smooth at the edge](../../curriculum/03-production/01-system-design/problems/video-streaming-platform.md) | [video_streaming_platform.py](video_streaming_platform.py) |
| [Online judge: untrusted code gets a small box](../../curriculum/03-production/01-system-design/problems/online-judge.md) | [online_judge.py](online_judge.py) |
| [API gateway: route safely across many teams](../../curriculum/03-production/01-system-design/problems/api-gateway-platform.md) | [api_gateway_platform.py](api_gateway_platform.py) |
| [Event ingestion: change a schema without losing yesterday](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/event-ingestion.md) | [event_ingestion.py](event_ingestion.py) |
| [Ad click aggregator: count late events once](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/ad-click-aggregator.md) | [ad_click_aggregator.py](ad_click_aggregator.py) |
| [Trending counts: the spike that breaks one partition](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/trending-counts.md) | [trending_counts.py](trending_counts.py) |
| [Distributed cache: recover when one shard leaves](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-cache.md) | [distributed_cache.py](distributed_cache.py) |
| [Key-value store: acknowledge only what survives](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-key-value-store.md) | [distributed_key_value_store.py](distributed_key_value_store.py) |
| [Document search: results must follow permissions](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/document-search.md) | [document_search.py](document_search.py) |
| [Typeahead: useful suggestions before the next keystroke](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/typeahead-search.md) | [typeahead_search.py](typeahead_search.py) |
| [File synchronization](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/file-synchronization.md) | [file_synchronization.py](file_synchronization.py) |
| [Web crawler: be fast without attacking one site](../../curriculum/04-scale-and-evolution/01-data-at-scale/problems/web-crawler.md) | [web_crawler.py](web_crawler.py) |
| [Feature rollout: the switch that failed after 100%](../../curriculum/03-production/02-delivery/problems/feature-rollout.md) | [feature_rollout.py](feature_rollout.py) |
| [Slow request: the healthy average hid a timeout](../../curriculum/03-production/04-observability/problems/slow-request.md) | [slow_request.py](slow_request.py) |
| [Metrics platform: query the right time window](../../curriculum/03-production/04-observability/problems/metrics-platform.md) | [metrics_platform.py](metrics_platform.py) |
| [Overload: protect the requests that can finish](../../curriculum/04-scale-and-evolution/02-performance-cost/problems/overload-shedding.md) | [overload_shedding.py](overload_shedding.py) |
| [Knowledge assistant: the citation that lost access](../../curriculum/04-scale-and-evolution/03-ai-systems/problems/knowledge-assistant.md) | [knowledge_assistant.py](knowledge_assistant.py) |
| [Support assistant](../../curriculum/04-scale-and-evolution/03-ai-systems/problems/support-assistant.md) | [support_assistant.py](support_assistant.py) |
| [Personalized ranking: low latency and evidence of quality](../../curriculum/04-scale-and-evolution/03-ai-systems/problems/personalized-ranking.md) | [personalized_ranking.py](personalized_ranking.py) |
| [1. The request you can trace end to end](../../curriculum/02-applications/01-backend/projects/01-the-request-you-can-trace-end-to-end.md) | [01_the_request_you_can_trace_end_to_end.py](01_the_request_you_can_trace_end_to_end.py) |
| [2. The three-second budget](../../curriculum/02-applications/01-backend/projects/02-the-three-second-budget.md) | [02_the_three_second_budget.py](02_the_three_second_budget.py) |
| [3. The fetch that cannot be aimed inward](../../curriculum/02-applications/01-backend/projects/03-the-fetch-that-cannot-be-aimed-inward.md) | [03_the_fetch_that_cannot_be_aimed_inward.py](03_the_fetch_that_cannot_be_aimed_inward.py) |
| [4. The API that does not break its callers](../../curriculum/02-applications/01-backend/projects/04-the-api-that-does-not-break-its-callers.md) | [04_the_api_that_does_not_break_its_callers.py](04_the_api_that_does_not_break_its_callers.py) |
| [5. The job that survives a restart](../../curriculum/02-applications/01-backend/projects/05-the-job-that-survives-a-restart.md) | [05_the_job_that_survives_a_restart.py](05_the_job_that_survives_a_restart.py) |
| [5. A public form](../../curriculum/02-applications/01-backend/projects/a-public-form.md) | [a_public_form.py](a_public_form.py) |
| [2. A receipt tracker](../../curriculum/02-applications/02-databases/projects/a-receipt-tracker.md) | [a_receipt_tracker.py](a_receipt_tracker.py) |
| [1. A shared reading list](../../curriculum/02-applications/03-frontend/projects/a-shared-reading-list.md) | [a_shared_reading_list.py](a_shared_reading_list.py) |
| [3. A shift schedule](../../curriculum/02-applications/05-security/projects/a-shift-schedule.md) | [a_shift_schedule.py](a_shift_schedule.py) |
