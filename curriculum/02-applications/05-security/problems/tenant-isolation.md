# Tenant isolation: an ID in the URL is not authority

## What you are building

> Build a shared report-export service for 4,000 customer organizations. An administrator at Acme guesses a report ID owned by Birch. Later an Acme user loses access while their cached report and queued export still exist. Make every access path enforce the current tenant boundary.

**Working contract:** Every request has one verified tenant context. GET /reports/{id}, export creation and export download must authorize the resource under that context. Do not trust an X-Tenant-ID header independently of membership.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 4,000 organizations; 250 reports each | One million reports. A guessed global report ID is not proof of membership. |
| 2,000 reads/s peak; 200 export jobs/min | Apply tenant scope to synchronous reads, caches, queue payloads and output downloads. |
| One tenant sends 1,000 jobs/min | Set per-tenant admission and worker shares before a shared queue becomes a noisy-neighbor outage. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/tenant_isolation.py
```

[Open the starting code](../../../../examples/architecture-starts/tenant_isolation.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| membership | (subject,tenant),role,revision | Current authorization basis; revocation changes the revision. |
| reports | (tenant,report_id) | Tenant scope is part of every key and query. |
| export_jobs | tenant,requester,report_id,policy_revision | Workers reauthorize before reading; downloads reauthorize before issuing access. |

## AWS implementation

![Tenant isolation: an ID in the URL is not authority: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/tenant-isolation.svg)

A shared database can be safe when tenant scope is enforced consistently. Dedicated databases trade cost and operating complexity for a stronger isolation boundary; choose that for requirements that application-level scoping cannot satisfy.

## Build it in this order

### 1. Create trusted request context

Resolve the authenticated subject’s active organization and role. Reject a requested tenant without membership. Make repository methods require a tenant argument; avoid an unscoped get-by-ID convenience method that callers can accidentally use.

### 2. Protect cached and asynchronous reads

Key caches with tenant and object version. Check current authorization before returning cached content. A worker loads the job’s verified tenant and requester, then checks current access before generating bytes. Never accept a queue-provided object prefix as unrestricted filesystem or bucket authority.

### 3. Make export access revocable

Keep exports private. Reauthorize each new download request. A presigned URL remains usable until expiry, so choose a short documented window or proxy every download if immediate revocation is required. Revocation must also stop future regeneration from queued jobs.

### 4. Bound tenant resource use

Add per-tenant admitted-job counters and a fair scheduler. Show Acme over its limit while Birch continues making progress. Partition metrics by bounded tier or top offenders instead of creating millions of uncontrolled labels.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Aurora PostgreSQL | Tenant composite keys; row-level security as defense in depth with a non-bypass application role and transaction-scoped tenant setting. |
| S3 private exports | Tenant-prefixed immutable objects; no public bucket access; scoped worker permissions and short-lived authorized downloads. |
| SQS workers | Validate job schema and tenant relationship; bound tenant concurrency and expose backlog age per tier. |
| Identity | Validate issuer/audience and membership; identity-provider authentication does not authorize each report. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Acme cannot read Birch’s report, and revoked Ana cannot receive her warm cached report. |
| Enqueue a job then revoke access | The worker records denied/cancelled and produces no downloadable export. |
| Mix tenant ID and object ID in a request | No cross-tenant result or existence disclosure outside the chosen 404 policy. |

## The next design decision

Offer dedicated storage to a regulated customer without forking the entire application. Define tenant placement metadata, connection routing, restore scope and the migration boundary between shared and dedicated storage.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



**Your contract.** Each request carries a verified tenant identity. Files and search snippets are sensitive. Some large tenants may need stronger isolation later. This is a constructed exercise.

| Request or failure | Required result |
|---|---|
| Tenant A requests B's document ID | 404 or 403 under stated disclosure policy; no title or content leaks |
| A signed URL for A's private file expires | New download requires fresh authorization; a cached URL must not bypass it |
| Worker receives A's job ID with B's object key | Refuse the mixed-tenant work before reading bytes |
| Tenant B floods export jobs | Tenant A retains its reserved share of processing capacity |

## Name the isolation boundary

Derive tenant identity from authenticated claims and membership, never a caller-supplied URL or body field alone. Carry it in a typed request context, scope all primary and secondary indexes, object keys, cache keys, logs, and queued messages. Check membership again at the **read of sensitive content**; an old search hit cannot authorize a snippet. Write a negative test that deliberately reuses a valid ID from another tenant. Separate security isolation from noisy-neighbor capacity: both need enforcement.

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| Cognito or external OIDC | Verify caller identity and tenant membership claims | Existing identity provider with short-lived, verified tokens |
| API Gateway + application policy | Validate claims and bind tenant context to operations | ALB + ECS application when existing identity integration is already owned |
| DynamoDB scoped partition keys | Store records under tenant-prefixed keys; use conditional reads/writes | Separate tables or accounts for regulated tenants needing a stronger physical boundary |
| S3 private objects | Store tenant-scoped bytes; issue short-lived links after authorization | Separate buckets/accounts for strict billing and administrative isolation |
| SQS tenant-aware worker | Preserve tenant context and budgets in asynchronous jobs | Per-tenant queues for stronger rate isolation and operational cost |

An IAM leading-key policy can provide defense in depth for correctly mapped sessions; an application role shared by all tenants does not magically make IAM understand end-user identity. Treat signed URLs as bearer capabilities until expiry and minimize their lifetime.
A tenant prefix partitions keys; it neither authenticates a caller nor proves
current object permission. A versioned cache key is safe only when its version
comes from trusted permission state, not a caller or stale search result.

For this exercise, check permission on every sensitive read and fail unavailable
when the authority cannot be consulted. A bounded authorization cache is a
**different** contract: name its maximum age and include propagation/clock delay.
Already issued bearer downloads remain usable until their enforced expiry unless
a read-time broker or revocation-aware edge checks them. Do not promise instant
revocation from an application check that the download route bypasses.

**Drill:** warm search, snippet, cache, export and direct-download routes; pause
indexing, revoke access and repeat each read. Distinguish a storage-key test, an
IAM-session isolation test and an application ACL test. None replaces the others.

**Senior follow-up:** A bulk export includes a deleted document. Define the consistency point, authorization check at worker time, pagination snapshot rule, and deletion behavior.

**Staff follow-up:** Move one enterprise tenant into its own AWS account without changing public IDs. Plan key ownership, dual reads, rollback, cost attribution, and measurable proof that no pooled path still exposes data.

**Practice artifact:** Draw boundaries for request, index/cache, object, and queue; write five cross-tenant negative tests and one saturation test. Explain why each box must carry or recover trusted tenant context.

**Source boundary:** Original scenario. AWS's [pooled storage isolation](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pooled-storage-isolation-strategies.html) and [multitenant DynamoDB strategies](https://docs.aws.amazon.com/whitepapers/latest/multi-tenant-saas-storage-strategies/multitenancy-on-dynamodb.html) describe the alternative isolation models.

</details>
