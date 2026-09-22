def minimum_covering_window(text, required):
    if not isinstance(text, str) or not isinstance(required, str):
        raise ValueError("arguments must be strings")
    if not required:
        return 0, 0
    need = {}
    for char in required:
        need[char] = need.get(char, 0) + 1
    missing = len(required)
    left = 0
    best = None
    for right, char in enumerate(text):
        if char in need:
            if need[char] > 0:
                missing -= 1
            need[char] -= 1
        while missing == 0:
            if best is None or right + 1 - left < best[1] - best[0]:
                best = left, right + 1
            departing = text[left]
            if departing in need:
                need[departing] += 1
                if need[departing] > 0:
                    missing += 1
            left += 1
    return best
