"""Bounded FIFO with condition predicate loops, deadlines, and explicit shutdown."""
from collections import deque
import math
import threading
import time


class QueueClosed(Exception):
    pass


class BoundedBlockingQueue:
    def __init__(self, capacity, *, condition=None):
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("positive integer capacity required")
        self.capacity = capacity
        self._items = deque()
        self._closed = False
        self._condition = condition if condition is not None else threading.Condition()

    @staticmethod
    def _deadline(timeout):
        if timeout is None:
            return None
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0:
            raise ValueError("finite nonnegative timeout required")
        return time.monotonic() + timeout

    def _wait(self, deadline):
        if deadline is None:
            self._condition.wait()
        else:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("queue operation timed out")
            self._condition.wait(min(remaining, threading.TIMEOUT_MAX))

    def put(self, item, timeout=None):
        deadline = self._deadline(timeout)
        with self._condition:
            while len(self._items) == self.capacity and not self._closed:
                self._wait(deadline)
            if self._closed:
                raise QueueClosed("queue is closed")
            self._items.append(item)
            self._condition.notify_all()

    def get(self, timeout=None):
        deadline = self._deadline(timeout)
        with self._condition:
            while not self._items and not self._closed:
                self._wait(deadline)
            if not self._items:
                raise QueueClosed("closed queue is drained")
            item = self._items.popleft()
            self._condition.notify_all()
            return item

    def shutdown(self, *, cancel_pending=False):
        """First call chooses drain or cancel; return removed items on cancellation."""
        with self._condition:
            if self._closed:
                return []
            self._closed = True
            cancelled = list(self._items) if cancel_pending else []
            if cancel_pending:
                self._items.clear()
            self._condition.notify_all()
            return cancelled
