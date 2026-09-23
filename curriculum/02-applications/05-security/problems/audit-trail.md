# Audit trail: who changed this permission?

> **Interviewer:** “A customer reports that access to a sensitive report changed yesterday. Show who made the change, what the old and new permissions were, and whether anyone tampered with the evidence.”

**Your contract.** The app processes 2,000 permission changes/s at peak and supports 7-year retained records for this exercise. Define which fields are sensitive and which employee roles may read them. These numbers are invented; retention and legal requirements are product decisions.

| Incident | Required outcome |
|---|---|
| Permission update commits; process crashes before emitting audit event | Change and audit intent are both durable, or the permission update fails |
| Two changes happen within the same second | Unambiguous ordering per resource and actor, with server-generated identity |
| Operator changes an audit row | Detection and an immutable retained source outside the operator's write privileges |
| User asks to delete personal data | Apply the governing retention rule; document any lawful exception and restrict access |

![Best-effort logging loses evidence; a committed audit intent preserves it](../../../../assets/design-next/audit-trail-before.svg)

## Separate evidence from visibility

Commit the permission transition and an audit intent in the **same transaction**. The event records who acted, verified tenant, target, before/after references, request ID, decision time, and policy version. Never let clients supply “actor” as an authoritative field. A dispatcher can export immutable records asynchronously; a searchable index is a *projection*, so losing it must not lose the retained original. Version the envelope so future readers can interpret old records. Avoid logging raw secrets; limit reader privileges and produce a separate audit for audit access.

![AWS architecture distinguishes transactional evidence, retained archive, and query projection](../../../../assets/design-next/audit-trail-aws.svg)

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| Aurora PostgreSQL transaction | Update permission plus append outbox/audit intent atomically | DynamoDB TransactWriteItems if permissions already live in DynamoDB |
| SQS + Lambda | Transfer committed intents into a retained archive, with retry and dedupe | Kinesis when ordered high-rate streams and multiple independent consumers matter |
| S3 Object Lock | Retain versioned evidence under separately controlled permissions | Purpose-built immutable ledger if chain verification and query access justify complexity |
| Athena | Query partitioned retained events for investigation | OpenSearch projection for interactive search, never as the sole evidence source |

S3 Object Lock protects retained **object versions** under configured retention/legal hold; it does not prove a missing event was ever emitted. Reconcile the outbox and archived sequence ranges and alert on gaps.

![Sequence and verification gap make missing records visible before an incident](../../../../assets/design-next/audit-trail-detail.svg)

**Senior follow-up:** A projected audit search is 20 minutes behind during an incident. Show the operator how to query the retained source and display a truthful freshness indicator.

**Staff follow-up:** Legal hold blocks deletion for one tenant while another has an erasure request. Define record scope, separation of duties, access logs, and a test of restore and evidence export; seek counsel on actual retention obligations.

**Practice artifact:** Draw the commit and export boundaries. Trace a crash at each boundary and show whether the event exists, is discoverable, and is independently protected.

**Source boundary:** Original exercise. [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) describes the AWS retention primitive, not a blanket legal compliance guarantee. A [June 2026 Meta engineering account](https://engineering.fb.com/2026/06/25/security/privacy-aware-infrastructure-in-the-ai-native-era-an-asset-classification-case-study/) motivates provenance and policy classification; this is not a reported Meta interview question.
