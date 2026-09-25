import unittest
from collections import OrderedDict
from solution import LRUCache


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class LRUTests(unittest.TestCase):
    def test_recency(self):
        c = LRUCache(2)
        c.put("a", 1); c.put("b", 2)
        self.assertEqual(c.get("a"), 1)
        c.put("c", 3)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("c"), 3)

    def test_update_refreshes(self):
        c = LRUCache(2)
        c.put("a", 1); c.put("b", 2); c.put("a", 2); c.put("c", 3)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 2)

    def test_capacity_one_and_miss(self):
        c = LRUCache(1)
        self.assertIsNone(c.get("z"))
        c.put("a", 1); c.put("b", 2)
        self.assertIsNone(c.get("a"))

    def test_ttl(self):
        clock = FakeClock()
        c = LRUCache(1, clock=clock)
        c.put("a", 1, ttl=5)
        clock.t = 4.9
        self.assertEqual(c.get("a"), 1)
        clock.t = 5
        self.assertIsNone(c.get("a"))
        c.put("a", 1, ttl=1)
        clock.t = 7
        c.put("b", 2)
        self.assertEqual(c.size(), 1)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            LRUCache(0)
        with self.assertRaises(ValueError):
            LRUCache(1).put("a", 1, ttl=0)

    def test_matches_ordered_dict_oracle(self):
        import random
        rng = random.Random(2)
        c = LRUCache(3)
        oracle = OrderedDict()
        for _ in range(500):
            key = rng.choice("abcde")
            if rng.random() < 0.5:
                c.put(key, key)
                if key in oracle:
                    oracle.move_to_end(key)
                oracle[key] = key
                if len(oracle) > 3:
                    oracle.popitem(last=False)
            else:
                expected = oracle.get(key)
                if expected is not None:
                    oracle.move_to_end(key)
                self.assertEqual(c.get(key), expected)


if __name__ == "__main__":
    unittest.main()
