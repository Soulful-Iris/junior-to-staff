import json
from pathlib import Path
import sys
import tempfile
from threading import Event, Thread
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import serve, connect


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "bookmarks.db")
        self.server = serve(self.db, 0)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, body=None, key="test-key", token="alice-local-token"):
        headers = {"Authorization": "Bearer " + token, "Idempotency-Key": key, "Content-Type": "application/json"}
        request = urllib.request.Request(self.url + path, data=None if body is None else json.dumps(body).encode(),
                                         headers=headers, method="GET" if body is None else "PATCH")
        try:
            response = urllib.request.urlopen(request, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_owner_enforced_for_reads_writes_and_missing_auth(self):
        self.assertEqual(self.request("/api/bookmarks/secret")[0], 404)
        self.assertEqual(self.request("/api/bookmarks/secret", {"title":"stolen", "expectedVersion":1})[0], 404)
        self.assertEqual(self.request("/api/bookmarks", token="invalid")[0], 401)
        code, page = self.request("/api/bookmarks", token="bob-local-token")
        self.assertEqual([row["id"] for row in page["items"]], ["secret"])

    def test_tied_cursor_complete_without_repeats(self):
        seen, cursor = [], None
        for _ in range(4):
            code, page = self.request("/api/bookmarks?limit=1" + ("&cursor=" + cursor if cursor else ""))
            self.assertEqual(code, 200)
            seen += [item["id"] for item in page["items"]]
            cursor = page["nextCursor"]
            if cursor is None:
                break
        self.assertEqual(seen, ["b", "a", "c"])

    def test_conditional_update_duplicate_response_and_durable_store(self):
        body = {"title": "A", "expectedVersion": 1}
        code, first = self.request("/api/bookmarks/b", body)
        self.assertEqual((code, first["version"]), (200, 2))
        self.assertEqual(self.request("/api/bookmarks/b", body), (200, first))
        code, conflict = self.request("/api/bookmarks/b", {"title":"B", "expectedVersion":1}, key="second")
        self.assertEqual((code, conflict["current"]["title"]), (409, "A"))
        self.assertEqual(self.request("/api/bookmarks/b", {"title":"other", "expectedVersion":2})[0], 409)
        with connect(self.db) as db:
            self.assertEqual(tuple(db.execute("SELECT title,version FROM bookmarks WHERE id='b'").fetchone()), ("A", 2))
            self.assertEqual(db.execute("SELECT count(*) FROM mutations").fetchone()[0], 1)

    def test_concurrent_writers_only_one_wins(self):
        from threading import Barrier
        gate, results = Barrier(3), []
        def writer(name):
            gate.wait()
            results.append(self.request("/api/bookmarks/b", {"title":name, "expectedVersion":1}, key=name)[0])
        threads = [Thread(target=writer, args=(name,)) for name in ("one", "two")]
        for thread in threads:
            thread.start()
        gate.wait()
        for thread in threads:
            thread.join(3)
        self.assertEqual(sorted(results), [200, 409])

    def test_runtime_validation_and_empty_search(self):
        for body in [{"title":"", "expectedVersion":1}, {"title":"A", "expectedVersion":True}, {"title":"A"},
                     {"title":"A" + " " * 200, "expectedVersion":1}, {"title":"A", "expectedVersion":10**100}]:
            self.assertEqual(self.request("/api/bookmarks/b", body)[0], 400)
        for query in ["limit=0", "limit=51", "cursor=bad", "cursor=W10="]:
            self.assertEqual(self.request("/api/bookmarks?" + query)[0], 400)
        self.assertEqual(self.request("/api/bookmarks?q=notpresent")[1]["items"], [])

    def test_unicode_validation_and_durable_idempotence(self):
        for title in ("\0abc", "a\0bc", "\ud800", "line\nbreak", "\u0085"):
            code, body = self.request("/api/bookmarks/b", {"title": title, "expectedVersion": 1})
            self.assertEqual(code, 400)
            self.assertIn("error", body)
        with connect(self.db) as db:
            self.assertEqual(tuple(db.execute("SELECT title,version FROM bookmarks WHERE id='b'").fetchone()), ("Beta", 1))
            self.assertEqual(db.execute("SELECT count(*) FROM mutations").fetchone()[0], 0)
        body = {"title": "Café 👩‍💻", "expectedVersion": 1}
        first = self.request("/api/bookmarks/b", body)
        self.assertEqual((first[0], first[1]["title"], first[1]["version"]), (200, body["title"], 2))
        self.assertEqual(self.request("/api/bookmarks/b", body), first)

    def test_slow_conflict_response_releases_write_transaction(self):
        self.request("/api/bookmarks/b", {"title": "first", "expectedVersion": 1}, key="first")
        entered, release, writer_done = Event(), Event(), Event()
        handler = self.server.RequestHandlerClass
        original = handler.reply
        results, errors = [], []
        def gated_reply(request, status, body):
            if status == 409:
                entered.set()
                if not release.wait(3):
                    raise TimeoutError("conflict response gate")
            return original(request, status, body)
        handler.reply = gated_reply
        def request_in_thread(body, key, done=None):
            try:
                results.append((key, self.request("/api/bookmarks/b", body, key=key)[0]))
            except Exception as exc:
                errors.append(exc)
            finally:
                if done:
                    done.set()
        conflict = Thread(target=request_in_thread, args=({"title": "stale", "expectedVersion": 1}, "stale"))
        writer = Thread(target=request_in_thread, args=({"title": "next", "expectedVersion": 2}, "next", writer_done))
        conflict.start()
        try:
            self.assertTrue(entered.wait(2))
            writer.start()
            self.assertTrue(writer_done.wait(2), "slow response retained a write transaction")
        finally:
            release.set()
            conflict.join(3)
            if writer.ident is not None:
                writer.join(3)
            handler.reply = original
        self.assertEqual(errors, [])
        self.assertEqual(sorted(results), [("next", 200), ("stale", 409)])


if __name__ == "__main__":
    unittest.main()
