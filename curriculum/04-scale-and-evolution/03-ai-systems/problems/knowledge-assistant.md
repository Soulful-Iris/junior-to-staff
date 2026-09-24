# Knowledge assistant: the citation that lost access

## What you are building

> Build an internal handbook assistant for a 2,000-person company. Employees ask policy questions across documents with different access rules. A document can be revoked while a generated answer is being prepared, and a retrieved page can contain instructions trying to redirect the assistant.

**Working contract:** Answer only from currently authorized source material, cite exact document/version evidence, and abstain when evidence is insufficient. Retrieved text is data, not permission to call tools or alter system behavior.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Four-second response target | Example budget: 700 ms retrieval, 2,500 ms generation, 200 ms final checks, 300 ms transport and 300 ms reserve. |
| 100,000 documents × eight chunks assumption | 800,000 chunk records before embeddings and index overhead. |
| 20 requests/s peak | At three seconds mean active time, about 60 concurrent requests; bound model and retrieval concurrency separately. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/knowledge_assistant.py
```

[Open the starting code](../../../../examples/architecture-starts/knowledge_assistant.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| source_chunks | tenant,document,version,chunk_id | Evidence with current ACL and source provenance. |
| answer_run | subject,query,source_versions,model,prompt | Reproducible answer context without unrestricted sensitive logging. |
| citations | answer_span,document_version,quoted_range | Support references that can be opened by the current caller. |

## AWS implementation

![Knowledge assistant: the citation that lost access: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/knowledge-assistant.svg)

Bedrock generates language; the application decides which documents the caller may use. OpenSearch provides candidates, while current policy and source version checks enforce the evidence boundary.

## Build it in this order

### 1. Ship authorized search first

Implement document/chunk ingestion with source versions and deletion handling. Search by tenant, then verify current access before loading chunk text. Provide a useful source-search UI before adding generation so the baseline can be compared directly.

### 2. Generate from a bounded evidence set

Pass only authorized chunks and a clear answer/abstain contract. Keep source instructions inside the data boundary. Record model/prompt/index versions and token/latency budgets. An answer containing a citation still requires checking whether that source supports the specific claim.

### 3. Recheck before returning

Track the policy revision used during retrieval and revalidate access to cited sources at finalization. If access changed, discard the affected answer and return a safe retry/abstention. Cache keys include authorization context; a warm generated-answer cache cannot bypass revocation.

### 4. Review concrete cases

Use supported, unsupported, conflicting-source and revoked-source questions. Compare useful answers and justified abstentions against the search-only baseline. Retain redacted failure examples and identify whether the fault was retrieval, authorization, generation or citation mapping.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Bedrock invocation | Explicit model configuration, request deadline and least-privilege invocation role; model output never grants tool permission. |
| Retrieval | Tenant filters plus current ACL checks; source deletions invalidate retrieval and answer-cache eligibility. |
| Telemetry | Record aggregate latency/token use and redacted evidence identities; keep sensitive document text out of general logs. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The private document is excluded; revocation during preparation withholds the answer. |
| Ask a question absent from sources | The assistant abstains and offers authorized source search. |
| Put tool instructions in a document | No tool action is authorized by the retrieved text. |

## The next design decision

Allow answers using multiple document versions during an ongoing policy update. Decide whether mixed-version evidence is acceptable and how conflicts are surfaced rather than silently resolved by the model.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



**Your contract.** Answers require verifiable citations, a 4-second response target, and no content from a document the caller cannot currently open. Retrieval quality is valuable but never grants access. This is a constructed exercise with invented numbers.

| Request | Expected answer |
|---|---|
| Authorized user asks about current policy | Grounded answer cites retrievable current document version |
| User loses document access after embedding | Neither snippets nor paraphrases derived from that document appear |
| Index sync lags for 20 minutes | Show a freshness limitation or refuse to answer where current truth is required |
| Model produces a plausible citation that does not support claim | Reject that citation/claim or mark answer uncertain; never invent evidence |

## Design the permission boundary first

Keep a versioned document catalog with current ACL and deletion state. Retrieve **candidates** from an index, then authorize every candidate and citation against the live catalog before showing titles, snippets, or generated content. Cache by caller's authorization scope and document versions, with revocation-driven invalidation or a fresh authorization gate; do not cache a final answer across users. A generation call receives only authorized excerpts. Validate claims against citations, measure unsupported answers and denial leakage in an evaluation set, and return a cautious response when retrieval or policy service is unavailable.

| AWS box | Job here | Alternative and deciding factor |
|---|---|---|
| Amazon S3 (document store) | Hold source bytes and version IDs | Existing document system as authoritative source if access changes originate there |
| Amazon Bedrock Knowledge Bases (retrieval index) | Parse, embed and retrieve candidate passages | Amazon OpenSearch Service (search index) for direct control of lexical/vector retrieval |
| Amazon DynamoDB (authorization catalog) | Hold current ACL and document state for final checks | Amazon RDS if ACL relationships and transactions fit relational queries |
| Amazon Bedrock (model inference) | Generate from authorized excerpts with citations | Existing model serving stack with comparable isolation, observability, and budget |
| Amazon CloudWatch (telemetry) | Monitor retrieval freshness, denial leaks, cost and latency | Existing platform monitoring with measurable per-stage budgets |

Bedrock Knowledge Bases synchronization after an update or deletion is an **index maintenance step**, not an instantaneous authorization revocation. Filter before model context; if uncertain about access, omit the passage. Distinguish document ingestion version, retrieval version, and ACL version in logs.

**Senior follow-up:** Retrieval runs out of time with two sources missing. Return a bounded partial answer or explicitly decline; prove that fallback never relaxes permissions.

**Staff follow-up:** The source corpus spans business units with different retention and legal policies. Define ownership of metadata, deletion propagation, offline quality evaluation, and incident response when a citation leaked.

**Practice artifact:** Draw retrieval and authorization as separate boxes, trace one revoked paragraph through cache/index/model, and define five evaluation cases with expected citations or abstentions.

**Source boundary:** Original prompt. A [June 2026 Spotify engineering article](https://engineering.atspotify.com/2026/6/encoding-your-domain-expert-the-context-layer-behind-spotifys-data-assistant) describes expert-owned data context; [Bedrock sync documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-data-source-sync-ingest.html) describes index refresh. Neither says this was a Spotify interview question.

</details>
