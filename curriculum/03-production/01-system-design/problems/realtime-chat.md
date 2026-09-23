# Realtime chat: reconnect without losing the conversation

> **Interviewer:** “Design a team chat. Ana sends ‘Ready?’ on her phone, loses reception before the acknowledgement, and retries from her laptop. Ben was offline. When both reconnect, which messages appear, in what order, and how do you avoid an accidental duplicate?”

Assume 2 million daily active users, 30,000 peak messages/s, groups of 2–500 members, and one-year history. These are exercise inputs. Distinguish server-accepted messages from messages displayed or read on a device.

| Scenario | Expected visible result |
|---|---|
| Send succeeds, reply disappears, same client message ID retried | One stored message and one stable server message ID |
| Ben reconnects after missing messages 18–21 | Resume after acknowledged cursor 17; return 18–21, then live delivery |
| Two devices send concurrently into one room | Explain the chosen per-room ordering rule; no unearned global order |
| Device is offline for two days | History query and pagination work even when live connection state expired |

![Ephemeral WebSocket delivery loses history; a durable log anchors reconnect](../../../../assets/design-practice/realtime-chat-boundary.svg)

## Separate storage from delivery

The message write becomes authoritative when the server persists it and assigns a room sequence or another documented order. WebSockets carry low-latency delivery, presence, and acknowledgements; connections are not the message database. Store `(room_id, sequence, message_id, sender_id, body, created_at)` and an idempotency key scoped to sender and room. If a device misses sequence 19, fetch the gap before advancing its cursor. Delivery may be at least once; the UI deduplicates by message ID. “Read” means the client confirms display according to an explicit policy, not merely that a push reached a gateway.

![Duplicate send, durable commit, missing acknowledgement, and replay](../../../../assets/design-practice/realtime-chat-trace.svg)

## Make the boxes accountable

Draw authentication/room membership check → message authority → history store → fanout workers → connection gateways → devices. Membership changes must be checked before fetching private history as well as before live subscriptions. Estimate the largest room's fanout separately from average room size. If media is added, separate encrypted object storage and its authorization from message ordering.

## Put the AWS names on the boxes

![AWS service boxes labeled with their general architectural roles](../../../../assets/design-practice/realtime-chat-aws.svg)

**Why these boxes, and what changes the choice:** WebSocket connections deliver low-latency updates, while a DynamoDB log owns acknowledged history. ECS owners may assign room sequence numbers; a database conditional write must still fence old owners. SQS fans out work but can redeliver, so reconnect uses log cursors instead.

Read the smaller label under each service first: it names the architectural job. Then ask whether that service supplies the guarantee in the problem, or simply moves work to the next box.

**Senior follow-up:** A fanout worker dies after delivering to half a room. The cursor-based recovery path replays without duplicating visible messages. Show what a restarted worker reads, when it checkpoints, and what happens if a user is removed halfway through a backlog.

**Staff follow-up:** The same room has members in three Regions. Choose one sequencing authority per room or state the weaker ordering promise. Partition a hot room's fanout without promising independent writers a single total order for free. Specify how ownership transfers and how to check no accepted message disappears.

**Practice artifact:** Label the durable commit on a before/after diagram; trace the lost acknowledgement and reconnect; define retention, per-room ordering, and two tests for replay plus removal.

**AWS translation:** API Gateway WebSocket or self-managed ECS gateways hold connections; a durable store holds history and cursor. DynamoDB can model `PK=room`, `SK=sequence`, but a single huge room may need a different distribution strategy; SQS standard delivery can duplicate and reorder, so it cannot establish room ordering. See [SQS standard queue guarantees](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html).

**Source note:** Original scenario, inspired by recurrent senior-level delivery/consistency themes; no company attribution.
