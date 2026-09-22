"""Shortest one-character transformation using an implicit unweighted graph."""
from collections import deque
from string import ascii_lowercase


def word_ladder(start, end, words):
    """Return endpoint-inclusive shortest path, or []; words are lowercase ASCII."""
    words = set(words)
    if not start or len(start) != len(end):
        raise ValueError("endpoints must have equal positive length")
    if any(len(w) != len(start) or any(c not in ascii_lowercase for c in w)
           for w in words | {start, end}):
        raise ValueError("words must have equal length and lowercase ASCII letters")
    if start == end:
        return [start]
    if end not in words:
        return []
    parent = {start: None}
    queue = deque([start])
    while queue:
        word = queue.popleft()
        for i in range(len(word)):
            for char in ascii_lowercase:
                if char == word[i]:
                    continue
                candidate = word[:i] + char + word[i + 1:]
                if candidate in words and candidate not in parent:
                    parent[candidate] = word
                    if candidate == end:
                        path = [end]
                        while parent[path[-1]] is not None:
                            path.append(parent[path[-1]])
                        return path[::-1]
                    queue.append(candidate)
    return []
