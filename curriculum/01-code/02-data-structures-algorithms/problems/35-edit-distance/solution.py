"""Unit-cost Levenshtein distance with one rolling row."""


def edit_distance(source, target):
    if not isinstance(source, str) or not isinstance(target, str):
        raise ValueError("string inputs required")
    if len(source) < len(target):
        source, target = target, source
    previous = list(range(len(target) + 1))
    for i, a in enumerate(source, 1):
        current = [i]
        for j, b in enumerate(target, 1):
            current.append(min(previous[j] + 1,
                               current[j - 1] + 1,
                               previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]
