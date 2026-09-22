import json
from pathlib import Path
import sys
import tempfile
from threading import Thread
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


if __name__ == "__main__":
    unittest.main()
