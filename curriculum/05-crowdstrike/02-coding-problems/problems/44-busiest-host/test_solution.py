import random
import unittest
from collections import Counter
from solution import busiest, top_k, TopKWindow


class BusiestTests(unittest.TestCase):
    def test_examples(self):
        self.assertEqual(busiest([("a", 1), ("b", 2), ("a", 3)]), "a")
        self.assertEqual(busiest([("b", 1), ("a", 2)]), "a")
        self.assertIsNone(busiest([]))
        self.assertEqual(top_k([("a", 1), ("b", 2), ("a", 3)], 2), ["a", "b"])
        self.assertEqual(top_k([("a", 1), ("b", 2)], 5), ["a", "b"])
        self.assertEqual(top_k([("a", 1)], 0), [])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            top_k([], -1)
        with self.assertRaises(ValueError):
            busiest(["a"])

    def test_top_k_matches_sort_oracle(self):
        rng = random.Random(7)
        for _ in range(200):
            records = [(rng.choice("abcdefg"), i) for i in range(rng.randint(0, 40))]
            counts = Counter(h for h, _ in records)
            expected = [h for h, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
            k = rng.randint(0, 8)
            self.assertEqual(top_k(records, k), expected[:k])

    def test_window_evicts(self):
        w = TopKWindow(2, 10)
        for ts in (0, 0, 0):
            w.add("a", ts)
        self.assertEqual(w.current(), ["a"])
        w.add("b", 11)
        self.assertEqual(w.current(), ["b"])
        w.add("c", 12)
        self.assertEqual(w.current(), ["b", "c"])

    def test_window_matches_recount_oracle(self):
        rng = random.Random(3)
        w = TopKWindow(3, 5)
        history = []
        for ts in range(60):
            host = rng.choice("xyz")
            w.add(host, ts)
            history.append((host, ts))
            live = Counter(h for h, t in history if t > ts - 5)
            expected = [h for h, _ in sorted(live.items(), key=lambda kv: (-kv[1], kv[0]))][:3]
            self.assertEqual(w.current(), expected)

    def test_window_invalid(self):
        with self.assertRaises(ValueError):
            TopKWindow(1, 0)


if __name__ == "__main__":
    unittest.main()
