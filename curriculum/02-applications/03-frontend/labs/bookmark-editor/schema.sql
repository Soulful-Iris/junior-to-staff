PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS bookmarks (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 200),
  url TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  version INTEGER NOT NULL DEFAULT 1 CHECK(version > 0)
);
CREATE INDEX IF NOT EXISTS bookmarks_owner_created_id ON bookmarks(owner_id,created_at DESC,id DESC);
CREATE TABLE IF NOT EXISTS mutations (
  owner_id TEXT NOT NULL,
  mutation_id TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  response TEXT NOT NULL,
  PRIMARY KEY(owner_id,mutation_id)
);
