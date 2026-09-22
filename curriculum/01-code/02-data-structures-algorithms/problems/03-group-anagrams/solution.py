def group_anagrams(words):
    if not isinstance(words, (list, tuple)) or any(not isinstance(word, str) for word in words):
        raise ValueError("expected a list or tuple of strings")
    groups = {}
    for word in words:
        key = "".join(sorted(word))
        groups.setdefault(key, []).append(word)
    return list(groups.values())
