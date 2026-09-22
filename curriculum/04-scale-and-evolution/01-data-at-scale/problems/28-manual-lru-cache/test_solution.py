import random
import unittest
from solution import LRUCache


class Tests(unittest.TestCase):
    def assert_links(self, cache):
        seen = []
        previous, node = cache.head, cache.head.next
        while node is not cache.tail:
            self.assertIs(node.prev, previous)
            self.assertIs(cache.nodes[node.key], node)
            self.assertNotIn(node.key, seen)
            seen.append(node.key)
            self.assertLessEqual(len(seen), cache.capacity)
            previous, node = node, node.next
        self.assertIs(cache.tail.prev, previous)
        self.assertEqual(set(seen), set(cache.nodes))
        self.assertIsNone(cache.head.prev)
        self.assertIsNone(cache.tail.next)

    def test_unlink_middle_and_evict(self):
        c = LRUCache(3)
        for key in 'abc':
            c.put(key, key.upper())
        self.assertEqual(c.get('b'), 'B')
        self.assertEqual(c.items_lru(), [('a', 'A'), ('c', 'C'), ('b', 'B')])
        self.assertEqual(c.put('d', 'D'), ('a', 'A'))
        with self.assertRaises(KeyError):
            c.get('a')
        c.put('c', None)
        self.assertIsNone(c.get('c'))
        self.assert_links(c)

    def test_model_after_every_operation(self):
        rng = random.Random(28)
        for capacity in [0, 1, 4]:
            c, model = LRUCache(capacity), []
            for _ in range(200):
                key = rng.randrange(7)
                if rng.random() < .65:
                    value = rng.randrange(20)
                    existing = next((item for item in model if item[0] == key), None)
                    if existing:
                        model.remove(existing)
                    model.append((key, value))
                    evicted = model.pop(0) if len(model) > capacity else None
                    self.assertEqual(c.put(key, value), evicted)
                else:
                    existing = next((item for item in model if item[0] == key), None)
                    if existing is None:
                        with self.assertRaises(KeyError):
                            c.get(key)
                    else:
                        self.assertEqual(c.get(key), existing[1])
                        model.remove(existing)
                        model.append(existing)
                self.assertEqual(c.items_lru(), model)
                self.assert_links(c)

    def test_bad_capacity(self):
        with self.assertRaises(ValueError):
            LRUCache(-1)


if __name__ == '__main__':
    unittest.main()
