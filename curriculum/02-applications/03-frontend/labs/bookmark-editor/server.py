"""Loopback teaching server. Tokens below are demonstration identities, not login."""
import argparse
import base64
import binascii
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).parent
TOKENS = {"Bearer alice-local-token": "alice", "Bearer bob-local-token": "bob"}


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=3)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(path):
    with connect(path) as db:
        db.executescript((ROOT / "schema.sql").read_text())
        db.executemany("INSERT OR IGNORE INTO bookmarks VALUES(?,?,?,?,?,?)", [
            ("a", "alice", "Alpha", "https://example.com/a", 100, 1),
            ("b", "alice", "Beta", "https://example.com/b", 100, 1),
            ("c", "alice", "Gamma", "https://example.com/c", 99, 1),
            ("secret", "bob", "Bob private", "https://example.com/private", 101, 1),
        ])


def record(row):
    return {k: row[k] for k in ("id", "title", "url", "created_at", "version")}


def handler(path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # client disposal does not roll back an already committed mutation

        def owner(self):
            return TOKENS.get(self.headers.get("Authorization"))

        def do_GET(self):
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/api/"):
                files = {"/": ("web/index.html", "text/html"),
                         "/app.js": ("web/app.js", "text/javascript"),
                         "/style.css": ("web/style.css", "text/css")}
                entry = files.get(parsed.path)
                if entry is None:
                    return self.reply(404, {"error": "not found"})
                source = ROOT / entry[0]
                if not source.exists():
                    return self.reply(503, {"error": "run node build.mjs first"})
                data = source.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", entry[1])
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'")
                self.end_headers()
                self.wfile.write(data)
                return
            owner = self.owner()
            if owner is None:
                return self.reply(401, {"error": "local demo token required"})
            with connect(path) as db:
                if parsed.path == "/api/bookmarks":
                    params = parse_qs(parsed.query)
                    try:
                        limit = int(params.get("limit", ["2"])[0])
                        query = params.get("q", [""])[0]
                        if not 1 <= limit <= 50 or len(query) > 200:
                            raise ValueError()
                        cursor = params.get("cursor", [None])[0]
                        args = [owner, query]
                        sql = "SELECT * FROM bookmarks WHERE owner_id=? AND instr(lower(title),lower(?))>0"
                        if cursor:
                            if len(cursor) > 1000:
                                raise ValueError()
                            stamp, ident = json.loads(base64.urlsafe_b64decode(cursor.encode()))
                            if type(stamp) is not int or abs(stamp) > 2**53 - 1 or not isinstance(ident, str):
                                raise ValueError()
                            sql += " AND (created_at,id)<(?,?)"
                            args += [stamp, ident]
                        sql += " ORDER BY created_at DESC,id DESC LIMIT ?"
                        args += [limit + 1]
                        rows = db.execute(sql, args).fetchall()
                    except (ValueError, TypeError, json.JSONDecodeError, UnicodeError, binascii.Error):
                        return self.reply(400, {"error": "invalid query or cursor"})
                    page = rows[:limit]
                    next_cursor = None
                    if len(rows) > limit:
                        last = page[-1]
                        next_cursor = base64.urlsafe_b64encode(json.dumps([last["created_at"], last["id"]]).encode()).decode()
                    return self.reply(200, {"items": [record(row) for row in page], "nextCursor": next_cursor})
                ident = parsed.path.removeprefix("/api/bookmarks/")
                row = db.execute("SELECT * FROM bookmarks WHERE id=? AND owner_id=?", (ident, owner)).fetchone()
                return self.reply(200, record(row)) if row else self.reply(404, {"error": "not found"})

        def do_PATCH(self):
            owner = self.owner()
            if owner is None:
                return self.reply(401, {"error": "local demo token required"})
            if not self.path.startswith("/api/bookmarks/"):
                return self.reply(404, {"error": "not found"})
            ident = self.path.removeprefix("/api/bookmarks/")
            key = self.headers.get("Idempotency-Key", "")
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096 or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", key):
                    raise ValueError()
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict) or set(body) != {"title", "expectedVersion"}:
                    raise ValueError()
                title, expected = body["title"], body["expectedVersion"]
                if not isinstance(title, str) or not title.strip() or len(title) > 200 or type(expected) is not int or not 1 <= expected < 2**53 - 1:
                    raise ValueError()
                title.encode("utf-8")  # reject lone surrogates before SQLite binding
                if any(unicodedata.category(ch) == "Cc" for ch in title):
                    raise ValueError("single-line title cannot contain control characters")
            except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
                return self.reply(400, {"error": "valid single-line Unicode title, integer expectedVersion and mutation key required"})
            fingerprint = hashlib.sha256(json.dumps([ident, title, expected]).encode()).hexdigest()
            try:
                with connect(path) as db:
                    db.execute("BEGIN IMMEDIATE")
                    row = db.execute("SELECT * FROM bookmarks WHERE id=? AND owner_id=?", (ident, owner)).fetchone()
                    if row is None:
                        status, result = 404, {"error": "not found"}
                    else:
                        old = db.execute("SELECT * FROM mutations WHERE owner_id=? AND mutation_id=?", (owner, key)).fetchone()
                        if old and old["fingerprint"] != fingerprint:
                            status, result = 409, {"error": "mutation key reused with different payload", "current": record(row)}
                        elif old:
                            status, result = 200, json.loads(old["response"])
                        else:
                            changed = db.execute("UPDATE bookmarks SET title=?,version=version+1 WHERE id=? AND owner_id=? AND version=?",
                                                 (title, ident, owner, expected)).rowcount
                            if not changed:
                                status, result = 409, {"error": "version conflict", "current": record(row)}
                            else:
                                status = 200
                                result = record(db.execute("SELECT * FROM bookmarks WHERE id=? AND owner_id=?", (ident, owner)).fetchone())
                                db.execute("INSERT INTO mutations VALUES(?,?,?,?)", (owner, key, fingerprint, json.dumps(result)))
                # Every outcome is chosen under the transaction; none writes to a
                # potentially slow socket until the transaction and connection end.
                return self.reply(status, result)
            except sqlite3.OperationalError as exc:
                code = getattr(exc, "sqlite_errorcode", None)
                busy = code is not None and (code & 0xff) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
                if busy or (code is None and str(exc) in ("database is locked", "database table is locked")):
                    return self.reply(503, {"error": "store busy; retry the same mutation key"})
                return self.reply(500, {"error": "store operation failed"})
    return Handler


def serve(path, port=8765):
    initialize(path)
    return ThreadingHTTPServer(("127.0.0.1", port), handler(path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(ROOT / "bookmarks.sqlite3"))
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = serve(args.db, args.port)
    print(f"Bookmark editor: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
