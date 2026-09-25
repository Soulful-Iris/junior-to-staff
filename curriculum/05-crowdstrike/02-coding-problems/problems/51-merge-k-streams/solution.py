import heapq


def merge(streams):
    iterators = [iter(s) for s in streams]
    heap = []
    last_ts = [None] * len(iterators)

    def advance(i):
        try:
            ts, payload = next(iterators[i])
        except StopIteration:
            return
        if last_ts[i] is not None and ts < last_ts[i]:
            raise ValueError(f"stream {i} is out of order at {ts}")
        last_ts[i] = ts
        heapq.heappush(heap, (ts, i, payload))

    for i in range(len(iterators)):
        advance(i)
    while heap:
        ts, i, payload = heapq.heappop(heap)
        yield ts, payload
        advance(i)
