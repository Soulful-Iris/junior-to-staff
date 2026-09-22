"""Enumerate unique nondecreasing combinations, with unlimited positive values."""


def combinations(candidates, target):
    if not isinstance(target, int) or target < 0:
        raise ValueError("nonnegative integer target required")
    unique = set()
    for value in candidates:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("positive integer candidates required")
        unique.add(value)
    values = sorted(unique)
    result, path = [], []
    # Each frame holds the next candidate index and remaining target.
    stack = [[0, target]]
    while stack:
        index, remaining = stack[-1]
        if remaining == 0:
            result.append(path.copy())
            stack.pop()
            if stack:
                path.pop()
        elif index == len(values) or values[index] > remaining:
            stack.pop()
            if stack:
                path.pop()
        else:
            stack[-1][0] += 1
            path.append(values[index])
            stack.append([index, remaining - values[index]])
    return result
