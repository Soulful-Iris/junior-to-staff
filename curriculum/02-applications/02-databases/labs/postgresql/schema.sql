-- Run only in a disposable database. This resets the named teaching schema.
DROP SCHEMA IF EXISTS interview_lab CASCADE;
CREATE SCHEMA interview_lab;
SET search_path = interview_lab;
CREATE TABLE stock (id integer PRIMARY KEY, available integer NOT NULL CHECK (available >= 0));
CREATE TABLE reservations (id text PRIMARY KEY, stock_id integer NOT NULL REFERENCES stock(id));
CREATE TABLE doctors (id integer PRIMARY KEY, on_call boolean NOT NULL);
CREATE TABLE counters (id integer PRIMARY KEY, hits integer NOT NULL);
INSERT INTO stock VALUES (1, 1);
INSERT INTO doctors VALUES (1, true), (2, true);
INSERT INTO counters VALUES (1, 0), (2, 0);
CREATE TABLE bookmarks (
  id bigint PRIMARY KEY,
  owner_id integer NOT NULL,
  created_at timestamptz NOT NULL,
  title text NOT NULL,
  note text NOT NULL DEFAULT ''
) WITH (fillfactor=80);
