# System design

Turn requirements and workload estimates into an explainable architecture.

[Curriculum](../../README.md) · [About this part](../README.md)

## Before this chapter

[Security](../../02-applications/05-security/README.md)

Testing and ownership checks are part of each implementation. The dedicated testing and security chapters deepen those checks; do not postpone them until those chapters.

## Learn in this order

| Step | Existing lesson or exercise |
|---|---|
| 1 | [System design](design-method.md) |
| 2 | [Draw the system, then break it](whiteboard.md) |
| 3 | [Architecture · understand the mechanism before naming a service](mechanism-reference.md) |
| 4 | [Bookmark service](problems/bookmark-service.md) |
| 5 | [API quota: which request spends the last token?](problems/api-quota.md) |
| 6 | [Ticket inventory: one seat, two buyers](problems/ticket-inventory.md) |
| 7 | [Realtime chat: reconnect without losing the conversation](problems/realtime-chat.md) |
| 8 | [Social feed: a popular author changes the shape](problems/social-feed.md) |
| 9 | [Video processing: accept once, publish when ready](problems/video-processing.md) |
| 10 | [Checkout: paid twice, ordered once?](problems/checkout-payment.md) |
| 11 | [Notification platform](problems/notification-platform.md) |

Work through each problem from its opening brief. First draw the failing design and identify which component decides the disputed state. Use the paired architecture and event-timeline diagrams to test the design; explain the senior and staff changes before checking a service name. The later chapters return to these boundaries under observability, outages, large data, AI serving, and regional recovery.

## Go deeper on the same problem

Read the brief and contract first. Attempt the baseline before opening its answer. Continue to the existing changed-requirement questions and redraw or retest the same system. Senior follow-ups emphasize failure behavior and operating constraints; staff/lead follow-ups add scope, compatibility and ownership where the supplied problem supports them. Later-topic dependencies are linked below; return after learning them.

Related prerequisites for deeper follow-ups: [Reliability and incident response](../05-reliability/README.md) · [Data at scale](../../04-scale-and-evolution/01-data-at-scale/README.md) · [Performance and cost](../../04-scale-and-evolution/02-performance-cost/README.md).

[Choose an independent assessment](../../../practice/README.md) · [Assessment depth](../../../practice/depth.md)

Next chapter: [CI/CD and progressive delivery](../02-delivery/README.md).
