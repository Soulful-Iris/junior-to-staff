"""Lazily merge finite ascending integer iterables; validate as consumed."""
import heapq


def merge_streams(streams):
    iterators = [iter(stream) for stream in streams]
    heap = []

    def checked(value):
        if not isinstance(value, int):
            raise ValueError("integer values required")
        return value

    for index, iterator in enumerate(iterators):
        try:
            heap.append((checked(next(iterator)), index))
        except StopIteration:
            pass
    heapq.heapify(heap)
    while heap:
        value, index = heapq.heappop(heap)
        yield value
        try:
            following = checked(next(iterators[index]))
        except StopIteration:
            continue
        if following < value:
            raise ValueError("stream is not sorted")
        heapq.heappush(heap, (following, index))
