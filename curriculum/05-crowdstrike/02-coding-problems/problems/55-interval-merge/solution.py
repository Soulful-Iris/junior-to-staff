def merge_windows(windows):
    cleaned = []
    for window in windows:
        if not isinstance(window, (tuple, list)) or len(window) != 2:
            raise ValueError("windows must be (start, end) pairs")
        start, end = window
        for bound in (start, end):
            if isinstance(bound, bool) or not isinstance(bound, (int, float)):
                raise ValueError("bounds must be numbers")
        if start >= end:
            raise ValueError(f"window {window} must have start < end")
        cleaned.append((start, end))
    cleaned.sort()
    merged = []
    for start, end in cleaned:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    result = [(s, e) for s, e in merged]
    total = sum(e - s for s, e in result)
    return result, total
