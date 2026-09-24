# Enforce identity, ownership and tenant boundaries

Enforce identity, ownership, and trust boundaries beyond the interface.

<section class="chapter-context" markdown="1">

## Enforce access where the protected action happens

Hiding another user’s Edit button does not stop a direct HTTP request. A saved URL can also cause the server to connect somewhere the user could not reach directly. Follow both the person’s permission and the service’s network privileges.

Begin with ownership checks in a local API, then extend to tenant boundaries, private links, and outbound fetches. Keep demonstration identity headers separate from production authentication. State the protected resource and action before selecting an AWS permission.

</section>

[Curriculum](../../README.md) · [About this part](../README.md)

## Prerequisites

[Find defects and evaluate engineering evidence](../04-testing/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Concepts and worked examples

| Step | Existing lesson or exercise |
|---|---|
| 1 | [Enforce who can act on each resource and what the server can reach](trust-and-authorization.md) |
| 2 | [Enforce tenant access in APIs, caches and exports](problems/tenant-isolation.md) |
| 3 | [Record permission changes with durable audit evidence](problems/audit-trail.md) |

## Explore failures and changed requirements

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Process, search and store data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Migrate live systems and verify recovery](../../04-scale-and-evolution/04-migrations/README.md).

## Build a project

Each project explains its application, names the deliverable, links the supplied code and gives ordered implementation steps. Run the local example first; use the AWS mapping after the local behavior works.

- [Prevent overlapping shifts and enforce manager access](projects/a-shift-schedule.md)

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [Design services from requirements to failure behavior](../../03-production/01-system-design/README.md).
