def _integers(values):
    if not isinstance(values, (list, tuple)) or any(type(x) is not int for x in values):
        raise ValueError("expected a list or tuple of integers, excluding bool")

def shipping_capacity(weights, days):
    _integers(weights)
    if type(days) is not int or days <= 0 or any(weight <= 0 for weight in weights):
        raise ValueError("days and weights must be positive integers")
    if not weights:
        return 0
    lo, hi = max(weights), sum(weights)
    while lo < hi:
        capacity = lo + (hi - lo) // 2
        used, load = 1, 0
        for weight in weights:
            if load + weight > capacity:
                used += 1
                load = 0
            load += weight
        if used <= days:
            hi = capacity
        else:
            lo = capacity + 1
    return lo
