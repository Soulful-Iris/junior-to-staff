# Key-value store: acknowledge only what survives

## What you are building

> Build a small replicated key-value store to understand the durability boundary behind a managed database. A leader acknowledges a write, crashes, and later returns with stale state. The replacement leader must not lose acknowledged data or accept writes from the old term.

**Working contract:** PUT /keys/{key} accepts a request identity and optional expected version. GET exposes a chosen consistency mode. The first milestone is one durable local log; the replicated milestone uses a specified consensus protocol with durable terms and a committed-log rule.

## Workload and the decisions it changes

These are constructed exercise assumptions. The stated workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| Two million operations/s target; 300 nodes | About 6,667 operations/s/node average before replication and skew; the local starter makes no throughput claim. |
| Three replicas per partition | A majority is two, but quorum arithmetic alone does not define leader election, log recovery or linearizable reads. |
| 99.99% availability objective | Roughly 4.32 minutes unavailable in a 30-day month; define which failed/slow requests count. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/distributed_key_value_store.py
```

[Open the starting code](../../../../examples/architecture-starts/distributed_key_value_store.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| log_entries | partition,index,term,request_id,command | Durable ordered commands before state application. |
| replica_state | current_term,voted_for,commit_index | Persisted protocol state with explicit recovery rules. |
| key_state | key,value,version | Materialized committed log; snapshots include last applied index. |

## AWS implementation

![Key-value store: acknowledge only what survives: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/distributed-key-value-store.svg)

This project intentionally uses EC2/EBS because building the storage mechanism is the assignment. DynamoDB is the practical alternative when the goal is to use a durable key-value service rather than implement one.

## Build it in this order

### 1. Make one node recoverable

Append length/checksummed records, flush according to the acknowledgement policy and replay committed records on restart. Handle a truncated final record explicitly. Add snapshots with a last included index, and retain log segments until snapshot durability is established.

### 2. Specify replication before adding nodes

Use a documented Raft implementation or implement its full term, election, log-matching and commitment rules as the learning objective. A leader sends ordered entries, followers durably record them, and success waits for the required committed majority. Never treat two arbitrary copies as proof of the protocol.

### 3. Define read and retry semantics

Deduplicate client operations at the replicated state-machine boundary. Linearizable reads require proof of current leadership and applied commit position; follower reads may be stale and must be labeled as such. Conditional writes compare the committed key version.

### 4. Partition and rebalance deliberately

Route keys to versioned partition ownership. Move snapshots plus log tails, then transfer authority under a fenced configuration change. Measure the hottest partition and replication cost before deriving node count from average operations.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Replica placement | Put a partition’s replicas in distinct AZs and state which correlated failures the design tolerates. |
| Storage | Benchmark durable flush latency and recovery time; local process success is not proof of replicated durability. |
| Membership | Use the consensus implementation’s safe reconfiguration mechanism; do not replace a majority simultaneously. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

For concrete provisioning commands, configuration wiring and cleanup, use the [AWS foundation guide](../../../../examples/architecture-starts/infra/README.md). It includes a deployable table/queue/object-storage foundation and explains which application and service adapters you still implement.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | The value is recovered from the flushed local log. |
| Kill the replicated leader after acknowledgement | The new leader retains every acknowledged command under the chosen protocol. |
| Resume the old leader | Its stale term cannot commit writes. |

## The next design decision

Add multi-region replicas. Quantify the write-latency cost of cross-region quorum and state the availability behavior under partition. Do not promise both independent regional writes and single-copy semantics without a protocol that actually provides them.

<details>
<summary>Additional design cases, alternatives and original source notes</summary>



This is a **commonly listed system-design interview prompt** with a concrete practice contract. Assume 2 million operations/s, 99.99% monthly availability and keys partitioned across 300 storage nodes. Clarify service guarantees and a first version before filling the board with services.

| Situation | Input / condition | Expected result |
|---|---|---|
| Read after write | Client puts v8 then reads from another node | Return v8 under the stated consistency contract. |
| One replica down | Two of three replicas are healthy | Define quorum and whether a write may be acknowledged. |
| Large object | Value is 2 GB | Store bytes separately; keep metadata and chunk manifest in KV path. |
| Tombstone expires | Old replica returns deleted value | Retention/repair protocol prevents resurrection. |

## Think from the contract to the boxes

Choose partitioning and replication before naming a database. A write has a version, replica quorum and durability promise. Read-your-writes can use session tokens or quorum reads. Deletes need tombstones long enough to reach every replica; compaction cannot erase the only evidence too early. Large values move through object storage with checksummed manifests. Distinguish acknowledgment latency from repair convergence.

**First diagram:** Draw hash partition → replica set → quorum response, then show hinted handoff/repair and tombstone propagation.

| AWS service / general role | Why it fits this design | Alternative and when it fits better |
|---|---|---|
| **Amazon DynamoDB** / managed key-value store | Choose for managed key access patterns and conditional writes. | Amazon Keyspaces for Cassandra-compatible wide-column workload. |
| **Amazon S3** / large-value object store | Keep multi-GB payload bytes outside the hot metadata path. | EBS only for attached block storage, not shared object access. |
| **Amazon Route 53** / client endpoint routing | Resolve regional/service endpoints. | AWS Global Accelerator for static anycast ingress. |
| **Amazon CloudWatch** / replica health telemetry | Track write latency, throttles, replication lag and repair backlog. | OpenTelemetry metrics where custom replica internals matter. |
| **AWS Backup** / recovery copies | Create point-in-time recovery protection for supported resources. | Application export snapshots for cross-engine recovery needs. |

Service choice follows the contract: the box label gives the generic job, while the table explains the AWS product and a reasonable substitute. Name which component owns durable truth, where retries happen, and the guarantee each managed service does **not** provide by itself.

## Pressure-test the design

**Follow-up: An acknowledged write is absent on one replica. Draw quorum intersection, read repair, and why expiring a tombstone too early resurrects a deleted key.**

**Senior expectation:** A rack loss causes repair traffic to compete with foreground reads. Set repair bandwidth, admission priority, and degraded-mode consistency behavior.

**Staff expectation:** Offer this store to teams with different data models. Define API/version contracts, isolation, migrations and when to use a managed database instead of operating a new distributed store.

**Practice artifact:** Draw hash partition → replica set → quorum response, then show hinted handoff/repair and tombstone propagation. Then trace every row in the table, draw one failure, and state what the customer observes. Suggested rehearsal: 35 minutes design, 10 minutes to challenge the guarantees.

**Evidence and origin:** The current community interview-question catalog lists a distributed key-value store prompt at LinkedIn, Databricks, Geico and Microsoft; individual report dates are not listed. The entry does not show the interview date and is not a verified company rubric. The prompt contract, workload, outcomes, diagrams and solution here are original practice material. Treat company tags as reported sightings, not a prediction of your interview loop.

**Interview report listing:** [Open the community question entry](https://www.hellointerview.com/community/questions/key-value-store/cm8gcrkz800b7epmpcj06fkwk).

</details>
