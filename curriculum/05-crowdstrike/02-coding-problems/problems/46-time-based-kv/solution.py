import bisect


def _check_ts(ts):
    if not isinstance(ts, int) or isinstance(ts, bool):
        raise ValueError("timestamps must be ints")


class TimeMap:
    def __init__(self):
        self._times = {}
        self._values = {}

    def set(self, key, value, ts):
        _check_ts(ts)
        times = self._times.setdefault(key, [])
        values = self._values.setdefault(key, [])
        if times and ts < times[-1]:
            raise ValueError("timestamps must be non-decreasing per key")
        if times and ts == times[-1]:
            values[-1] = value
        else:
            times.append(ts)
            values.append(value)

    def get(self, key, ts):
        _check_ts(ts)
        times = self._times.get(key)
        if not times:
            return None
        i = bisect.bisect_right(times, ts) - 1
        if i < 0:
            return None
        return self._values[key][i]
