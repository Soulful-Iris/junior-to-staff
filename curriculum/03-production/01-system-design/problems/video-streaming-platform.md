# Video streaming: keep playback smooth at the edge

## What you are building

> Build a video platform where creators upload large files and viewers start playback on phones and TVs. A popular new video attracts a regional traffic spike. Playback needs adaptive renditions, private-content authorization and an upload path that can resume after interruption.

**Working contract:** Uploads are resumable and bounded to 20 GB. Playback returns a manifest only for a ready, authorized video. The target is p95 startup under two seconds, measured on a defined device/network cohort rather than promised for every connection.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Five million uploads/day | About 58 uploads/s average; at an assumed 500 MB mean that is 2.5 PB/day of source data before renditions. |
| 100 million viewers; 20 GB maximum upload | Maximum file size is a request bound, not the average storage assumption. |
| Two-second p95 playback start | Budget authorization, manifest fetch, first segment transfer and decoder startup independently. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/video_streaming_platform.py
```

[Open the starting code](../../../../examples/architecture-starts/video_streaming_platform.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| upload_sessions | creator,session,object_key,parts | Resumable source transfer and expiry. |
| video_catalog | video_id,owner,visibility,generation,state | Current publication and access authority. |
| playback_sessions | viewer,video,generation,expires_at | Authorized access to a specific published rendition set. |

## AWS implementation

![Video streaming: keep playback smooth at the edge: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/video-streaming-platform.svg)

The CDN carries repeated viewer bytes; the application handles identity, catalog state and publication. Keeping large transfers off API servers changes both capacity and failure behavior.

## Build it in this order

### 1. Complete one resumable upload

Create multipart upload sessions scoped to one creator and source key. Track uploaded parts and finish only the intended object. Expire abandoned sessions and multipart data; accept completion idempotently and never trust a browser’s ready flag as processing evidence.

### 2. Create adaptive playback output

Transcode a defined bitrate ladder into HLS or DASH segments. Publish an immutable versioned manifest after all required outputs are ready. Choose segment duration with startup delay, switching granularity and request overhead in mind; document the exact profiles used in your small demo.

### 3. Authorize and distribute playback

Check current visibility before issuing a short-lived playback authorization. Restrict S3 origin access so users cannot bypass the CDN policy. Document that already issued signed access may remain valid until expiry; proxy or shorten the window if immediate revocation is required.

### 4. Measure a cold and warm start

Capture time to authorization, manifest, first segment and first rendered frame. Compare a cold CDN object with a warm one and a constrained client connection. Tune the first-rendition choice and caching using the measured bottleneck, not only server response latency.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| S3 lifecycle | Abort incomplete multipart uploads and separately retain source/rendition generations according to product policy. |
| CloudFront | Restricted origin access, cache versioned segments long-term and keep authorization responses private. |
| Cost model | Estimate storage, transcode minutes and delivered GB separately; show assumptions for watch duration and average bitrate. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Only part 2 needs resuming; only the authorized viewer receives manifest access. |
| Interrupt a large upload | Resume missing parts without restarting completed transfer. |
| Request a processing video | Status is visible; no incomplete manifest is issued. |

## The next design decision

Add live streaming. Revisit segment latency, encoder failure, rolling manifest updates and origin failover; the immutable completed-video assumptions no longer cover the entire path.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 5 million daily uploads, 100 million viewers, 4K source files up to 20 GB, and playback start p95 under 2 seconds. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Partial upload | Network drops at 80% | Resume multipart upload without restarting all bytes. |
| Worker retry | Transcode task delivered twice | Stable rendition key and manifest commit prevent duplicate publication. |
| Slow connection | Bandwidth falls mid-playback | Player switches to a lower bitrate segment. |
| Private video | Owner revokes access | New segment requests fail authorization after bounded token expiry. |

## Think from the contract to the boxes

Separate the control path (upload authorization, job state, manifest) from media bytes. Transcode into aligned segments at multiple bitrates; publish a manifest only after required renditions pass validation. A CDN serves immutable segments, while signed access controls protect private content. Model the player’s buffer and bitrate adaptation, not just the upload pipeline.

**First diagram:** Show source upload, processing fan-out, manifest publish point, CDN cache, and authorization on segment fetch.

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon S3** / source + rendition objects | Durably store large media through multipart upload. | EFS only for shared POSIX scratch, not a public byte-serving path. |
| **Amazon SQS** / transcode work queue | Buffer rendition tasks and retry workers. | Step Functions for multi-stage workflows with explicit job state. |
| **AWS Elemental MediaConvert** / transcode service | Generate device/bitrate outputs without owning codec fleet. | ECS/EC2 with FFmpeg for custom filters or codec tuning. |
| **Amazon CloudFront** / media CDN | Serve cached segments near viewers. | Third-party CDN where geographic reach/contracts require it. |
| **Amazon DynamoDB** / job + manifest state | Track processing and publish only validated outputs. | Aurora for relational creator/catalog requirements. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

## Pressure-test the design

**Follow-up: A single 4K file becomes a bitrate ladder. Show the player switching from 8 Mbps to 2 Mbps while the segment timeline remains aligned.**

**Senior expectation:** A viral launch empties origin capacity. Explain CDN cache key, segment immutability, cache warming limits, origin shielding, and how auth changes affect cacheability.

**Staff expectation:** Multiple regions ingest the same creator’s content. Set source ownership, replication/egress trade-offs, takedown propagation target, and recovery behavior during an origin outage.

**Practice artifact:** Show source upload, processing fan-out, manifest publish point, CDN cache, and authorization on segment fetch. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists YouTube-style streaming reports at companies including Datadog, Snapchat and Meta; report dates are not disclosed. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/creator-viewer-paths/cm6wu2x3y0000356pl299toa0).

</details>
