"""Explicit forest with union by size and iterative path compression."""


class DisjointSet:
    def __init__(self, n):
        if not isinstance(n, int) or n < 0:
            raise ValueError("nonnegative integer size required")
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def _check(self, node):
        if not isinstance(node, int) or not 0 <= node < len(self.parent):
            raise IndexError("unknown node")

    def find(self, node):
        self._check(node)
        root = node
        while root != self.parent[root]:
            root = self.parent[root]
        while node != root:
            next_node = self.parent[node]
            self.parent[node] = root
            node = next_node
        return root

    def union(self, a, b):
        self._check(a)
        self._check(b)
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        self.components -= 1
        return True

    def connected(self, a, b):
        self._check(a)
        self._check(b)
        return self.find(a) == self.find(b)
