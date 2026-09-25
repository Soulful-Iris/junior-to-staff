class TokenBucket:
    def __init__(self, capacity, refill_per_second):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be a positive int")
        if not isinstance(refill_per_second, (int, float)) or isinstance(refill_per_second, bool) or refill_per_second <= 0:
            raise ValueError("refill rate must be positive")
        self.capacity = capacity
        self.rate = float(refill_per_second)
        self._buckets = {}  # tenant -> [tokens, last_now]

    def allow(self, tenant, now):
        bucket = self._buckets.get(tenant)
        if bucket is None:
            bucket = [float(self.capacity), float(now)]
            self._buckets[tenant] = bucket
        tokens, last = bucket
        now = max(float(now), last)
        tokens = min(float(self.capacity), tokens + (now - last) * self.rate)
        admitted = tokens >= 1.0 - 1e-9
        if admitted:
            tokens -= 1.0
        bucket[0], bucket[1] = tokens, now
        return admitted
