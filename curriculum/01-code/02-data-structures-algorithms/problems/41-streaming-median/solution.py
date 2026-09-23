"""Exact median of all inserted integers using two balanced heaps."""
from fractions import Fraction
import heapq


class StreamingMedian:
    def __init__(self):
        self.lower_half, self.upper_half = [], []

    def add(self, value):
        if not isinstance(value, int):
            raise ValueError("integer observations required")
        if not self.lower_half or value <= -self.lower_half[0]:
            heapq.heappush(self.lower_half, -value)
        else:
            heapq.heappush(self.upper_half, value)
        if len(self.lower_half) > len(self.upper_half) + 1:
            heapq.heappush(self.upper_half, -heapq.heappop(self.lower_half))
        elif len(self.upper_half) > len(self.lower_half):
            heapq.heappush(self.lower_half, -heapq.heappop(self.upper_half))

    def median(self):
        if not self.lower_half:
            raise ValueError("median of empty stream")
        if len(self.lower_half) > len(self.upper_half):
            return Fraction(-self.lower_half[0])
        return Fraction(-self.lower_half[0] + self.upper_half[0], 2)
