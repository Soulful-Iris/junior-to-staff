import itertools
import unittest
from solution import lower_bound

class BoundaryTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(lower_bound([1, 3, 3, 8], 3), 1)
        self.assertEqual(lower_bound([1, 3, 3, 8], 4), 3)
        self.assertEqual(lower_bound([1, 3, 3, 8], 9), 4)
        self.assertEqual(lower_bound([], 2), 0)
        for nums, target in [([3, 1], 2), ([True], 1), (None, 2), ([1], 1.0)]:
            with self.assertRaises(ValueError):
                lower_bound(nums, target)

    def test_linear_boundary_oracle(self):
        for n in range(8):
            for nums in itertools.combinations_with_replacement(range(-2, 3), n):
                for target in range(-3, 4):
                    result = lower_bound(nums, target)
                    expected = next((i for i, value in enumerate(nums) if value >= target), n)
                    self.assertEqual(result, expected)
                    self.assertTrue(all(value < target for value in nums[:result]))
                    self.assertTrue(all(value >= target for value in nums[result:]))

if __name__ == "__main__":
    unittest.main()
