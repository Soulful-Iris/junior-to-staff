def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def lower_bound(nums, target):
    _integers(nums)
    if type(target) is not int or any(nums[i] > nums[i + 1] for i in range(len(nums) - 1)):
        raise ValueError("expected sorted integers and integer target")
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo
