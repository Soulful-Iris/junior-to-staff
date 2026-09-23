"""Lexicographic prefix lookup using explicit trie nodes and iterative DFS."""
from string import ascii_lowercase


class Node:
    def __init__(self):
        self.children = {}
        self.terminal = False


class Trie:
    def __init__(self, words=()):
        if isinstance(words, (str, bytes)):
            raise ValueError("expected an iterable of words, not one string")
        try:
            words = iter(words)
        except TypeError as exc:
            raise ValueError("expected an iterable of words") from exc
        self.root = Node()
        for word in words:
            self.add(word)

    @staticmethod
    def _validate(text, allow_empty=False):
        if not isinstance(text, str) or (not text and not allow_empty) or any(c not in ascii_lowercase for c in text):
            raise ValueError("lowercase ASCII words required")

    def add(self, word):
        self._validate(word)
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = Node()
            node = node.children[char]
        node.terminal = True

    def suggest(self, prefix, limit=5):
        self._validate(prefix, allow_empty=True)
        if type(limit) is not int or limit < 0:
            raise ValueError("nonnegative integer limit required")
        if limit == 0:
            return []
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        result = [prefix] if node.terminal else []
        path = list(prefix)
        stack = [iter(sorted(node.children.items()))]
        while stack and len(result) < limit:
            try:
                char, child = next(stack[-1])
            except StopIteration:
                stack.pop()
                if stack:
                    path.pop()
                continue
            path.append(char)
            if child.terminal:
                result.append(''.join(path))
            stack.append(iter(sorted(child.children.items())))
        return result[:limit]
