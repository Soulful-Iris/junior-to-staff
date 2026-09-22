import itertools
import math
import unittest
from solution import product_except_self

class ProductTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(product_except_self([]), [])
        self.assertEqual(product_except_self([7]), [1])
        self.assertEqual(product_except_self([0, 3, 4]), [12, 0, 0])
        self.assertEqual(product_except_self([0, 0, 4]), [0, 0, 0])
        nums = [2, 3, 4]
        self.assertEqual(product_except_self(nums), [12, 8, 6])
        self.assertEqual(nums, [2, 3, 4])
        with self.assertRaises(ValueError):
            product_except_self([False])

    def test_independent_exclusion_oracle(self):
        for n in range(6):
            for nums in itertools.product(range(-2, 3), repeat=n):
                expected = [math.prod(nums[:i] + nums[i+1:]) for i in range(n)]
                self.assertEqual(product_except_self(nums), expected)

if __name__ == "__main__":
    unittest.main()
