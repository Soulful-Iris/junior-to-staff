from collections import Counter


def _minute_key(ts):
    """Return 'YYYY-MM-DDTHH:MM' if ts starts with that shape, else None."""
    if len(ts) < 16:
        return None
    shape = "dddd-dd-ddTdd:dd"
    for ch, want in zip(ts[:16], shape):
        if want == "d":
            if not ch.isdigit():
                return None
        elif ch != want:
            return None
    return ts[:16]


def count_errors(lines):
    counts = Counter()
    malformed = 0
    for line in lines:
        if not isinstance(line, str):
            raise ValueError("lines must be strings")
        parts = line.rstrip("\r\n").split(" ", 3)
        if len(parts) < 3:
            malformed += 1
            continue
        minute = _minute_key(parts[0])
        if minute is None:
            malformed += 1
            continue
        if parts[1] == "ERROR":
            counts[(parts[2], minute)] += 1
    return dict(counts), malformed
