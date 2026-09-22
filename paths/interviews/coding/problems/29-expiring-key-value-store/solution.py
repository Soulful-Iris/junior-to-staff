"""Single-process TTL dictionary with injected monotonic clock and explicit purge."""
import math
import time


class ExpiringStore:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._entries = {}

    def set(self, key, value, ttl):
        if not isinstance(ttl, (int, float)) or not math.isfinite(ttl) or ttl < 0:
            raise ValueError("finite nonnegative TTL required")
        if ttl == 0:
            self._entries.pop(key, None)
            return
        deadline = self.clock() + ttl
        if not math.isfinite(deadline):
            raise ValueError("expiration must be finite")
        self._entries[key] = value, deadline

    def get(self, key):
        value, deadline = self._entries[key]
        if self.clock() >= deadline:
            del self._entries[key]
            raise KeyError(key)
        return value

    def delete(self, key):
        try:
            self.get(key)
        except KeyError:
            return False
        del self._entries[key]
        return True

    def purge(self):
        """Remove all entries expired at one clock reading; return removed count."""
        now = self.clock()
        expired = [key for key, (_, deadline) in self._entries.items() if now >= deadline]
        for key in expired:
            del self._entries[key]
        return len(expired)
