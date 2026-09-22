import itertools
import unittest
from solution import subarray_sum_count

class PrefixTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(subarray_sum_count([1, -1, 0], 0), 3)
        self.assertEqual(subarray_sum_count([], 0), 0)
        self.assertEqual(subarray_sum_count([0] * 100, 0), 5050)
        self.assertEqual(subarray_sum_count([10**100, -(10**100)], 0), 1)
        for nums, target in [([True], 1), ([1.5], 1), ([1], False), (None, 0)]:
            with self.assertRaises(ValueError):
                subarray_sum_count(nums, target)

    def test_range_sum_oracle(self):
        for n in range(6):
            for nums in itertools.product(range(-1, 2), repeat=n):
                for target in range(-2, 3):
                    expected = sum(sum(nums[i:j]) == target
                                   for i in range(n) for j in range(i + 1, n + 1))
                    self.assertEqual(subarray_sum_count(nums, target), expected)

if __name__ == "__main__":
    unittest.main()
