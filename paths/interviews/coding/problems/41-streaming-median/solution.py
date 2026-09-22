"""Exact median of all inserted integers using two balanced heaps."""
from fractions import Fraction
import heapq


class StreamingMedian:
    def __init__(self):
        self.low, self.high = [], []

    def add(self, value):
        if not isinstance(value, int):
            raise ValueError("integer observations required")
        if not self.low or value <= -self.low[0]:
            heapq.heappush(self.low, -value)
        else:
            heapq.heappush(self.high, value)
        if len(self.low) > len(self.high) + 1:
            heapq.heappush(self.high, -heapq.heappop(self.low))
        elif len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def median(self):
        if not self.low:
            raise ValueError("median of empty stream")
        if len(self.low) > len(self.high):
            return Fraction(-self.low[0])
        return Fraction(-self.low[0] + self.high[0], 2)
