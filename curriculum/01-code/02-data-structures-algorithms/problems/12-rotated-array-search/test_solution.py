import itertools
import unittest
from solution import rotated_search

class RotationTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(rotated_search([4, 5, 7, 0, 1, 2], 1), 4)
        self.assertEqual(rotated_search([], 6), -1)
        self.assertEqual(rotated_search([1], 1), 0)
        for nums in [[2, 1, 3], [1, 1], [2, 1, 2], [True], [1, 3, 2, 4]]:
            with self.assertRaises(ValueError):
                rotated_search(nums, 1)

    def test_every_rotation_against_linear_lookup(self):
        for n in range(7):
            for ordered in itertools.combinations(range(-3, 4), n):
                for pivot in range(max(1, n)):
                    nums = ordered[pivot:] + ordered[:pivot]
                    for target in range(-4, 5):
                        expected = nums.index(target) if target in nums else -1
                        self.assertEqual(rotated_search(nums, target), expected)

if __name__ == "__main__":
    unittest.main()
