"""Explicit-watermark tumbling counts with a fixed allowed-lateness duration."""


class TumblingCounter:
    def __init__(self, width, allowed_lateness=0):
        if not isinstance(width, int) or width <= 0:
            raise ValueError("positive integer width required")
        if not isinstance(allowed_lateness, int) or allowed_lateness < 0:
            raise ValueError("nonnegative integer lateness required")
        self.width, self.allowed_lateness = width, allowed_lateness
        self.watermark = None
        self._counts = {}

    def add(self, timestamp):
        if not isinstance(timestamp, int):
            raise ValueError("integer event timestamp required")
        start = (timestamp // self.width) * self.width
        close_at = start + self.width + self.allowed_lateness
        if self.watermark is not None and close_at <= self.watermark:
            return False
        self._counts[start] = self._counts.get(start, 0) + 1
        return True

    def advance_watermark(self, watermark):
        if not isinstance(watermark, int):
            raise ValueError("integer watermark required")
        if self.watermark is not None and watermark < self.watermark:
            raise ValueError("watermark cannot decrease")
        self.watermark = watermark
        closed = sorted(start for start in self._counts
                        if start + self.width + self.allowed_lateness <= watermark)
        return [(start, start + self.width, self._counts.pop(start)) for start in closed]
