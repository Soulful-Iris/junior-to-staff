def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def subarray_sum_count(nums, target):
    _integers(nums)
    if type(target) is not int:
        raise ValueError("target must be an integer")
    counts = {0: 1}
    prefix = total = 0
    for value in nums:
        prefix += value
        total += counts.get(prefix - target, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
    return total
