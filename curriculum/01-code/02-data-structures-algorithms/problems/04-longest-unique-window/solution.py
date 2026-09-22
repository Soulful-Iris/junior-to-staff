def longest_unique_window(text):
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    left = 0
    last = {}
    best = (0, 0)
    for right, char in enumerate(text):
        left = max(left, last.get(char, -1) + 1)
        last[char] = right
        if right + 1 - left > best[1] - best[0]:
            best = left, right + 1
    return best
