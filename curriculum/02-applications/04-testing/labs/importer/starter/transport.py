"""Injected transport owns timeout enforcement; importer owns the total budget."""
class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.waits = []

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


class FakeServer:
    def __init__(self, responses, clock):
        self.responses, self.clock, self.calls = responses, clock, []
        self.counts = {}

    def get(self, cursor, timeout):
        key = cursor if cursor is not None else "START"
        self.calls.append((key, self.clock.now, timeout))
        count = self.counts.get(key, 0)
        options = self.responses[key]
        response = options[min(count, len(options) - 1)]
        self.counts[key] = count + 1
        elapsed = response.get("elapsed", 0)
        self.clock.now += min(elapsed, timeout)
        if elapsed >= timeout:
            raise TimeoutError("request deadline")
        return response


def fetch(server, clock, cursor, deadline, attempts=3):
    for attempt in range(attempts):
        remaining = deadline - clock.now
        if remaining <= 0:
            raise TimeoutError("total deadline")
        response = server.get(cursor, timeout=remaining)
        if clock.now >= deadline:
            raise TimeoutError("total deadline")
        status = response["status"]
        if status == 200:
            return response["body"]
        if status not in (429, 500, 502, 503, 504):
            raise ValueError(f"non-retryable HTTP {status}")
        if attempt == attempts - 1:
            raise TimeoutError("attempt budget exhausted")
        # This exercise's API specifies numeric seconds, not HTTP-date syntax.
        delay = 0.0  # TODO: honor service backoff
        if isinstance(delay, bool) or not isinstance(delay, (int, float)) or not 0 <= delay < float("inf"):
            raise ValueError("invalid Retry-After")
        if clock.now + delay >= deadline:
            raise TimeoutError("retry exceeds total deadline")
        clock.sleep(delay)
    raise AssertionError("unreachable")
