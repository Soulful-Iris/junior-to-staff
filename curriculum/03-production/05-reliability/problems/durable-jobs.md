# Durable jobs: the queue drained, the work did not

> **Interviewer:** “Users request a CSV export. The API returns ‘accepted’ and puts a job on a queue. A worker writes the file, then dies before acknowledging the message. A second worker receives it. Later one customer sends 40,000 exports in a minute. Make completion, retries, and overload observable.”

Assume 500 ordinary exports/minute, 20-second average processing time, and a 60-second API request timeout. The job should survive a worker crash; accepted means durably recorded, not completed.

| Input / state | Expected result |
|---|---|
| Client retries create after lost reply with same key | One logical job; stable status URL |
| Worker writes file, then crashes | Later worker checks committed output; does not send two invoices/files |
| Worker is stuck forever | Visibility expires; bounded retries and DLQ plus an operator repair path |
| 40,000 requests in 60 seconds | Admit within capacity or return an explicit overload outcome; backlog is measurable |

![A queue acknowledgement does not atomically commit the output](../../../../assets/design-practice/durable-jobs-boundary.svg)

## Keep job truth separate from message delivery

Create a durable job record keyed by customer and request identity; record ACCEPTED, RUNNING, SUCCEEDED or FAILED with attempt/lease information. Queue messages ask workers to make progress; status comes from the job store. Write outputs under a stable job-derived key and verify the expected checksum/version before marking success. A delivery may be repeated even while an earlier worker is running. Fence stale workers with a generation/version check at the authoritative status write. If a side effect cannot be idempotent, reconcile it explicitly.

![Queue grows when 500 arrivals per minute exceed 150 completions per minute](../../../../assets/design-practice/durable-jobs-deep.svg)

The bars show a trend, not a measured forecast. At the stated steady rates the backlog grows by **350 jobs each minute**; after ten minutes that is 3,500 waiting jobs before cancellations, retries, or changes in service time. An overload policy must address admitted work before the oldest age runs away.

![Completed output followed by lost acknowledgement and duplicate delivery](../../../../assets/design-practice/durable-jobs-trace.svg)

**Senior follow-up:** At 500/min and 20 seconds per job, Little's-law concurrency estimate is roughly 167 occupied worker slots for zero queue growth at steady load. If the system can run only 50 tasks, derive the queue growth and make the wait visible. Apply per-tenant fairness and a bounded retention/expiry policy.

**Staff follow-up:** A customer requests data deletion while an export waits or runs. Decide which step authorizes the read, how to revoke or cancel the output, and what audit record survives deletion without retaining private data. Show the repair path after an entire Region disappears.

**Practice artifact:** State machine, duplicate timeline, backlog calculation, cancellation test, and operations panel with oldest-job age, retry count, completion lag, and DLQ volume.

**AWS translation:** SQS standard queues can redeliver and occasionally reorder; tune visibility timeout, DLQ policy, and worker concurrency. Store authoritative jobs in DynamoDB/RDS and outputs in private S3. Read [SQS standard delivery](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html) and [visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html).

**Source note:** Constructed exercise; service delivery facts come from AWS documentation.
