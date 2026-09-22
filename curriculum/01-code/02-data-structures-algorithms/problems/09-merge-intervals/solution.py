def _intervals(intervals):
    if not isinstance(intervals, (list, tuple)):
        raise ValueError("expected a list or tuple of intervals")
    for pair in intervals:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or any(type(x) is not int for x in pair) or pair[0] >= pair[1]):
            raise ValueError("intervals require integer start < end")

def merge_intervals(intervals):
    _intervals(intervals)
    result = []
    for start, end in sorted(intervals, key=lambda pair: (pair[0], pair[1])):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result
