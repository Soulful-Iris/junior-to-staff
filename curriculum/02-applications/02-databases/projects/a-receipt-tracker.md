# Store receipts with reviewable extraction and corrections

## Application background

Employees upload receipts and accountants confirm amounts for bookkeeping. Extracted values are suggestions; a human-approved amount must remain authoritative when extraction runs again.

This is a fictional engineering scenario. The workload figures later in the page are exercise assumptions, not measured production traffic.

## Your assignment

**Deliver:** Receipt/source records, extraction attempts and a review operation that protects confirmed values from stale machine output.

Build a receipt tracker for a small business. An employee uploads a receipt for 19.99, but extraction reads 199.90. The accountant corrects it, and a later extraction retry must not overwrite the confirmed amount.

**Required behavior:** Keep source evidence, extracted suggestions and human-confirmed values as distinct records. Money is stored in integer minor units with currency. Reports use confirmed values or clearly label unreviewed entries.

The required first milestone is a working local implementation of the behavior above. The numbered implementation steps define the scope; the cloud architecture is a later extension, not something the starter has already provisioned.

## Get the code and run the supplied example

The code is in the public [junior-to-staff repository](https://github.com/Soulful-Iris/junior-to-staff). Install Git and Python 3.12+. No AWS account or Python packages are required for this first run. If you already have a checkout, use it and skip cloning.

```bash
git clone https://github.com/Soulful-Iris/junior-to-staff.git
cd junior-to-staff
python3 examples/architecture-starts/a_receipt_tracker.py
```

**Supplied file:** [`examples/architecture-starts/a_receipt_tracker.py`](https://github.com/Soulful-Iris/junior-to-staff/blob/main/examples/architecture-starts/a_receipt_tracker.py). You can also [read or download the source here](../../../../examples/architecture-starts/a_receipt_tracker.py).

This program is a **mechanism demonstration**: it runs the small scenario in one process and prints the result. It is not an HTTP service, a complete application, or an AWS deployment. A successful run demonstrates this mechanism only; it does not establish the workload or failure guarantees of the application you will build.

**Example output from the supplied run:**

Generated IDs and timestamps may differ; compare the state transitions and outcomes.

```text
Machine suggestion: 19990
Report amount: 1999 minor units; revision 2
```

### Set up your implementation workspace

Create `work/a-receipt-tracker/` in your checkout (or use a separate repository). Copy the supplied mechanism into that directory as `mechanism.py`, then extract its state transitions into functions you can call from your implementation. The record and module names below describe what you must implement; they are not a promise that files with those names already exist. Keep a `README.md` beside your implementation with its exact run commands and observed results.

## Local components and state to implement

This table names the records, interfaces or decision inputs for your deliverable. Unless a name is explicitly linked to supplied source above, it is something you create. Implement the local state transitions first, then connect the HTTP, storage or worker boundaries required by the steps.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| receipts | receipt_id,owner,source_key,source_hash | Immutable original evidence. |
| extraction_attempts | receipt_id,attempt,model,fields | Versioned machine suggestions and provenance. |
| confirmed_fields | receipt_id,revision,amount_minor,currency,actor | Human-approved reporting authority. |

## Implement the assignment

### 1. Store one receipt with evidence

Save the private original image and checksum, then create a receipt record with owner and upload time. Keep object identity immutable so an accountant can inspect exactly what supported a correction.

### 2. Add extraction as a suggestion

Record each extractor/model version, raw suggested fields and confidence/evidence location. Validate currency and decimal conversion explicitly. Low confidence, inconsistent totals or missing fields route to review rather than becoming silently accepted financial data.

### 3. Implement conditional human review

Display image, suggestion and editable confirmed fields side by side. Save against expected revision and record actor plus previous/new values. An extraction retry appends a new suggestion; it has no authority to overwrite confirmed fields.

### 4. Build useful reports and recovery

Filter reports by owner/date/currency and distinguish reviewed from pending amounts. Export integer-money-derived decimal strings without binary floating-point rounding. Restore a database backup together with referenced object versions and show that every confirmed record still has source evidence.

## Demonstrate the completed local result

| Action | Expected visible result |
|---|---|
| Run the starting program | Reporting stays at 1,999 minor units after another 19,990-unit suggestion. |
| Two reviewers save the same revision | One succeeds; the other sees a conflict with their draft preserved. |
| Restore the data | Confirmed values remain linked to the original receipt evidence. |

**Handoff:** In your implementation README, include the start command, one successful operation, the failure case above and the resulting stored state or decision. State which dependencies are simulated. Someone with a fresh checkout should be able to reproduce this without your chat history.

## Workload assumptions and capacity decisions

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 1,000 receipts/month; 2 MB average image | About 2 GB/month of source objects before versions and backups. |
| OCR suggests 199.90; human confirms 19.99 | Suggested 19,990 minor units must not replace confirmed 1,999 minor units. |
| Two reviewers may edit simultaneously | Require expected revision and preserve an audit trail of corrections. |

## Map the local implementation to AWS

**Deployment status: local only.** Running the supplied command creates no AWS resources and configures no cloud connections. The diagram is a proposed deployment of the completed application. Each box needs either a deployed runtime, a provisioned service or an explicitly external dependency.

Read the diagram by following the arrows from the entry point: application code accepts the request or event, the state owner commits it, and any worker produces the later result. The table ties those roles to code and adapter work. Multiple boxes do not imply multiple Python files already exist.

![Store receipts with reviewable extraction and corrections: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/a-receipt-tracker.svg)

Textract supplies candidate data; the review transaction establishes the confirmed financial record. Keeping those authorities separate makes correction durable across retries.

| Local responsibility | Cloud destination and role | Implementation still required |
|---|---|---|
| Local HTTP boundary or the endpoint you will add | Amazon API Gateway: receipt workflow API | Create routes and an integration; translate requests and responses and configure identity validation. |
| Python operation or worker function | AWS Lambda: receipt application | Write a Lambda event adapter, package its dependencies and give its role only the required resource actions. |
| Local file, object fixture or exported payload | Amazon S3: receipt evidence storage | Implement upload/download and metadata adapters, scoped access, object naming, retention and incomplete-upload cleanup. |
| Local extracted-field fixture | Amazon Textract: document extraction | Implement asynchronous or synchronous extraction adapters, retain source version and separate provider failures from invalid extracted data. |
| Local records and transaction boundary | Amazon Aurora PostgreSQL: review authority | Write PostgreSQL schema/migrations and a database adapter; configure credentials, connection limits and recovery. |
| Local pending-work collection | Amazon SQS: extraction queue | Publish committed job intent, consume messages and persist deduplication/ownership state; add visibility, retry and dead-letter handling. |

### Provision resources, then connect the application

| Resource or boundary | Initial configuration and reason |
|---|---|
| Evidence bucket | Private access, versioning and owner-authorized download; avoid receipt content in logs. |
| Database | Currency plus integer minor units, optimistic revision updates and immutable correction history. |
| Extraction | Bounded document size/pages, stable source identity and explicit review state after provider failure. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

A provisioned queue or table does not make the local program use it. Configure resource IDs in the deployed runtime, replace the local adapter, and replay the same successful and failing operation against that runtime. Record the deployed commit and observable result, then remove the disposable resources using your infrastructure tool.

## Extend the design after the baseline works


Add currencies with different minor-unit conventions and tax-line reconciliation. Make the currency exponent part of the conversion policy instead of multiplying every amount by 100.

<details>
<summary>Additional design reasoning and requirement changes</summary>

## Follow-up 1 · The upload is retried

**Changed requirement:** The phone loses the completion response and submits the same upload ID twice. What is counted? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Use an owner-scoped upload identity, verify object metadata and finalize idempotently. A repeated completion must not create another receipt or queue an unbounded duplicate extraction.

</details>

## Follow-up 2 · Several currencies

**Changed requirement:** The month contains USD 19.99 and JPY 500. What does the summary show? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Group totals by currency unless conversion is explicitly requested. Conversion needs rate source, rate date, rounding and audit trail; adding 1999 and 500 would combine different units.

</details>

</details>
