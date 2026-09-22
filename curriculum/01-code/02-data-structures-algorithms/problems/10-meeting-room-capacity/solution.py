def _intervals(intervals):
    if not isinstance(intervals, (list, tuple)):
        raise ValueError("expected a list or tuple of intervals")
    for pair in intervals:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or any(type(x) is not int for x in pair) or pair[0] >= pair[1]):
            raise ValueError("intervals require integer start < end")

def meeting_room_capacity(intervals):
    _intervals(intervals)
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    active = best = 0
    for _, delta in sorted(events):
        active += delta
        best = max(best, active)
    return best
