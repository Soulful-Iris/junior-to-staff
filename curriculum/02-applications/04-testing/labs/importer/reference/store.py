import sqlite3


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS transactions(id TEXT PRIMARY KEY, cents INTEGER NOT NULL, currency TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS progress(singleton INTEGER PRIMARY KEY CHECK(singleton=1), cursor TEXT, done INTEGER NOT NULL);
          INSERT OR IGNORE INTO progress VALUES(1,NULL,0);
        """)

    def checkpoint(self):
        return self.db.execute("SELECT cursor,done FROM progress WHERE singleton=1").fetchone()

    def persist(self, rows):
        with self.db:
            for row in rows:
                old = self.db.execute("SELECT id,cents,currency FROM transactions WHERE id=?", (row[0],)).fetchone()
                if old is not None and old != row:
                    raise ValueError("duplicate id with conflicting payload")
                self.db.execute("INSERT OR IGNORE INTO transactions VALUES(?,?,?)", row)

    def advance(self, cursor):
        with self.db:
            self.db.execute("UPDATE progress SET cursor=?,done=? WHERE singleton=1", (cursor, cursor is None))

    def rows(self):
        return self.db.execute("SELECT id,cents,currency FROM transactions ORDER BY id").fetchall()

    def close(self):
        self.db.close()
