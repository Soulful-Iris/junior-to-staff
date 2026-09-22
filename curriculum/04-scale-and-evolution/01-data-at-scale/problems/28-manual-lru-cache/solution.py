"""LRU implemented with a dict and explicit doubly linked sentinel list."""


class Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = self.next = None


class LRUCache:
    def __init__(self, capacity):
        if not isinstance(capacity, int) or capacity < 0:
            raise ValueError("capacity must be a nonnegative integer")
        self.capacity = capacity
        self.nodes = {}
        self.head, self.tail = Node(), Node()
        self.head.next, self.tail.prev = self.tail, self.head

    @staticmethod
    def _unlink(node):
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None

    def _append_recent(self, node):
        previous = self.tail.prev
        previous.next = node
        node.prev, node.next = previous, self.tail
        self.tail.prev = node

    def get(self, key):
        node = self.nodes[key]
        self._unlink(node)
        self._append_recent(node)
        return node.value

    def put(self, key, value):
        """Return an evicted (key, value), or None; overwrite refreshes recency."""
        if key in self.nodes:
            node = self.nodes[key]
            node.value = value
            self._unlink(node)
            self._append_recent(node)
            return None
        if self.capacity == 0:
            return key, value
        node = Node(key, value)
        self.nodes[key] = node
        self._append_recent(node)
        if len(self.nodes) > self.capacity:
            victim = self.head.next
            self._unlink(victim)
            del self.nodes[victim.key]
            return victim.key, victim.value
        return None

    def items_lru(self):
        result = []
        node = self.head.next
        while node is not self.tail:
            result.append((node.key, node.value))
            node = node.next
        return result
