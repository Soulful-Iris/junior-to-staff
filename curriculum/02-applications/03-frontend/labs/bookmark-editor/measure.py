"""Reproducible query measurement; numbers are local observations, not SLOs."""
import json
from pathlib import Path
import platform
import sqlite3
from statistics import median
import tempfile
from time import perf_counter


def measure():
    with tempfile.TemporaryDirectory() as folder:
        db = sqlite3.connect(Path(folder) / "profile.db")
        db.executescript((Path(__file__).parent / "schema.sql").read_text())
        db.execute("DROP INDEX bookmarks_owner_created_id")
        db.executemany("INSERT INTO bookmarks VALUES(?,?,?,?,?,?)", (
            (f"{i:07}", "alice" if i < 90000 else f"tenant{i % 1000}", f"Bookmark {i}", "https://example.com", i // 10, 1)
            for i in range(100000)))
        db.commit()
        sql = "SELECT id,title,version FROM bookmarks WHERE owner_id=? AND (created_at,id)<(?,?) ORDER BY created_at DESC,id DESC LIMIT 50"
        args = ("alice", 8000, "0080000")
        result = {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version, "rows": 100000,
                  "workload": "90% Alice; tied timestamp groups of ten; page limit 50; 15 warm queries"}
        baseline = None
        for label in ("before", "after"):
            if label == "after":
                db.execute("CREATE INDEX bookmarks_owner_created_id ON bookmarks(owner_id,created_at DESC,id DESC)")
                db.execute("ANALYZE")
            plan = [row[-1] for row in db.execute("EXPLAIN QUERY PLAN " + sql, args)]
            timings = []
            for _ in range(15):
                start = perf_counter()
                rows = db.execute(sql, args).fetchall()
                timings.append((perf_counter() - start) * 1000)
            if baseline is None:
                baseline = rows
            assert rows == baseline and len(rows) == 50
            result[label] = {"median_ms": round(median(timings), 3), "plan": plan}
        db.close()
        return result


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2))
