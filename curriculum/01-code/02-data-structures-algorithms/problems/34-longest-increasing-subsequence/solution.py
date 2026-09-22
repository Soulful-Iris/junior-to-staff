"""Strict LIS with tails indices and predecessor reconstruction."""
from bisect import bisect_left


def longest_increasing_subsequence(values):
    values = list(values)
    if any(not isinstance(x, int) for x in values):
        raise ValueError("integer sequence required")
    tails, indices = [], []
    previous = [-1] * len(values)
    for index, value in enumerate(values):
        position = bisect_left(tails, value)
        if position:
            previous[index] = indices[position - 1]
        if position == len(tails):
            tails.append(value)
            indices.append(index)
        else:
            tails[position] = value
            indices[position] = index
    if not indices:
        return []
    result, index = [], indices[-1]
    while index != -1:
        result.append(values[index])
        index = previous[index]
    return result[::-1]
