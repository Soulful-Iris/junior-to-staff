# Working notes — 05 data-and-databases projects.md (2026-09-22)

Scope: five section projects + one animated SVG (`migration-both-ways.svg`).
Everything below verified by web search this session, 2026-09-22.

## AWS facts checked

- **Free tier changed 2025-07-15.** Accounts created on/after that date get a
  credit pool (Free Plan) instead of the old 12-month allowances (750 h/month
  RDS/EC2 micro etc.). Older accounts keep the legacy shape. Always Free
  unchanged: Lambda 1M invocations/mo, DynamoDB 25 GB, S3 5 GB.
  Source: aws.amazon.com free tier pages + coverage of the July 2025 revamp.
- **RDS automated backups**: retention 1–35 days; daily snapshot plus
  transaction logs shipped ~every 5 minutes; PITR to any second up to the
  latest restorable time; **restore always creates a new instance** — never
  in place. Automated snapshots can be copied to manual to outlive retention.
  Source: docs.aws.amazon.com RDS UserGuide (WorkingWithAutomatedBackups),
  aws.amazon.com/rds/features/backup.
- **Aurora Serverless v2 scale-to-zero**: announced 2024-11-20; min 0 ACU
  with auto-pause (idle 5 min–24 h), resume typically <15 s, storage still
  billed while paused; some configs prevent pausing (RDS Proxy, logical
  replication, global database). Source: AWS what's-new 2024-11 + Aurora
  UserGuide aurora-serverless-v2-auto-pause.
- **RDS Blue/Green supports PostgreSQL** (Aurora + RDS for PostgreSQL, since
  Oct 2023). Green follows blue via logical replication for major upgrades;
  DDL on blue degrades replication; since 2024-11-22 minor-version B/G uses
  physical replication and green is read-only. So B/G is for upgrades and
  maintenance rehearsal, not the app-shape expand/contract migration.
  Source: AWS what's-new 2023-10, blue-green-deployments-considerations doc.

No prices quoted anywhere in projects.md (spec rule; only checked shapes,
not numbers).

## Design decisions

- Project order rises: model → change the model live → measure it → make
  writes safe under concurrency → survive losing all of it.
- Prompt-sequence requirement "review a schema a model proposed" lives in
  project 1, with a planted flaw so the review is an instrument, not a
  compliment generator (differs from the README's Request 1: the plant and
  the propose→review loop are the project here).
- Project 4 deliberately separates isolation (lost update, READ COMMITTED)
  from atomicity (kill -9 between paired writes) — the folk cure "wrap it in
  a transaction" treats the wrong disease and the project makes that visible.
- Project 5 is pitched junior (pg_dump/restore/diff, minutes measured);
  deep PITR/replication remain senior per the section's "not covered here".
- Diagram: add → backfill → switch → remove with a dashed warm wall before
  REMOVE; green reversal rail under steps 1–3, blocked stub under step 4;
  one paced dot runs up → down → up past the wall and fades (SMIL only,
  frame one static-correct, loop restarts clean because the dot fades out).
- migration-phases.svg (staff tier 19) is a cost curve; no overlap.

## Text-width bookkeeping for the SVG

Budgets used: 12.5px sans ≈ 6.8 px/ch, 11px sans ≈ 6.0, 11px mono ≈ 6.6,
10px mono + 1.2 ls ≈ 7.2. Widest strings per 150px box kept ≤ 132px;
caption lines ≤ 640px. Rendered in chrome-headless-shell at t≈0 and t≈6 s
and inspected before committing to the reference.
