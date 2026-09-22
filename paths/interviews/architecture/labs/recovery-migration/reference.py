"""Local protocol boundaries: real SQLite atomic intent; simulated remote failures."""
from dataclasses import dataclass
import hashlib
import json
import sqlite3


class Conflict(Exception):
    pass


class HistoryExpired(Exception):
    pass


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class FencedResult:
    """One atomic storage boundary; clock represents authoritative lease time."""
    def __init__(self):
        self.epoch = 0
        self.until = 0
        self.result = None

    def claim(self, now, ttl=5):
        if now < self.until:
            raise Conflict("lease held")
        self.epoch += 1
        self.until = now + ttl
        return self.epoch

    def complete(self, epoch, now, result):
        if epoch != self.epoch or now >= self.until:
            raise Conflict("stale or expired owner")
        self.result = result


class Provider:
    def __init__(self):
        self.receipts = {}
        self.effects = 0
        self.available = True
        self.lose_next_response = False

    def send(self, operation_id, payload):
        if not self.available:
            raise TimeoutError("provider unavailable")
        identity = digest(payload)
        previous = self.receipts.get(operation_id)
        if previous and previous[0] != identity:
            raise Conflict("same ID, changed intent")
        if previous is None:
            self.effects += 1
            self.receipts[operation_id] = (identity, f"receipt-{self.effects}")
        if self.lose_next_response:
            self.lose_next_response = False
            raise TimeoutError("effect happened, response lost")
        return self.receipts[operation_id][1]


class IntentStore:
    """Business row + outbox are committed together in a real local transaction."""
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE intent(id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE outbox(id TEXT PRIMARY KEY REFERENCES intent(id), state TEXT NOT NULL, receipt TEXT);
        """)

    def close(self):
        self.db.close()

    def accept(self, operation_id, payload, crash_before_commit=False):
        with self.db:
            old = self.db.execute("SELECT digest FROM intent WHERE id=?", (operation_id,)).fetchone()
            if old:
                if old[0] != digest(payload):
                    raise Conflict("quarantine changed intent")
                return "duplicate"
            self.db.execute("INSERT INTO intent VALUES (?,?,?)", (operation_id, digest(payload), json.dumps(payload)))
            if crash_before_commit:
                raise RuntimeError("crash: transaction rolls back")
            self.db.execute("INSERT INTO outbox VALUES (?, 'pending', NULL)", (operation_id,))
        return "accepted"

    def dispatch(self, operation_id, provider, crash_after_send=False):
        payload, state = self.db.execute("SELECT payload,state FROM intent JOIN outbox USING(id) WHERE id=?", (operation_id,)).fetchone()
        if state == "done":
            return "done"
        try:
            receipt = provider.send(operation_id, json.loads(payload))
        except TimeoutError:
            with self.db:
                self.db.execute("UPDATE outbox SET state='uncertain' WHERE id=?", (operation_id,))
            return "uncertain"
        if crash_after_send:
            raise RuntimeError("crash before local receipt")
        with self.db:
            self.db.execute("UPDATE outbox SET state='done', receipt=? WHERE id=?", (receipt, operation_id))
        return "done"


@dataclass(frozen=True)
class Row:
    version: int
    value: str | None
    deleted: bool = False


def apply(rows, key, row):
    previous = rows.get(key)
    if previous is not None and previous.version == row.version and previous != row:
        raise Conflict("same version has different contents")
    if previous is None or row.version > previous.version:
        rows[key] = row


class ChangeSource:
    """Single-thread atomic source mutation + log model, not an actual CDC client."""
    def __init__(self):
        self.rows, self.log = {}, []
        self.sequence = self.retained_after = 0

    def write(self, key, value=None, deleted=False):
        version = self.rows[key].version + 1 if key in self.rows else 1
        row = Row(version, value, deleted)
        self.sequence += 1
        self.rows[key] = row
        self.log.append((self.sequence, key, row))
        return row

    def snapshot(self):
        # In a real source, snapshot and position must describe the SAME database state.
        return dict(self.rows), self.sequence

    def events_after(self, checkpoint):
        if checkpoint < self.retained_after:
            raise HistoryExpired("resnapshot required before continuing")
        return [event for event in self.log if event[0] > checkpoint]

    def expire_through(self, sequence):
        self.log = [event for event in self.log if event[0] > sequence]
        self.retained_after = sequence


class Replica:
    def __init__(self):
        self.rows, self.checkpoint = {}, 0

    def resume(self, source, crash_after_apply=False):
        for sequence, key, row in source.events_after(self.checkpoint):
            apply(self.rows, key, row)
            if crash_after_apply:
                raise RuntimeError("row durable, checkpoint not yet advanced")
            self.checkpoint = sequence

    def resnapshot(self, source):
        self.rows, self.checkpoint = source.snapshot()

    def differences(self, source):
        return {key for key in self.rows.keys() | source.rows.keys() if self.rows.get(key) != source.rows.get(key)}


class RoutingRegistry:
    def __init__(self):
        self.epoch, self.owner = 1, "old"

    def cutover(self, target, source):
        if target.checkpoint != source.sequence or target.differences(source):
            raise Conflict("cutover requires full reconciliation at write barrier")
        # A real implementation atomically fences old writes and changes authority.
        self.epoch += 1
        self.owner = "new"

    def check_write(self, owner, epoch):
        if owner != self.owner or epoch != self.epoch:
            raise Conflict("refresh routing; stale authority")


def rollback_ready(old_rows, new_rows):
    return old_rows == new_rows
