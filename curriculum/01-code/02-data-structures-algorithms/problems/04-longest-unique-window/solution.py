def longest_unique_window(text):
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    left = 0
    last_seen = {}
    best = (0, 0)
    for right, char in enumerate(text):
        left = max(left, last_seen.get(char, -1) + 1)
        last_seen[char] = right
        if right + 1 - left > best[1] - best[0]:
            best = left, right + 1
    return best
