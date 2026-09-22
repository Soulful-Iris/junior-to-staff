\set ON_ERROR_STOP on
\pset pager off
SET search_path = interview_lab;
\echo 'Small uniform table: 200 rows. Owner 2 has 2 rows.'
TRUNCATE bookmarks;
DROP INDEX IF EXISTS bookmarks_owner_time;
INSERT INTO bookmarks
SELECT g, 1 + (g % 100), '2026-01-01 UTC'::timestamptz + g * interval '1 second', repeat('x',200), ''
FROM generate_series(1,200) g;
ANALYZE bookmarks;
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks WHERE owner_id=2 ORDER BY created_at DESC,id DESC LIMIT 20;
CREATE INDEX bookmarks_owner_time ON bookmarks(owner_id,created_at DESC,id DESC);
ANALYZE bookmarks;
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks WHERE owner_id=2 ORDER BY created_at DESC,id DESC LIMIT 20;
\echo 'Large uniform table: 100000 rows. Owner 2 has 1000 rows.'
TRUNCATE bookmarks;
INSERT INTO bookmarks
SELECT g, 1 + (g % 100), '2026-01-01 UTC'::timestamptz + g * interval '1 second', repeat('x',200), ''
FROM generate_series(1,100000) g;
ANALYZE bookmarks;
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks WHERE owner_id=2 ORDER BY created_at DESC,id DESC LIMIT 20;
\echo 'Remove matching index for the same large query, then restore it.'
DROP INDEX bookmarks_owner_time;
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks WHERE owner_id=2 ORDER BY created_at DESC,id DESC LIMIT 20;
CREATE INDEX bookmarks_owner_time ON bookmarks(owner_id,created_at DESC,id DESC);
\echo 'Skew: owner 1 gets first 90000 rows; owner 2 gets 100 rows.'
UPDATE bookmarks SET owner_id=1 WHERE id<=90000;
ANALYZE bookmarks;
SELECT owner_id,count(*) FROM bookmarks WHERE owner_id IN (1,2) GROUP BY owner_id ORDER BY owner_id;
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks WHERE owner_id=2;
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks WHERE owner_id=1;
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks WHERE owner_id=1 ORDER BY created_at DESC,id DESC LIMIT 20;
\echo 'Keyset page: owner 2, cursor at row 99901; expect at most 20 strictly earlier pairs.'
EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM bookmarks
WHERE owner_id=2 AND (created_at,id)<('2026-01-02 03:45:01 UTC'::timestamptz,99901)
ORDER BY created_at DESC,id DESC LIMIT 20;
\echo 'Heap location is independent from key order; HOT eligibility is conditional.'
SELECT id,ctid FROM bookmarks ORDER BY id LIMIT 5;
UPDATE bookmarks SET note='non-indexed update' WHERE id BETWEEN 1 AND 100;
SELECT relname,n_tup_upd,n_tup_hot_upd FROM pg_stat_user_tables WHERE schemaname='interview_lab' AND relname='bookmarks';
-- Statistics can be delayed. This is observation, not a guaranteed HOT count.
