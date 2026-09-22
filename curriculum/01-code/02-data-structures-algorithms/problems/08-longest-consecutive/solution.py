def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def longest_consecutive(nums):
    _integers(nums)
    values = set(nums)
    best = 0
    for start in values:
        if start - 1 in values:
            continue
        end = start
        while end in values:
            end += 1
        best = max(best, end - start)
    return best
