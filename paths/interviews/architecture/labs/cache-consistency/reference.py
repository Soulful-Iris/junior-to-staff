"""Deterministic in-process boundary model, not a Redis or fleet-lock client."""
import asyncio
from collections import deque


class Unavailable(Exception):
    pass


class Clock:
    def __init__(self):
        self.now = 0.0

    def advance(self, seconds):
        self.now += seconds


class OriginBudget:
    """Shared model of atomic admission: rolling one-second cap plus in-flight cap."""
    def __init__(self, clock, per_second=100, concurrent=10):
        self.clock, self.per_second, self.concurrent = clock, per_second, concurrent
        self.starts = deque()
        self.active = self.peak = self.total = 0

    def enter(self):
        while self.starts and self.starts[0] <= self.clock.now - 1:
            self.starts.popleft()
        if len(self.starts) >= self.per_second or self.active >= self.concurrent:
            raise Unavailable("origin admission exhausted")
        self.starts.append(self.clock.now)
        self.active += 1
        self.total += 1
        self.peak = max(self.peak, self.active)

    def leave(self):
        self.active -= 1


class CacheAside:
    def __init__(self, clock, budget, ttl=5):
        self.clock, self.budget, self.ttl = clock, budget, ttl
        self.values, self.flights = {}, {}
        self.cache_available = True

    async def get(self, key, loader):
        cached = self.values.get(key) if self.cache_available else None
        if cached and self.clock.now < cached[0]:
            return cached[1]
        task = self.flights.get(key)
        if task is None:
            task = asyncio.create_task(self._load(key, loader))
            self.flights[key] = task
            # Retrieve even an unobserved exception if every waiter leaves.
            task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        # A disconnected waiter must not cancel work shared with other waiters.
        return await asyncio.shield(task)

    async def _load(self, key, loader):
        entered = False
        try:
            self.budget.enter()
            entered = True
            value = await loader(key)
            if self.cache_available:
                self.values[key] = (self.clock.now + self.ttl, value)
            return value
        finally:
            if entered:
                self.budget.leave()
            self.flights.pop(key, None)


def sticky_read(primary, replica, now, pin_until):
    return primary if now < pin_until else replica


def strict_read(primary, replica, minimum_version):
    if replica is not None and replica >= minimum_version:
        return replica
    if primary is not None and primary >= minimum_version:
        return primary
    raise Unavailable("no source has the session watermark")


class LinkDelivery:
    """Explicitly separate authorization-decision age from object cache age."""
    def __init__(self, clock, policy="immediate", auth_ttl=5):
        if policy not in {"immediate", "bounded"}:
            raise ValueError(policy)
        self.clock, self.policy, self.auth_ttl = clock, policy, auth_ttl
        self.tokens = {"A": ("tenant-a", "schedule-1"), "B": ("tenant-b", "schedule-1")}
        self.objects = {("tenant-a", "schedule-1"): "Ana 09:00", ("tenant-b", "schedule-1"): "Ben 10:00"}
        self.decisions, self.cache = {}, {}
        self.auth_available = self.origin_available = True
        self.origin_calls = 0

    def get(self, token):
        decision = self.decisions.get(token)
        fresh = self.policy == "bounded" and decision and self.clock.now < decision[0]
        if fresh:
            identity = decision[1]
        else:
            if not self.auth_available:
                return 503, None  # Never extend an expired decision during outage.
            identity = self.tokens.get(token)
            if identity is None:
                return 403, None
            self.decisions[token] = (self.clock.now + self.auth_ttl, identity)
        # Authorization precedes EVERY object-cache lookup; identity scopes bytes.
        if identity in self.cache:
            return 200, self.cache[identity]
        if not self.origin_available:
            return 503, None
        self.origin_calls += 1
        value = self.objects[identity]
        self.cache[identity] = value
        return 200, value
