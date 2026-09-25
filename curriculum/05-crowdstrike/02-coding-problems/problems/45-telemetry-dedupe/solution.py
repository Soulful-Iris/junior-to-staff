from collections import deque


class Deduper:
    """Emit each (sensor_id, seq) once within a sliding window of event time."""

    def __init__(self, window_seconds):
        if not isinstance(window_seconds, (int, float)) or isinstance(window_seconds, bool) or window_seconds <= 0:
            raise ValueError("window must be a positive number")
        self.window = window_seconds
        self.now = None
        self.seen = {}      # key -> newest sighting ts
        self.order = deque()  # (ts, key) in arrival order

    def accept(self, sensor_id, seq, ts):
        if not isinstance(seq, int) or isinstance(seq, bool):
            raise ValueError("seq must be an int")
        self.now = ts if self.now is None else max(self.now, ts)
        self._evict()
        key = (sensor_id, seq)
        if ts <= self.now - self.window:
            return False  # too old to emit or remember
        if key in self.seen:
            self.seen[key] = max(self.seen[key], ts)
            return False
        self.seen[key] = ts
        self.order.append((ts, key))
        return True

    def _evict(self):
        cutoff = self.now - self.window
        while self.order and self.order[0][0] <= cutoff:
            _, key = self.order.popleft()
            newest = self.seen.get(key)
            if newest is not None and newest <= cutoff:
                del self.seen[key]
            elif newest is not None:
                self.order.append((newest, key))  # a later sighting keeps it alive

    def size(self):
        return len(self.seen)
