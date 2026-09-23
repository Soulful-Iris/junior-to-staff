def valid_anagram(first, second):
    if not isinstance(first, str) or not isinstance(second, str):
        raise ValueError("arguments must be strings")
    if len(first) != len(second):
        return False
    remaining = {}
    for char in first:
        remaining[char] = remaining.get(char, 0) + 1
    for char in second:
        if remaining.get(char, 0) == 0:
            return False
        remaining[char] -= 1
    return True
