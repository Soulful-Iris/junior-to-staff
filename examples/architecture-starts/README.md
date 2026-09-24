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
