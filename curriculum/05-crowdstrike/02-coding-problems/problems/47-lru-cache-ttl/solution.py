import time
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity, clock=None):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be a positive int")
        self.capacity = capacity
        self.clock = clock or time.monotonic
        self._items = OrderedDict()  # key -> (value, expires_at or None)

    def _expired(self, key):
        _, expires_at = self._items[key]
        return expires_at is not None and self.clock() >= expires_at

    def get(self, key):
        if key not in self._items:
            return None
        if self._expired(key):
            del self._items[key]
            return None
        self._items.move_to_end(key)
        return self._items[key][0]

    def put(self, key, value, ttl=None):
        if ttl is not None and (not isinstance(ttl, (int, float)) or isinstance(ttl, bool) or ttl <= 0):
            raise ValueError("ttl must be a positive number or None")
        expires_at = None if ttl is None else self.clock() + ttl
        if key in self._items:
            self._items[key] = (value, expires_at)
            self._items.move_to_end(key)
            return
        if len(self._items) >= self.capacity:
            oldest = next(iter(self._items))
            if self._expired(oldest):
                del self._items[oldest]
            else:
                self._items.popitem(last=False)
        self._items[key] = (value, expires_at)

    def size(self):
        for key in [k for k in self._items if self._expired(k)]:
            del self._items[key]
        return len(self._items)
