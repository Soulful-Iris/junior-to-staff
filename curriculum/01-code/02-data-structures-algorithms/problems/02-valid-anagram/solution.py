def valid_anagram(first, second):
    if not isinstance(first, str) or not isinstance(second, str):
        raise ValueError("arguments must be strings")
    if len(first) != len(second):
        return False
    counts = {}
    for char in first:
        counts[char] = counts.get(char, 0) + 1
    for char in second:
        if counts.get(char, 0) == 0:
            return False
        counts[char] -= 1
    return True
