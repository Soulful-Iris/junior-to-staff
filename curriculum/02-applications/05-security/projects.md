# Practice authorization, credential recovery and dependency boundaries

[Chapter](README.md)

A bookmark API accepts requests from members, accesses storage with a service identity, and is built by a deployment workflow. Those are three different trust boundaries. Work on a local fixture or disposable environment so each exercise can demonstrate the exact allowed and denied action.

## Choose your starting code

Begin with [the authorization lesson](trust-and-authorization.md) and [the local reading-list API](../../../examples/reading-list-starter/README.md). Its demonstration identity makes ownership visible but is not a production login system.

<a id="1-routes-minus-checks"></a>

## 1. Map routes to explicit access decisions

The interface hides Edit for another member’s bookmark, but a direct PATCH can still name its ID.

**Your task.** Inventory every route, method, resource, and permitted actor. Include reads, exports, and background operations. Trace where each decision is enforced, then send an allowed and denied request through that boundary. A route-to-middleware name table is evidence to investigate, not proof of correct policy.

**What to observe.** Alice cannot modify Bob’s row. Public routes are explicitly named, and a missing check cannot be mistaken for an intentionally public operation.

**Changed requirement.** A batch route accepts several IDs. Decide whether denial fails the whole batch or returns scoped per-item results without leaking private data.

[Worked mechanism and implementation context](problems/tenant-isolation.md)

<a id="2-the-cross-user-suite"></a>

## 2. Exercise another user’s object through every access path

An authenticated caller is known, but that does not make every resource theirs. The same object may be reachable through detail, search, export, and worker paths.

**Your task.** Use two known identities and private fixture objects. Attempt each applicable read and mutation as the wrong identity. Inspect stored state as well as the response. Keep rejection logs useful without recording protected payloads.

**What to observe.** Denied mutations leave data unchanged. The chosen 403 or 404 policy is consistent with the information the product permits revealing.

**Changed requirement.** Membership is revoked after a response is cached. Move authorization to the delivery decision or define an explicit bounded-stale policy.

[Worked mechanism and implementation context](../../04-scale-and-evolution/01-data-at-scale/labs/cache-consistency/revocation.md)

<a id="3-deleting-the-secret-instead-of-rotating-it"></a>

## 3. Rotate a credential and verify the old one no longer works

Deleting a secret from a file does not revoke copies already obtained. The running application also needs to learn the replacement value.

**Your task.** Inventory runtime and deployment credentials. Replace a disposable credential through its actual reload or restart path, time the transition, and verify old access fails. For a deployment identity, compare short-lived workload federation with a stored key and state the remaining permissions.

**What to observe.** The intended operation succeeds with the new identity and fails with the revoked one. No credential values appear in the evidence record.

**Changed requirement.** An old process still has a cached credential. Define refresh, overlap, and cutoff behavior without assuming a secret-store update automatically restarts every consumer.

[Worked mechanism and implementation context](../../03-production/03-infrastructure/configuration-and-environments.md)

<a id="4-the-lockfile-diff-read-for-tampering"></a>

## 4. Review what a dependency update can execute

A lockfile changes one direct package and several transitive packages. Installation may also execute scripts using the build job’s permissions.

**Your task.** Inspect the exact diff, integrity/provenance information, install scripts, and required behavior. Compare retaining the dependency with alternatives against its full contract. An age delay is one risk control, not proof a version is safe. Record accepted uncertainty.

**What to observe.** You can identify the version and transitive path actually used by the built artifact. A dependency inventory answers whether a named package is present.

**Changed requirement.** A trusted package begins requiring a new install script. Decide which isolated build capability it needs and what evidence justifies allowing it.

[Worked mechanism and implementation context](trust-and-authorization.md)

<a id="5-the-second-path"></a>

## 5. Find alternate paths around a control

An API ownership check can be correct while an export job uses a privileged database query without the same scope.

**Your task.** Choose a protected operation and draw every route to its effect. Include direct service access, scheduled jobs, administrative tools, and cached delivery where applicable. Exercise one suspected bypass in your controlled fixture and repair the authority boundary.

**What to observe.** The original allowed operation still works, while the alternate unauthorized route is denied at the effect or data boundary.

**Changed requirement.** An emergency operator needs broader access. Define a separate attributable capability and revocation path instead of silently treating all callers as administrators.

[Worked mechanism and implementation context](problems/audit-trail.md)

## Connect the exercise to a deployed application

The linked lessons identify local mechanisms and proposed cloud roles. A database fixture, browser screenshot, or capacity equation does not create AWS resources. Implement the local contract first, then add the storage, network, identity, and operational adapters named by the deployment lesson. Keep measured results separate from proposed infrastructure.
