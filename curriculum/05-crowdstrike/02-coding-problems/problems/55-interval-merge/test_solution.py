import random
import unittest
from solution import merge_windows


def oracle(windows):
    covered = set()
    for s, e in windows:
        covered.update(range(s, e))
    merged, start = [], None
    for t in range(0, 40):
        if t in covered and start is None:
            start = t
        if t not in covered and start is not None:
            merged.append((start, t))
            start = None
    if start is not None:
        merged.append((start, 40))
    return merged, len(covered)


class IntervalTests(unittest.TestCase):
    def test_scenarios(self):
        self.assertEqual(merge_windows([(0, 5), (3, 8), (10, 12)]), ([(0, 8), (10, 12)], 10))
        self.assertEqual(merge_windows([(0, 5), (5, 8)]), ([(0, 8)], 8))
        self.assertEqual(merge_windows([(0, 10), (2, 3)]), ([(0, 10)], 10))
        self.assertEqual(merge_windows([(10, 12), (0, 5)]), ([(0, 5), (10, 12)], 7))
        self.assertEqual(merge_windows([]), ([], 0))
        self.assertEqual(merge_windows([(1, 2), (1, 2)]), ([(1, 2)], 1))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            merge_windows([(5, 5)])
        with self.assertRaises(ValueError):
            merge_windows([("a", 1)])

    def test_matches_coverage_oracle(self):
        rng = random.Random(13)
        for _ in range(300):
            windows = []
            for _ in range(rng.randint(0, 8)):
                s = rng.randint(0, 30)
                windows.append((s, s + rng.randint(1, 8)))
            self.assertEqual(merge_windows(windows), oracle(windows), windows)


if __name__ == "__main__":
    unittest.main()
