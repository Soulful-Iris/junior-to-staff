"""Largest rectangle under unit-width, nonnegative integer histogram bars."""
from itertools import chain


def largest_rectangle(heights):
    heights = list(heights)
    if any(not isinstance(height, int) or height < 0 for height in heights):
        raise ValueError("nonnegative integer heights required")
    best, stack = 0, []
    for index, height in enumerate(chain(heights, [0])):
        start = index
        while stack and stack[-1][1] > height:
            start, previous_height = stack.pop()
            best = max(best, previous_height * (index - start))
        if height and (not stack or stack[-1][1] < height):
            stack.append((start, height))
    return best
