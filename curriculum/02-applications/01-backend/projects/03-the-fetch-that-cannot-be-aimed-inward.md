# 3. The fetch that cannot be aimed inward

## What you are building

> Build server-side link previews for user-submitted URLs. A malicious URL resolves to an internal address or redirects to the instance metadata endpoint. Valid public pages should still work, but the preview service must never become a proxy into your private network.

**Working contract:** Only explicitly supported public HTTP(S) destinations may be fetched. Validate the resolved addresses used by the actual connection and repeat the policy for every redirect. Bound all response work.

## Workload and the decisions it changes

These are constructed exercise assumptions. The large workload is a design target; the local demonstration does not establish that throughput. Use the [estimation constants](../../../01-code/01-problem-solving/estimation-constants.md) to check units before choosing capacity.

| Input or objective | Calculation / consequence |
|---|---|
| 100 previews/s; two-second total deadline | About 200 in-flight calls at full two-second occupancy unless admission caps it lower. |
| 1 MiB maximum response; three redirects | At most 100 MiB/s body transfer at the stated rate; rejected oversized pages stop early. |
| DNS may change between checks | Resolving once for validation and again for connection creates a bypass window. |

## Start with one working boundary

Run from the repository root with Python 3.12+:

```bash
python3 examples/architecture-starts/03_the_fetch_that_cannot_be_aimed_inward.py
```

[Open the starting code](../../../../examples/architecture-starts/03_the_fetch_that_cannot_be_aimed_inward.py). This is a runnable demonstration of the critical state boundary. The API, UI, cloud adapters and operating behavior below are the application you build around it.

| Record / module | Key or interface | Responsibility |
|---|---|---|
| url_policy | scheme,port,hostname,address_set | Reject credentials and non-public destinations. |
| fetch_plan | normalized_url,validated_ip,hostname,deadline | Connect to the validated address while preserving TLS hostname verification. |
| fetch_result | final_url,status,bytes,reason | Bounded metadata and explicit policy denial. |

## AWS implementation

![3. The fetch that cannot be aimed inward: AWS services, their general roles, and the primary data flow](../../../../assets/architecture-guides/03-the-fetch-that-cannot-be-aimed-inward.svg)

Network controls reduce exposure, while the HTTP adapter enforces which public destination was actually approved. A URL regex or a DNS check disconnected from the socket is insufficient.

## Build it in this order

### 1. Parse and reject before resolving

Use a standard URL parser, reject embedded credentials, unsupported schemes and unexpected ports, and normalize the host deliberately. Handle IPv4, IPv6 and mapped-address forms consistently. Do not rely on a substring blacklist such as localhost.

### 2. Bind validation to connection

Resolve the hostname, reject disallowed addresses and connect through an adapter that uses the validated IP while preserving Host and TLS SNI/certificate checks for the original hostname. Disable implicit environment proxies unless explicitly configured under the same policy.

### 3. Control every redirect and body

Disable automatic redirects in the HTTP client. Parse each Location, resolve and validate again, and stop after three redirects. Enforce a total deadline, decompressed byte limit and bounded content parsing; a tiny compressed response can expand into a large body.

### 4. Add network defense and diagnostics

Restrict worker egress and metadata access independently of application checks. Return a generic unavailable preview to the user while recording a safe policy reason. Use local controlled public/private-address fixtures to observe denials; do not probe real internal services.

## Infrastructure configuration

| Resource or boundary | Initial configuration and reason |
|---|---|
| Worker placement | Use a network boundary that cannot reach sensitive internal services; do not attach broad cloud credentials to fetch workers. |
| HTTP adapter | Verify destination pinning, TLS hostname handling, redirects and proxy behavior in the selected client library. |
| Resource limits | Total deadline, concurrency, redirect count and decompressed body cap are independent controls. |

Use one disposable AWS environment for the cloud exercise. Put the named resources in `infra/template.yaml` or your existing IaC tool, pass resource IDs through configuration, and scope each runtime role to its own tables, buckets and queues. The diagram is a design to implement; it is not a claim that these resources have been deployed. Record the commands you used to deploy and remove the exercise resources.

## Observe the result

| Action | Expected visible result |
|---|---|
| Run the starting program | Public fixture address passes; metadata and mixed public/private resolutions fail. |
| Return a redirect to loopback | The second hop is denied before a connection. |
| Send an oversized compressed page | The worker stops at the decompressed byte limit. |

## The next design decision

Allow customer-managed authenticated previews. Keep credentials scoped to approved origins and strip them on redirects; define whether cross-origin redirects are allowed at all.

<details>
<summary>Further constraints from the original project</summary>

## Follow-up 1 · DNS returns mixed addresses

**Changed requirement:** One hostname returns both a public IPv4 and private IPv6 address. What does your policy do? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

For this exercise reject mixed unsafe answers rather than relying on client selection order. Test IPv4-mapped IPv6 and redirects with the same canonical address policy.

</details>

## Follow-up 2 · A future worker reuses fetching

**Changed requirement:** The queued worker gains new credentials and network routes. Is the guard enough? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Reuse the same client and add restricted egress and least-privilege credentials. Application validation and network isolation protect different boundaries; neither proves the other.

</details>

</details>
