# Document search: results must follow permissions

> **Interviewer:** “Employees search internal documents. A newly edited policy must become searchable within two minutes. Alice loses access to a document at noon; she must not see it at 12:01 even if the index or cache is stale. Design ingestion, search, and permission revocation.”

Assume 30 million documents, 15,000 updates/minute, and 3,000 search requests/s. Return title, snippet, and source link for the top 20. Choose whether the two-minute freshness target includes failures and define how you observe it.

| Situation | Visible result |
|---|---|
| New authorized document written at 12:00 | Searchable by 12:02 or explicit ingestion SLA breach |
| Alice's permission removed at 12:00 | No Alice-visible hit or snippet at 12:01, including cached pages |
| Indexer sees same update twice | One current document version in results |
| ACL store unavailable | Do not silently return private snippets with stale permission |

![Indexing lag and cached search hits can bypass current permission](../../../../assets/design-practice/document-search-boundary.svg)

## Give each copy a job

The source store owns document content and version; an index owns searchable tokens and perhaps embeddings; an authorization source owns current read rights. Updates flow through a durable change stream and idempotent versioned indexing. A keyword index retrieves exact terms; semantic/vector retrieval helps with paraphrases but changes ranking and cost. Merge candidates and rank them after checking authorization for **each result before exposing title or snippet**. Index-time ACL filtering alone can leave a revocation gap. Keep document and ACL versions in cache keys or revalidate at read time according to the one-minute contract.

![Twenty search hits pass through the current access decision before snippets are shown](../../../../assets/design-practice/document-search-deep.svg)

The search index can be two minutes behind and still meet its freshness target. The authorization check has the stricter one-minute revocation rule. If ACL lookup fails, the design must choose an explicit unavailable/partial response without leaking snippets.

![Document edit and permission revocation race with index refresh](../../../../assets/design-practice/document-search-trace.svg)

**Senior follow-up:** A backfill is 90% complete and new changes continue arriving. Define snapshot watermark, catch-up stream, version comparisons, cutover gates, and rollback. Measure ingestion age separately from query latency.

**Staff follow-up:** A legal deletion request covers two Regions, search index, vector index, result cache, and backups. Enumerate ownership and retention exceptions; do not claim delete is instant while replicas or signed artifacts remain. Demonstrate a revocation drill with an indexer paused.

**Practice artifact:** Source/index/ACL box diagram, edit-and-revoke timeline, freshness watermark definition, and three negative authorization tests. Explain which property is eventually consistent and which is enforced on every read.

**AWS translation:** S3/RDS/DynamoDB for source data per access pattern, event stream for changes, OpenSearch for text/vector candidates, and a separate authoritative permission decision. Technology choice does not replace read-time access checks.

**Evidence:** [Meta engineering, April 2026](https://engineering.fb.com/2026/04/21/ml-applications/modernizing-the-facebook-groups-search-to-unlock-the-power-of-community-knowledge/) describes hybrid retrieval and evaluation. This exercise's permission contract and numbers are invented; it does not claim to reproduce Meta's implementation.
