# Working notes — 13 · data-at-scale projects.md (written 2026-09-22)

Verification log for claims made in `tiers/02-senior/13-data-at-scale/projects.md`.
All checked 2026-09-22 against AWS/PostgreSQL documentation via web fetch.

## Verified facts

- **SQS `ApproximateAgeOfOldestMessage`** (SQS dev guide, sqs-available-cloudwatch-metrics):
  seconds; age of oldest unprocessed message. Caveats now documented: on standard
  queues a message received 3+ times and not deleted is moved to the back and
  **excluded from the metric** until successfully processed — so a pure poison
  pill can hide from the age metric; the DLQ redrive (`maxReceiveCount`) is what
  surfaces it. When a message moves to a DLQ, age resets; the DLQ metric reflects
  move time, not send time. Recommended DLQ metric: `ApproximateNumberOfMessagesVisible`.
  Depth metric: `ApproximateNumberOfMessagesVisible`.
- **SQS visibility timeout** (sqs-visibility-timeout): default 30 s; hard max 12 h
  from first receive (extensions via `ChangeMessageVisibility` do not reset the
  12 h); too-short timeout → message becomes visible again → second consumer,
  duplicate processing. Heartbeat-extend is the documented pattern.
- **Lambda + SQS `ScalingConfig.MaximumConcurrency`** (lambda/latest/dg/services-sqs-scaling
  + AWS what's-new Jan 2023): event-source-level, range 2–1,000, no charge; docs
  recommend it over reserved concurrency for limiting SQS-driven scaling (reserved
  concurrency causes throttles + retries); if both set, reserved concurrency must
  be ≥ total max concurrency across that function's SQS event sources.
- **SQS free tier** (aws.amazon.com/sqs/pricing): 1M requests/month free, every
  month, all customers; unused does not roll over.
- **DynamoDB TTL** (howitworks-ttl): deletes expired items "typically within a few
  days", consumes no write throughput, expired-but-undeleted items still appear in
  reads — filter expressions recommended. TTL is a janitor, not an expiry contract.
- **Kinesis `GetRecords.IteratorAgeMilliseconds`** (streams monitoring-with-cloudwatch):
  0 = caught up; same age-not-depth lesson under a different name; AWS guidance:
  keep under 50% of retention (default 24 h) or records expire unread.
- **RDS `ReplicaLag`** (RDS monitoring read replication + re:Post): seconds, derived
  from `now() - pg_last_xact_replay_timestamp()`; −1 when indeterminable; on an
  idle source it can read up to ~5 min because lag is measured against the last
  committed transaction. **`AuroraReplicaLag`**: milliseconds; Aurora replicas read
  the same storage volume, lag is page-cache propagation, typically well under
  100 ms — the architectural reason Aurora's number is a different unit.
- **RDS Proxy** (aws.amazon.com/rds/proxy): pools/shares established connections;
  Aurora PG/MySQL, RDS PG/MySQL/MariaDB/SQL Server; positioned for serverless
  bursts of new connections; failover time reduced up to 66%.
- **ElastiCache** (aws.amazon.com/elasticache): Valkey, Redis OSS and Memcached
  compatible; ElastiCache Serverless exists.
- **`pg_wal_replay_pause()` / `pg_wal_replay_resume()`** (postgresql.org
  functions-admin, current): standby-only recovery-control functions; pause
  request returns immediately, replay pauses shortly after; resumed explicitly.
  This is the honest way to manufacture replication lag for a read-after-write demo.
- **PostgreSQL default `max_connections` = 100** — reusing the section README's
  citation (checked 2026-09-21 there); not re-verified today.

## Corrections made because of verification

- Planned to write "a poison message keeps `ApproximateAgeOfOldestMessage`
  climbing forever." Current SQS docs say the opposite for standard queues
  (excluded after 3+ receives). Rewritten: age catches the stalled-backlog case;
  the DLQ alarm catches the poison case; you need both.
- Planned to present Lambda reserved concurrency as the flood valve; current docs
  recommend event-source maximum concurrency for SQS and reserved concurrency as
  the blunter function-level cap. Wrote both, in that order.
- DynamoDB TTL delay: docs say "within a few days", not the older "48 hours" figure.

## Diagram decisions (queue-age-vs-depth.svg)

- Depth (messages) and age (seconds) are different units → no dual axis; two
  stacked panels sharing one time axis, which is also how the two CloudWatch
  metrics would sit on a real dashboard.
- Frame one must read complete: both lines drawn statically; animation is a "now"
  cursor + two dots riding the lines (motion = time passing), fading out at the
  right edge and back in at the left so the loop returns to its start.
- Identity never color-alone: each line lives in its own labelled panel.
- Mechanism wording kept honest: depth flat because arrivals and completions
  cancel; age climbs because the oldest work is never the work being done
  (stalled backlog / starved subset), not a claim about strict-FIFO queues.
