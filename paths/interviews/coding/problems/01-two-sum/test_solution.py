import itertools
import unittest
from solution import two_sum

class TwoSumTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(two_sum([3, 3, 2], 6), (0, 1))
        self.assertEqual(two_sum([1, 1, 3], 4), (0, 2))
        self.assertIsNone(two_sum([3], 6))
        nums = [-3, 8, 4]
        self.assertEqual(two_sum(nums, 5), (0, 1))
        self.assertEqual(nums, [-3, 8, 4])
        for nums, target in [(None, 2), ([True], 2), ([1], 2.0)]:
            with self.assertRaises(ValueError):
                two_sum(nums, target)

    def test_exhaustive_pair_oracle(self):
        for n in range(6):
            for values in itertools.product(range(-1, 2), repeat=n):
                for target in range(-2, 3):
                    expected = next(((i, j) for j in range(n) for i in range(j)
                                     if values[i] + values[j] == target), None)
                    self.assertEqual(two_sum(values, target), expected)

if __name__ == "__main__":
    unittest.main()
