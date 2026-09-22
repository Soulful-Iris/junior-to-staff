# 1. A shared reading list

## The reviewer's brief

> A book club shares links. Alice marks a link read and Bob’s unread list unexpectedly changes. Correct the data model while preserving group visibility and owner-only edits. Which facts belong to a person, an item, and a group?

This is a **constructed practice brief**, not an attributed company question.
Prerequisites: [the act index](../README.md) and [the tier starting point](../../../tiers/01-junior/01-the-change-loop/README.md). This page is a build brief; it does not ship a runnable application. The original build and prompt sequence below defines the implementation checkpoints.

| Case | Exact input or workload | Expected outcome |
|---|---|---|
| Small example | Group G contains Alice and Bob; Alice creates item 7; Alice marks item 7 read. | Both see the item; only Alice has read state; Bob cannot edit Alice’s URL. |
| Boundary / failure | Bob sends a direct DELETE for item 7 while hiding the UI button. | Server refuses with the chosen 403/404 policy and the item remains. |
| Scope | One group initially; tags and visible fetch failure; no anonymous editing. | Explain any additional assumption before implementing it. |

Before looking at the guidance, state the invariant in one sentence and trace the example. In interview practice, implement or sketch independently, then reveal the reasoning. On the AI path, use the prompts below and verify each checkpoint before the next request.

## Baseline and the failure to explain

```mermaid
flowchart TD
 A["Alice: mark read"] --> I["Item 7: read=true"]
 I --> B["Bob incorrectly sees read"]
 I --> G["Shared group list"]
```

An item-level boolean merges two different users’ facts. UI controls do not protect the write boundary.

<details>
<summary>Reveal the approach and decisions</summary>

Write the ownership and visibility rules before endpoints. Use items, memberships, and read-state keyed by person/item; enforce authorization in server queries. The invariant is that one member’s read action cannot change another member’s read state. Keep title extraction optional to successful saving.

</details>

## Follow-up 1 · Many groups

**Changed requirement:** Alice belongs to two groups; Bob belongs to one. Which rows can Bob list? Predict which boundary must change before opening the design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Filter by verified membership at the data access boundary; never trust a client-supplied group ID alone. Test list, detail, edit and title-job paths for cross-group leakage.

```mermaid
flowchart TD
 U["Authenticated user"] --> A["Membership authorization"]
 X["Requested group ID"] --> A
 A -->|member| I["Items by allowed group"]
 A -->|member| R["Read state by user and item"]
 A -->|not a member| D["403 or 404"]
```

</details>

## Follow-up 2 · The title provider stalls

**Changed requirement:** Saving must return in 300 ms while the provider takes ten seconds. What moves? State what evidence would make you reject your first design.

<details>
<summary>Expected reasoning and changed diagram</summary>

Atomically save the item and durable title job, return pending, and let a guarded bounded worker complete the title. Retry execution may repeat fetching; conditional versions protect the current result.

```mermaid
flowchart TD
 B["Browser"] --> A["Authorized API"]
 A --> D["Item and job transaction"]
 D --> Q["Pending work"]
 Q --> W["Guarded title worker"]
 W -->|current version only| D
```

</details>

## Evidence to bring to review

Build in three stops: reproduce the small case and baseline failure; implement the protected boundary; then replay both changed requirements with captured outputs. Record commands, fixtures, and observed results in your implementation README. A diagram is a prediction until those checks run.

**Senior expectation:** Test separate users, direct unauthorized writes and provider failure. **Additional lead scope:** Define membership changes and ownership transfer contracts. Completion demonstrates practice evidence; it does not establish interview readiness or multi-team delivery experience.

## Build and prompt sequence

![The shape every act one system has: a browser, an API, a store, and one outside dependency you do not control, with a request travelling through and the outside call marked as the part that will fail](../../../assets/diagrams/act1-shape.svg)

*A group adds links, tags them, marks them read, and sees what the group is reading.*

**Build**

Sign-in, add a URL, the system fetches the page title, tag it, mark it read, see
everyone's. This is the same system the [spine](../../../projects/) uses, so if you
pick this one you can carry it through all five spine projects without starting
again.

```mermaid
graph LR
  B[browser] --> A[api]
  A --> D[(store)]
  A -.->|"untrusted external page"| W[someone else's site]
```

**The thought process**

The first real decision is not technical. It is **what "shared" means**: one
group, or groups? Because "one group" is a system with users, and "groups" is a
system with memberships, and that is a different schema, a different
authorisation rule and a different set of screens. Deciding late costs you a
migration in a project that has no migrations yet.

Then the one people get wrong: **what owns "read"?** Marking something read is a
fact about a person *and* an item, not about the item. If you put a boolean on
the item, the second user to mark it read will silently mark it for everybody,
and you will not notice until somebody complains that their list is wrong.

Third: the fetch is somebody else's server. It can be slow, absent, enormous, or
deliberately hostile. You decide whether the user waits for it, and whichever
you choose, the timeout is yours to pick.

**How to organise the prompts**

```
I am building a shared reading list. Before any code: write the data
model and the endpoints, and tell me the three decisions in this design
most likely to be wrong.

Do not write code yet.
```

Argue with the answer. Specifically, check whether "read" is on the item.

```
Implement only sign-up and sign-in, with tests. Stop when I can run it
and log in.
```

```
Add the rule that a person can only edit or delete their own items.
Write the test for somebody else's item FIRST and show me it failing
before you add the check.
```

```
Now the fetch. It must have a timeout I chose, and a URL that hangs,
404s or returns no title must still leave a saved item with the failure
visible rather than swallowed.

Show me all four cases.
```

**On AWS**

For a small existing container, compare **ECS on Fargate**, **App Runner**
where available to your account, or **EC2** according to deployment control,
operational burden and steady versus bursty demand. A small **RDS PostgreSQL**
database fits the membership and ownership relations. A bounded **Lambda**
request path is also viable; manage connection reuse and concurrency deliberately,
and evaluate **RDS Proxy** when its connection behavior justifies the additional
service. Waiting on external calls consumes resources in any runtime.

Use **S3** for uploaded objects and an appropriate secrets/configuration store,
such as **Parameter Store** or **Secrets Manager**, based on rotation and access
needs. **Route 53** and **ACM** cover DNS and supported certificate integrations.
Compare the full account estimate, including database, load balancer, public IP,
network egress and logs; a small instance does not imply a free deployment.
Prefer the local implementation while learning the contract, and delete optional
cloud resources when the exercise ends.

**What productionising it means**

Somebody who is not you can deploy it from the README. Secrets are injected, not
committed. There is a backup and you have restored from it. The fetch cannot
hang the whole app. And the authorisation rule has a test that fails when you
remove the check — that one rule is the difference between a demo and something
you would let a group of friends use.

**The learning**

Almost every small product is this: identity, a store, a list, and one call to
someone else's computer. The hard parts are never the list. They are who is
allowed to do what, and what happens when the other computer misbehaves.

**How you would know it is wrong**

- Sign in as one user and send a delete for another user's item **directly**, not through the UI. It must refuse.
- Turn off your network and add a URL. The failure should be visible, the record sane.
- Two accounts, same item, one marks it read. Check the other's list.
- Deploy from a clean clone in a fresh directory, on a machine that has never seen the project.

**Stage it**

1. Auth and an empty list, deployed and reachable.
2. Items, tags, and the authorisation rule with its failing-first test.
3. The fetch, with its four failure cases.
4. Backups, a restore you have actually done, and the README a stranger can follow.

---

[Back to the ordered project index](../README.md)
