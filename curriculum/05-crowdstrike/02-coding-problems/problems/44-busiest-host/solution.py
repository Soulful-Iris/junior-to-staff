import heapq
from collections import Counter, deque


def _check_record(record):
    if not isinstance(record, tuple) or len(record) != 2:
        raise ValueError("records must be (host, timestamp) tuples")
    return record


def busiest(records):
    counts = Counter(_check_record(r)[0] for r in records)
    if not counts:
        return None
    return min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]


def top_k(records, k):
    if not isinstance(k, int) or isinstance(k, bool) or k < 0:
        raise ValueError("k must be a non-negative integer")
    counts = Counter(_check_record(r)[0] for r in records)
    smallest = heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [host for host, _ in smallest]


class TopKWindow:
    """Top-k hosts among records newer than now - window, where now is the largest timestamp seen."""

    def __init__(self, k, window_seconds):
        if not isinstance(k, int) or isinstance(k, bool) or k < 0 or window_seconds <= 0:
            raise ValueError("k must be non-negative and the window positive")
        self.k = k
        self.window = window_seconds
        self.now = None
        self.events = deque()
        self.counts = Counter()

    def add(self, host, ts):
        self.now = ts if self.now is None else max(self.now, ts)
        if ts > self.now - self.window:
            self.events.append((ts, host))
            self.counts[host] += 1
        self._evict()

    def _evict(self):
        cutoff = self.now - self.window
        while self.events and self.events[0][0] <= cutoff:
            _, host = self.events.popleft()
            self.counts[host] -= 1
            if self.counts[host] == 0:
                del self.counts[host]

    def current(self):
        smallest = heapq.nsmallest(self.k, self.counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return [host for host, _ in smallest]
