# Video processing: accept once, publish when ready

## What you are building

> Build upload-to-playback processing for a training company. An instructor uploads a video, processing creates several renditions, and one rendition fails. Students must never receive a manifest that points at unfinished or missing output.

**Working contract:** Create an upload session, accept a completed source object, and expose processing status. Publish a versioned playback manifest only after every required rendition is verified. Reprocessing creates a new generation without overwriting the currently published one.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 50,000 uploads/day | About 0.58 uploads/s average; the stated 300 concurrent processing jobs is a separate peak. |
| 99% of files below 2 GB ready within ten minutes | Measure from completed upload to published manifest; separate upload time and processing queue time. |
| Three renditions/source assumption | Track 150,000 rendition outcomes/day, plus retries and reprocessing generations. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/video_processing.py
```

[Open the starting code](../../../../examples/architecture-starts/video_processing.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| uploads | upload_id,owner,source_key,checksum | Authorized source object and completion evidence. |
| processing_jobs | video_id,generation,required_outputs,state | Current ownership and expected rendition set. |
| manifests | video_id,generation,object_keys | Atomic pointer to verified complete output. |

## AWS implementation

![Video processing: accept once, publish when ready: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/video-processing.svg)

Transcoding completion and publication are separate decisions. Step Functions tracks workflow progress; DynamoDB’s conditional pointer makes one complete generation visible to readers.

## Build it in this order

### 1. Accept and verify a source upload

Issue a short-lived upload authorization scoped to owner, key, size and allowed type. On completion, inspect object metadata and checksum where available. Object notifications may duplicate, so create processing identity from video and source version rather than notification delivery ID.

### 2. Run versioned processing

Store the required rendition list and generation before submission. Use MediaConvert for supported managed transcoding or a bounded container worker for custom processing. Retry failed work under the same logical job while writing immutable attempt-specific outputs.

### 3. Publish a complete manifest

Verify that each required output is present, readable and belongs to the current source generation. Commit ready plus the manifest pointer conditionally. A late success from an old generation must not replace newer output.

### 4. Expose progress and repair

Show queued, processing, failed and ready with a reason and last progress time. Track queue wait separately from encoding duration. Keep original input until the documented reprocessing/retention policy allows removal; clean orphan output after active attempts expire.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| S3 upload/output | Separate private prefixes or buckets, scoped upload authorization and lifecycle for abandoned multipart uploads. |
| MediaConvert jobs | Explicit output profiles, account concurrency/quota review, bounded retries and completion-event reconciliation. |
| Publication | Conditional generation change; CloudFront origin access restricted to the intended output bucket. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Two renditions remain processing; the third enables publication. |
| Deliver a duplicate source notification | One logical processing generation exists. |
| Finish an old generation late | The current manifest pointer is unchanged. |

## The next design decision

Allow students to keep watching during reprocessing. Keep the previous manifest valid until the new generation is complete, and define when old segments can be removed without breaking active sessions.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>

> **Interviewer:** “Creators upload 4 GB videos. Processing produces three renditions and a thumbnail. The mobile connection drops mid-upload; a transcode task times out after writing one rendition. Design the upload and watch experience without making the API hold a 4 GB request open.”

Assume 50,000 uploads/day, peak 300 concurrent uploads, and a 99% target of publish-ready within ten minutes for videos under 2 GB. The target is a hypothetical exercise requirement; clarify whether larger files have a different SLA.

| Situation | Observable result |
|---|---|
| Upload session created, bytes never arrive | Expiring session; no playable video |
| Client retries the last part | Already accepted part is not doubled in final object |
| Transcoder writes one rendition, then crashes | Retry resumes or safely replaces output; no premature READY |
| Creator revokes a published video | New playback requests denied; address old signed URLs' expiry |

![Proxying media through the API blocks workers; direct upload and durable processing isolate it](../../../../assets/design-practice/video-processing-boundary.svg)

## Design the state machine first

CREATED → UPLOADING → RECEIVED → PROCESSING → READY, with FAILED and DELETED branches. A signed upload permission is scoped to one object key and expires; it is not a proof that the final object exists or passes validation. Verify completion, size, content type, owner, and malware policy before enqueueing work. Commit READY only after all required outputs and metadata are durable. Treat object events as triggers to reconcile state, not as unique commands.

![Partial upload, duplicate work, and completion gate](../../../../assets/design-practice/video-processing-trace.svg)

## Draw the byte path and the control path

The small API path creates a session and reports status. Bytes travel directly to object storage; a worker creates renditions and publishes a manifest. Playback requests pass authorization and fetch content via CDN. Specify which objects get cleaned when an upload expires, a job fails, or a creator deletes the video. A video CDN reduces origin load; it does not itself authorize revoked users after a signed URL was issued.

## Put the AWS names on the boxes

![AWS service boxes labeled with their general architectural roles](../../../../assets/design-practice/video-processing-aws.svg)

**Why these boxes, and what changes the choice:** Direct S3 upload keeps bytes away from API workers. MediaConvert handles managed media jobs; ECS with FFmpeg fits custom codecs and scheduling. DynamoDB moves status to READY only when outputs exist, SQS can redeliver, and CloudFront distributes authorized renditions.

Read the smaller label under each service first: it names the architectural job. Then ask whether that service supplies the guarantee in the problem, or simply moves work to the next box.

**Senior follow-up:** Publishing has a ten-minute target but the processing queue waits twelve minutes. Estimate arrivals × average work and worker demand. Prioritize small jobs fairly without starving large jobs; expose P50/P99 ingest-to-ready and DLQ age, not just successful worker duration.

**Staff follow-up:** A viral launch floods playback while an owner requests removal. State revocation delay and signed URL expiry; describe a stricter authorized delivery path when immediate revocation is mandatory. Budget transcoding and egress cost under peak demand.

**Practice artifact:** Draw an upload status machine, two paths, and a failure timeline for a duplicated transcode. Explain what READY certifies and give three testable stop conditions.

**AWS translation:** Short-lived S3 multipart upload URLs, private buckets, SQS for processing triggers, ECS/MediaConvert for conversion depending on requirements, and CloudFront for delivery. Standard SQS can redeliver; use job identity and compare state before committing output. Read [SQS visibility semantics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) and [CloudFront signed URL semantics](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-creating-signed-url-canned-policy.html).

**Source note:** Original scenario with exercise numbers; cloud service capabilities are linked, not attributed interview questions.

</details>
