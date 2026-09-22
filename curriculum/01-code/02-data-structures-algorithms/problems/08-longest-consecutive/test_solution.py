import itertools
import unittest
from solution import longest_consecutive

class ConsecutiveTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(longest_consecutive([100, 4, 200, 1, 3, 2, 2]), 4)
        self.assertEqual(longest_consecutive([-1, 1, 0]), 3)
        self.assertEqual(longest_consecutive([]), 0)
        self.assertEqual(longest_consecutive([1] * 200 + list(range(1, 200))), 199)
        with self.assertRaises(ValueError):
            longest_consecutive(["1"])

    def test_sorted_oracle(self):
        for n in range(6):
            for nums in itertools.product(range(-2, 3), repeat=n):
                ordered = sorted(set(nums))
                best = run = 0
                previous = None
                for value in ordered:
                    run = run + 1 if previous is not None and value == previous + 1 else 1
                    best = max(best, run)
                    previous = value
                self.assertEqual(longest_consecutive(nums), best)

if __name__ == "__main__":
    unittest.main()
