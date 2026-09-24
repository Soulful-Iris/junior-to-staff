"""Local link-monitor reference. Python 3.12+, standard library only.

The HTTP adapter intentionally accepts only the supplied loopback fixture server.
Do not remove that boundary to create an internet crawler; see the project guide.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request

SCHEMA = '''
CREATE TABLE IF NOT EXISTS links (
 id TEXT PRIMARY KEY, url TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'unknown',
 version INTEGER NOT NULL DEFAULT 0, last_sequence INTEGER NOT NULL DEFAULT -1);
CREATE TABLE IF NOT EXISTS observations (
 job_id TEXT PRIMARY KEY, link_id TEXT NOT NULL REFERENCES links(id),
 sequence INTEGER NOT NULL, observed_at TEXT NOT NULL, status INTEGER, outcome TEXT NOT NULL, content_hash TEXT,
 UNIQUE(link_id, sequence));
CREATE TABLE IF NOT EXISTS transitions (
 id TEXT PRIMARY KEY, link_id TEXT NOT NULL REFERENCES links(id),
 from_state TEXT NOT NULL, to_state TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS outbox (
 transition_id TEXT PRIMARY KEY REFERENCES transitions(id),
 status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0);
'''

@contextmanager
def connect(path):
    db = sqlite3.connect(path, isolation_level=None, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript(SCHEMA)
    try:
        yield db
    finally:
        db.close()


def classify(status, expected_found=True):
    if status in (404, 410):
        return 'broken'
    if status == 429:
        return 'throttled'
    if status is not None and 200 <= status < 300:
        return 'reachable' if expected_found else 'content_changed'
    return 'uncertain'


def record(db, link_id, url, job_id, sequence, status, body=b'', expected_found=True):
    """Atomically append an observation, advance ordered state, and enqueue a transition.

    sequence is assigned by the scheduler per link, never by queue receive order.
    An identical job is a replay; conflicting reuse of an ID is an input error.
    """
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError('sequence must be a nonnegative integer')
    outcome = classify(status, expected_found)
    digest = hashlib.sha256(body).hexdigest()
    db.execute('BEGIN IMMEDIATE')
    try:
        old_job = db.execute('SELECT * FROM observations WHERE job_id=?', (job_id,)).fetchone()
        if old_job:
            actual = (old_job['link_id'], old_job['sequence'], old_job['status'], old_job['content_hash'], old_job['outcome'])
            if actual != (link_id, sequence, status, digest, outcome):
                raise ValueError('job_id reused with different observation')
            db.execute('COMMIT')
            return 'duplicate'
        db.execute('INSERT OR IGNORE INTO links(id,url) VALUES (?,?)', (link_id, url))
        link = db.execute('SELECT * FROM links WHERE id=?', (link_id,)).fetchone()
        if link['url'] != url:
            raise ValueError('link_id reused with different URL')
        db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?)',
                   (job_id, link_id, sequence, datetime.now(timezone.utc).isoformat(), status, outcome, digest))
        if sequence > link['last_sequence']:
            db.execute('UPDATE links SET last_sequence=? WHERE id=?', (sequence, link_id))
            # Temporary failures never erase the last known meaningful state.
            if outcome in ('reachable', 'broken') and outcome != link['state']:
                version = link['version'] + 1
                db.execute('UPDATE links SET state=?,version=? WHERE id=?', (outcome, version, link_id))
                # A first healthy sample is baseline. First observed 404 is actionable.
                if link['state'] != 'unknown' or outcome == 'broken':
                    transition = f'{link_id}:{version}'
                    db.execute('INSERT INTO transitions VALUES (?,?,?,?)',
                               (transition, link_id, link['state'], outcome))
                    db.execute('INSERT INTO outbox(transition_id) VALUES (?)', (transition,))
        db.execute('COMMIT')
        return outcome
    except Exception:
        db.execute('ROLLBACK')
        raise


def snapshot(db):
    return {table: [dict(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY rowid')]
            for table in ('links', 'observations', 'transitions', 'outbox')}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_fixture(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
            or parsed.port != 8765 or parsed.username or parsed.password):
        raise ValueError('Local adapter only accepts http://127.0.0.1:8765 fixtures')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': 'LearningLinkWatcher/1.0'})
    try:
        response = opener.open(request, timeout=2)
    except urllib.error.HTTPError as exc:
        response = exc
    except (urllib.error.URLError, TimeoutError):
        return None, b''
    with response:
        body = response.read(65537)
        if len(body) > 65536:
            return None, b''
        return response.status, body


def demo(db):
    for sequence, status in enumerate((200, 404, 404, 200), start=1):
        record(db, 'guide', 'https://example.invalid/guide', f'run-{sequence}:guide', sequence, status)
    return snapshot(db)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='watcher.sqlite3')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo'); sub.add_parser('inspect')
    check = sub.add_parser('check')
    check.add_argument('--url', required=True); check.add_argument('--id', required=True)
    check.add_argument('--sequence', required=True, type=int)
    check.add_argument('--expect', default='guide-v1')
    args = parser.parse_args()
    with connect(args.db) as db:
        if args.command == 'demo':
            result = demo(db)
        elif args.command == 'check':
            job_id = f'{args.sequence}:{args.id}'
            existing = db.execute('SELECT 1 FROM observations WHERE job_id=?', (job_id,)).fetchone()
            if existing:
                registered = db.execute('SELECT url FROM links WHERE id=?', (args.id,)).fetchone()
                if registered['url'] != args.url:
                    raise ValueError('link_id reused with different URL')
            if not existing:
                status, body = fetch_fixture(args.url)
                record(db, args.id, args.url, job_id, args.sequence,
                       status, body, args.expect.encode() in body)
            result = snapshot(db)
        else:
            result = snapshot(db)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
