def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def two_sum(nums, target):
    _integers(nums)
    if type(target) is not int:
        raise ValueError("target must be an integer")
    pending_matches = {}
    for j, value in enumerate(nums):
        if value in pending_matches:
            return pending_matches[value], j
        pending_matches.setdefault(target - value, j)
    return None
