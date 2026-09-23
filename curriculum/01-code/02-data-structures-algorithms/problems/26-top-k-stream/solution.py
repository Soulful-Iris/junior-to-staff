"""Keep the k largest observed integers, including duplicate observations."""
import heapq


class TopK:
    def __init__(self, k):
        if not isinstance(k, int) or k < 0:
            raise ValueError("k must be a nonnegative integer")
        self.k = k
        self._top_k = []

    def add(self, value):
        if not isinstance(value, int):
            raise ValueError("integer observations required")
        if self.k == 0:
            return
        if len(self._top_k) < self.k:
            heapq.heappush(self._top_k, value)
        elif value > self._top_k[0]:
            heapq.heapreplace(self._top_k, value)

    def largest(self):
        return sorted(self._top_k, reverse=True)
