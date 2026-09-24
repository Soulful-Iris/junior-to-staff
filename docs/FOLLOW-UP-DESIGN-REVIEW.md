# Follow-up design review

Reviewed all 90 project and system-design briefs individually. Large changes receive a revised responsibility/failure-flow diagram, implementation boundary and concrete outcome. Smaller changes use explicit state, arithmetic, API behavior or decision evidence. Figures describe proposed extensions rather than deployed resources. Original worked references remain available.

No tests, scheduled checks or publishing gates were added to this repository. Lessons about testing and delivery still teach those subjects in their exercise environments.

| Project | Worked scenarios expanded | Focus |
|---|---:|---|
| [bookmark-service](../curriculum/03-production/01-system-design/problems/bookmark-service.md) | 1 | Revoke a shared bookmark even when its content is cached |
| [url-shortener](../curriculum/03-production/01-system-design/problems/url-shortener.md) | 1 | Allocate custom aliases across two regions |
| [api-quota](../curriculum/03-production/01-system-design/problems/api-quota.md) | 1 | Enforce one hard quota across regions |
| [checkout-payment](../curriculum/03-production/01-system-design/problems/checkout-payment.md) | 1 | Add a second payment provider without charging twice |
| [audit-trail](../curriculum/02-applications/05-security/problems/audit-trail.md) | 1 | Restore the application without rewriting audit history |
| [tenant-isolation](../curriculum/02-applications/05-security/problems/tenant-isolation.md) | 1 | Move one tenant into dedicated storage |
| [durable-jobs](../curriculum/03-production/05-reliability/problems/durable-jobs.md) | 1 | Erase data while an export worker is still running |
| [job-scheduler](../curriculum/03-production/05-reliability/problems/job-scheduler.md) | 1 | Change a recurring schedule without sending twice |
| [erasure-workflow](../curriculum/04-scale-and-evolution/04-migrations/problems/erasure-workflow.md) | 1 | Keep erased data suppressed while a downstream store is offline |
| [multi-tenant-migration](../curriculum/04-scale-and-evolution/04-migrations/problems/multi-tenant-migration.md) | 1 | Cross the point where an old schema cannot represent new writes |
| [regional-failover](../curriculum/04-scale-and-evolution/04-migrations/problems/regional-failover.md) | 1 | Choose between regional durability and regional write availability |
| [calendar-availability](../curriculum/03-production/01-system-design/problems/calendar-availability.md) | 1 | Reserve three rooms as one booking |
| [ticket-inventory](../curriculum/03-production/01-system-design/problems/ticket-inventory.md) | 1 | Claim four adjacent seats without partial success |
| [rideshare-dispatch](../curriculum/03-production/01-system-design/problems/rideshare-dispatch.md) | 1 | Keep one driver owner during a region crossing |
| [realtime-chat](../curriculum/03-production/01-system-design/problems/realtime-chat.md) | 1 | Order a chat room across regions and scale its delivery |
| [collaborative-editor](../curriculum/03-production/01-system-design/problems/collaborative-editor.md) | 1 | Merge offline edits using stable character identities |
| [notification-platform](../curriculum/03-production/01-system-design/problems/notification-platform.md) | 1 | Isolate tenant backlogs and add an explicit fallback policy |
| [webhook-delivery](../curriculum/03-production/01-system-design/problems/webhook-delivery.md) | 1 | Rotate webhook secrets while deliveries are pending |
| [food-delivery-marketplace](../curriculum/03-production/01-system-design/problems/food-delivery-marketplace.md) | 1 | Coordinate restaurant acceptance before capturing payment |
| [social-feed](../curriculum/03-production/01-system-design/problems/social-feed.md) | 1 | Revoke a creator without waiting for every feed copy to disappear |
| [news-aggregator](../curriculum/03-production/01-system-design/problems/news-aggregator.md) | 1 | Rebuild multilingual story groups without losing attribution |
| [video-processing](../curriculum/03-production/01-system-design/problems/video-processing.md) | 1 | Publish a new video generation while viewers use the old one |
| [video-streaming-platform](../curriculum/03-production/01-system-design/problems/video-streaming-platform.md) | 1 | Replace completed-video publishing with a live stream |
| [online-judge](../curriculum/03-production/01-system-design/problems/online-judge.md) | 1 | Admit a new language runtime without trusting its code |
| [api-gateway-platform](../curriculum/03-production/01-system-design/problems/api-gateway-platform.md) | 1 | Let teams own routes without editing the whole gateway |
| [event-ingestion](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/event-ingestion.md) | 1 | Correct a week of events while fresh events keep arriving |
| [ad-click-aggregator](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/ad-click-aggregator.md) | 1 | Separate revisable click reports from finalized invoices |
| [trending-counts](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/trending-counts.md) | 1 | Use approximate trends without pretending every rank is exact |
| [distributed-cache](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-cache.md) | 1 | Cache missing products without hiding a new product |
| [distributed-key-value-store](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/distributed-key-value-store.md) | 1 | Choose a cross-region replication protocol explicitly |
| [document-search](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/document-search.md) | 1 | Add vector retrieval without bypassing document permissions |
| [typeahead-search](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/typeahead-search.md) | 1 | Personalize suggestions without sharing private history |
| [file-synchronization](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/file-synchronization.md) | 1 | Move a file between folders with different permissions |
| [web-crawler](../curriculum/04-scale-and-evolution/01-data-at-scale/problems/web-crawler.md) | 1 | Migrate URL identity rules without duplicating the crawl |
| [feature-rollout](../curriculum/03-production/02-delivery/problems/feature-rollout.md) | 1 | Change experiment cohorts without mixing two experiments |
| [slow-request](../curriculum/03-production/04-observability/problems/slow-request.md) | 1 | Investigate one slow tenant without exploding metric labels |
| [metrics-platform](../curriculum/03-production/04-observability/problems/metrics-platform.md) | 1 | Budget temporary diagnostic metrics separately |
| [overload-shedding](../curriculum/04-scale-and-evolution/02-performance-cost/problems/overload-shedding.md) | 1 | Allocate scarce database work across competing products |
| [knowledge-assistant](../curriculum/04-scale-and-evolution/03-ai-systems/problems/knowledge-assistant.md) | 1 | Answer during a policy revision without mixing incompatible sources |
| [support-assistant](../curriculum/04-scale-and-evolution/03-ai-systems/problems/support-assistant.md) | 1 | Execute a multi-step approved workflow safely |
| [personalized-ranking](../curriculum/04-scale-and-evolution/03-ai-systems/problems/personalized-ranking.md) | 1 | Keep ten thousand ranking candidates out of the serving path |
| [01-the-request-you-can-trace-end-to-end](../curriculum/02-applications/01-backend/projects/01-the-request-you-can-trace-end-to-end.md) | 2 | Expanded both changed-requirement scenarios |
| [02-the-three-second-budget](../curriculum/02-applications/01-backend/projects/02-the-three-second-budget.md) | 2 | Expanded both changed-requirement scenarios |
| [03-the-fetch-that-cannot-be-aimed-inward](../curriculum/02-applications/01-backend/projects/03-the-fetch-that-cannot-be-aimed-inward.md) | 2 | Expanded both changed-requirement scenarios |
| [04-the-api-that-does-not-break-its-callers](../curriculum/02-applications/01-backend/projects/04-the-api-that-does-not-break-its-callers.md) | 2 | Expanded both changed-requirement scenarios |
| [05-the-job-that-survives-a-restart](../curriculum/02-applications/01-backend/projects/05-the-job-that-survives-a-restart.md) | 2 | Expanded both changed-requirement scenarios |
| [a-public-form](../curriculum/02-applications/01-backend/projects/a-public-form.md) | 2 | Expanded both changed-requirement scenarios |
| [a-receipt-tracker](../curriculum/02-applications/02-databases/projects/a-receipt-tracker.md) | 2 | Expanded both changed-requirement scenarios |
| [a-shared-reading-list](../curriculum/02-applications/03-frontend/projects/a-shared-reading-list.md) | 2 | Expanded both changed-requirement scenarios |
| [a-shift-schedule](../curriculum/02-applications/05-security/projects/a-shift-schedule.md) | 2 | Expanded both changed-requirement scenarios |
| [01-the-suite-that-can-fail](../curriculum/02-applications/04-testing/projects/01-the-suite-that-can-fail.md) | 2 | Expanded both changed-requirement scenarios |
| [02-the-contract-nobody-breaks-by-accident](../curriculum/02-applications/04-testing/projects/02-the-contract-nobody-breaks-by-accident.md) | 2 | Expanded both changed-requirement scenarios |
| [03-the-flake-hunter](../curriculum/02-applications/04-testing/projects/03-the-flake-hunter.md) | 2 | Expanded both changed-requirement scenarios |
| [04-the-load-test-that-finds-the-real-limit](../curriculum/02-applications/04-testing/projects/04-the-load-test-that-finds-the-real-limit.md) | 2 | Expanded both changed-requirement scenarios |
| [05-the-test-that-runs-in-production-forever](../curriculum/02-applications/04-testing/projects/05-the-test-that-runs-in-production-forever.md) | 2 | Expanded both changed-requirement scenarios |
| [twenty-deploys-a-day](../curriculum/03-production/02-delivery/projects/twenty-deploys-a-day.md) | 1 | Recover external effects after a code rollback |
| [debuggable-at-three-in-the-morning](../curriculum/03-production/04-observability/projects/debuggable-at-three-in-the-morning.md) | 2 | Expanded both changed-requirement scenarios |
| [01-the-slo-you-would-actually-honour](../curriculum/03-production/05-reliability/projects/01-the-slo-you-would-actually-honour.md) | 2 | Expanded both changed-requirement scenarios |
| [02-the-alert-that-fires-when-it-matters-and-not-before](../curriculum/03-production/05-reliability/projects/02-the-alert-that-fires-when-it-matters-and-not-before.md) | 2 | Expanded both changed-requirement scenarios |
| [03-the-retry-storm-you-build-on-purpose](../curriculum/03-production/05-reliability/projects/03-the-retry-storm-you-build-on-purpose.md) | 2 | Expanded both changed-requirement scenarios |
| [04-shedding-the-right-thing](../curriculum/03-production/05-reliability/projects/04-shedding-the-right-thing.md) | 2 | Expanded both changed-requirement scenarios |
| [05-the-failure-that-will-not-recover](../curriculum/03-production/05-reliability/projects/05-the-failure-that-will-not-recover.md) | 2 | Expanded both changed-requirement scenarios |
| [degrade-do-not-stop](../curriculum/03-production/05-reliability/projects/degrade-do-not-stop.md) | 2 | Expanded both changed-requirement scenarios |
| [the-incident-you-caused-on-purpose](../curriculum/03-production/05-reliability/projects/the-incident-you-caused-on-purpose.md) | 2 | Expanded both changed-requirement scenarios |
| [the-flood](../curriculum/04-scale-and-evolution/01-data-at-scale/projects/the-flood.md) | 2 | Expanded both changed-requirement scenarios |
| [01-evidence-desk](../curriculum/04-scale-and-evolution/03-ai-systems/projects/01-evidence-desk.md) | 1 | Revoke a source while an answer is being generated |
| [02-approval-desk](../curriculum/04-scale-and-evolution/03-ai-systems/projects/02-approval-desk.md) | 1 | Turn an approved batch into individually accountable effects |
| [03-invoice-review](../curriculum/04-scale-and-evolution/03-ai-systems/projects/03-invoice-review.md) | 1 | Assemble a multi-file invoice before extraction |
| [04-release-evidence](../curriculum/04-scale-and-evolution/03-ai-systems/projects/04-release-evidence.md) | 1 | Make release approval control the runtime that serves users |
| [an-ai-feature-you-can-defend](../curriculum/04-scale-and-evolution/03-ai-systems/projects/an-ai-feature-you-can-defend.md) | 2 | Expanded both changed-requirement scenarios |
| [the-migration-you-actually-finish](../curriculum/04-scale-and-evolution/04-migrations/projects/the-migration-you-actually-finish.md) | 2 | Expanded both changed-requirement scenarios |
| [the-paved-road](../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-paved-road.md) | 2 | Expanded both changed-requirement scenarios |
| [the-strategy-you-found-rather-than-invented](../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-strategy-you-found-rather-than-invented.md) | 2 | Expanded both changed-requirement scenarios |
| [the-thing-you-decided-not-to-build](../curriculum/04-scale-and-evolution/05-technical-decisions/projects/the-thing-you-decided-not-to-build.md) | 2 | Expanded both changed-requirement scenarios |
| [README](../projects/reading-list/stages/01-it-works/README.md) | 2 | Expanded both changed-requirement scenarios |
| [README](../projects/reading-list/stages/02-it-survives/README.md) | 2 | Expanded both changed-requirement scenarios |
| [README](../projects/reading-list/stages/03-under-load/README.md) | 2 | Expanded both changed-requirement scenarios |
| [README](../projects/reading-list/stages/04-it-reasons/README.md) | 2 | Expanded both changed-requirement scenarios |
| [README](../projects/reading-list/stages/05-it-changes/README.md) | 2 | Expanded both changed-requirement scenarios |
| [05-the-honest-log](../curriculum/01-code/01-problem-solving/projects/ai-assisted/05-the-honest-log.md) | 2 | Expanded both changed-requirement scenarios |
| [01-the-spec-that-survives-a-stranger](../curriculum/01-code/01-problem-solving/projects/ai-assisted/01-the-spec-that-survives-a-stranger.md) | 2 | Expanded both changed-requirement scenarios |
| [02-the-verification-you-could-not-have-written-yourself](../curriculum/01-code/01-problem-solving/projects/ai-assisted/02-the-verification-you-could-not-have-written-yourself.md) | 2 | Expanded both changed-requirement scenarios |
| [03-the-prompt-library](../curriculum/01-code/01-problem-solving/projects/ai-assisted/03-the-prompt-library.md) | 2 | Expanded both changed-requirement scenarios |
| [04-the-review-harness](../curriculum/01-code/01-problem-solving/projects/ai-assisted/04-the-review-harness.md) | 2 | Expanded both changed-requirement scenarios |
| [01-the-history-a-stranger-can-debug-from](../curriculum/01-code/01-problem-solving/projects/change-loop/01-the-history-a-stranger-can-debug-from.md) | 2 | Expanded both changed-requirement scenarios |
| [02-the-change-small-enough-to-judge](../curriculum/01-code/01-problem-solving/projects/change-loop/02-the-change-small-enough-to-judge.md) | 2 | Expanded both changed-requirement scenarios |
| [05-two-greens-that-make-a-red](../curriculum/01-code/01-problem-solving/projects/change-loop/05-two-greens-that-make-a-red.md) | 2 | Expanded both changed-requirement scenarios |
| [04-the-review-you-automate-away](../curriculum/01-code/01-problem-solving/projects/change-loop/04-the-review-you-automate-away.md) | 2 | Expanded both changed-requirement scenarios |
| [03-the-pipeline-that-can-refuse](../curriculum/01-code/01-problem-solving/projects/change-loop/03-the-pipeline-that-can-refuse.md) | 2 | Expanded both changed-requirement scenarios |
| [a-link-rot-watcher](../curriculum/02-applications/01-backend/projects/a-link-rot-watcher.md) | 1 | Isolate hosts when the watched URL set grows |
