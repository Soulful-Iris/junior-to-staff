def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def rotated_search(nums, target):
    _integers(nums)
    if type(target) is not int:
        raise ValueError("target must be an integer")
    n = len(nums)
    if n > 1:
        descents = 0
        for i in range(n):
            current, following = nums[i], nums[(i + 1) % n]
            if current == following:
                raise ValueError("values must be distinct")
            descents += current > following
        if descents != 1:
            raise ValueError("input must be a strict sorted rotation")
    lo, hi = 0, n - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        elif nums[mid] < target <= nums[hi]:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
