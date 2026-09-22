def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def product_except_self(nums):
    _integers(nums)
    result = [1] * len(nums)
    prefix = 1
    for i, value in enumerate(nums):
        result[i] = prefix
        prefix *= value
    suffix = 1
    for i in range(len(nums) - 1, -1, -1):
        result[i] *= suffix
        suffix *= nums[i]
    return result
