# Typeahead: useful suggestions before the next keystroke

> **Interviewer:** “As a user types a query, show the top five likely completions. Popular prefixes are extremely hot; ranking data changes every few minutes.”

This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 80,000 queries/s, 150 ms end-to-end p99, and a 3-character minimum prefix. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Prefix `iph` | Millions of possible terms | Return top five from a bounded precomputed candidate set. |
| New trending term | Ranking changes in 2 minutes | Publish a new index version without partial mixed results. |
| One hot prefix | `a` receives 12% of queries | Cache safely and avoid recomputing full descendant scans. |
| Unicode query | User types accented text | Normalize consistently while preserving display form. |

![The failure path and repaired design for Typeahead](../../../../assets/design-interview/typeahead-search-before.svg)

## Think from the contract to the boxes

Separate offline/stream ranking from online prefix lookup. Build a versioned prefix index containing top candidates by score; online reads should be bounded by prefix and small K, not scan every completion. Keep raw popularity signals distinct from personalization. Atomically swap index versions and measure suggestion latency, zero-result rate, and freshness.

**First diagram:** Draw term events → rank build → immutable prefix index → cache → bounded query; mark index version on response.

![AWS services named with their provider-neutral architectural roles](../../../../assets/design-interview/typeahead-search-aws.svg)

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon Kinesis** / query/event stream | Collect searches and clicks for ranking updates. | SQS for simple asynchronous feedback without event-time windows. |
| **AWS Glue** / batch index build | Normalize and aggregate historical terms. | EMR when custom large-scale compute is needed. |
| **Amazon S3** / versioned index files | Hold immutable prefix snapshots for atomic publish. | DynamoDB when the complete lookup fits key-value access. |
| **Amazon ElastiCache** / prefix cache | Protect hot prefix reads with short TTL. | CloudFront for public query results where personalization is absent. |
| **Amazon ECS** / suggestion API | Serve bounded prefix lookups and ranking blend. | Lambda for sparse traffic with cold-start allowance. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

![A focused failure, capacity, or state diagram for Typeahead](../../../../assets/design-interview/typeahead-search-deep.svg)

## Pressure-test the design

**Follow-up: Prefix `iph` maps to a bounded list already ranked offline; extending to `ipho` performs a narrower lookup. Show where personalization can add or remove candidates.**

**Senior expectation:** A new vocabulary release improves quality but makes p99 worse. Split read latency by cache/index/network and roll back only the index version.

**Staff expectation:** Multiple products want one shared suggestion platform. Govern normalization, source attribution, privacy, and quality evaluation without coupling every team to one ranking model.

**Practice artifact:** Draw term events → rank build → immutable prefix index → cache → bounded query; mark index version on response. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists typeahead reports at Databricks, Meta, Expedia and Salesforce; it does not show interview dates. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/typeahead-search-system/cm7l2wazy00t7105qdvnemtwy).
