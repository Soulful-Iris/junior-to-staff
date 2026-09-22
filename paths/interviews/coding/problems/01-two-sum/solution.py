def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def two_sum(nums, target):
    _integers(nums)
    if type(target) is not int:
        raise ValueError("target must be an integer")
    earliest = {}
    for j, value in enumerate(nums):
        needed = target - value
        if needed in earliest:
            return earliest[needed], j
        earliest.setdefault(value, j)
    return None
