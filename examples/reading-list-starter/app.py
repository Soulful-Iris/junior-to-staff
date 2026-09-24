"""Local teaching API. Python 3.12+, standard library, no cloud resources.

Run: python3 examples/reading-list-starter/app.py --db /tmp/reading-list.sqlite3
Demo identity is NOT authentication. This server binds only to loopback.
Title lookup is a controlled fixture; it never fetches submitted URLs.
"""
import argparse
from contextlib import contextmanager
import json
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MEMBERS = {"alice", "bob"}


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(path):
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY, owner TEXT NOT NULL, url TEXT NOT NULL,
            title TEXT, title_status TEXT NOT NULL DEFAULT 'pending',
            note TEXT NOT NULL DEFAULT '', version INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS reading_state (
            bookmark_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,
            member TEXT NOT NULL, is_read INTEGER NOT NULL,
            PRIMARY KEY (bookmark_id, member)
        );
        """)


def lookup_title(mode):
    """Replace this fixture with a bounded, SSRF-safe adapter in that exercise."""
    if mode == "timeout":
        time.sleep(0.5)
        return None, "timeout"
    return "Example documentation", "ready"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        # Avoid logging request paths or URL query strings in the starter.
        pass

    def reply(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 16384:
            raise ValueError("Send a JSON body of 1 to 16384 bytes")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        return value

    def dispatch(self):
        # Intentional instrumentation boundary for the tracing exercise.
        self.connection.settimeout(5)
        member = self.headers.get("X-Demo-User")
        if member not in MEMBERS:
            return self.reply(401, {"error": "Use X-Demo-User: alice or bob locally"})
        route = urlsplit(self.path).path.strip("/").split("/")
        if route[0] != "bookmarks":
            return self.reply(404, {"error": "Unknown route"})
        try:
            if self.command == "GET" and route == ["bookmarks"]:
                with connect(self.server.db_path) as db:
                    rows = db.execute("""SELECT b.*, COALESCE(r.is_read, 0) AS is_read
                        FROM bookmarks b LEFT JOIN reading_state r
                        ON r.bookmark_id=b.id AND r.member=? ORDER BY b.id""", (member,))
                    items = [dict(row, is_read=bool(row["is_read"])) for row in rows]
                return self.reply(200, {"items": items})
            if self.command == "POST" and route == ["bookmarks"]:
                data = self.body()
                url = data.get("url")
                mode = data.get("title_mode", "ok")
                if not isinstance(url, str) or len(url) > 2048 or urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).hostname:
                    raise ValueError("url must be an HTTP(S) URL of at most 2048 characters")
                if mode not in {"ok", "timeout"}:
                    raise ValueError("title_mode must be ok or timeout")
                with connect(self.server.db_path) as db:
                    item_id = db.execute("INSERT INTO bookmarks(owner,url) VALUES (?,?)", (member, url)).lastrowid
                # Save commits before enrichment. A failed title never loses the URL.
                title, outcome = lookup_title(mode)
                with connect(self.server.db_path) as db:
                    db.execute("UPDATE bookmarks SET title=?,title_status=? WHERE id=?", (title, outcome, item_id))
                    item = dict(db.execute("SELECT * FROM bookmarks WHERE id=?", (item_id,)).fetchone())
                return self.reply(201, item)
            if len(route) >= 2 and route[1].isdigit():
                item_id = int(route[1])
                data = self.body() if self.command == "PATCH" else {}
                with connect(self.server.db_path) as db:
                    if self.command == "PATCH" and len(route) == 3 and route[2] == "read":
                        if not isinstance(data.get("is_read"), bool):
                            raise ValueError("is_read must be a boolean")
                        if not db.execute("SELECT 1 FROM bookmarks WHERE id=?", (item_id,)).fetchone():
                            return self.reply(404, {"error": "Unknown bookmark"})
                        db.execute("""INSERT INTO reading_state VALUES (?,?,?)
                            ON CONFLICT(bookmark_id,member) DO UPDATE SET is_read=excluded.is_read""", (item_id, member, data["is_read"]))
                        result = {"id": item_id, "is_read": data["is_read"]}
                    elif self.command == "PATCH" and len(route) == 2:
                        if not isinstance(data.get("note"), str) or len(data["note"]) > 4000 or type(data.get("version")) is not int:
                            raise ValueError("Send note (up to 4000 characters) and integer version")
                        row = db.execute("SELECT owner,version FROM bookmarks WHERE id=?", (item_id,)).fetchone()
                        if not row or row["owner"] != member:
                            return self.reply(404, {"error": "Bookmark not editable by this member"})
                        changed = db.execute("UPDATE bookmarks SET note=?,version=version+1 WHERE id=? AND owner=? AND version=?", (data["note"], item_id, member, data["version"])).rowcount
                        if not changed:
                            return self.reply(409, {"error": "Version conflict; refresh before editing"})
                        result = dict(db.execute("SELECT * FROM bookmarks WHERE id=?", (item_id,)).fetchone())
                    else:
                        return self.reply(404, {"error": "Unknown route"})
                return self.reply(200, result)
            return self.reply(404, {"error": "Unknown route"})
        except (ValueError, json.JSONDecodeError) as error:
            return self.reply(400, {"error": str(error)})
        except sqlite3.OperationalError:
            return self.reply(503, {"error": "Store unavailable; no success promised"})

    do_GET = dispatch
    do_POST = dispatch
    do_PATCH = dispatch


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="/tmp/reading-list.sqlite3")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    initialize(args.db)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.db_path = args.db
    print(f"Reading-list API: http://127.0.0.1:{server.server_port}; SQLite: {args.db}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
