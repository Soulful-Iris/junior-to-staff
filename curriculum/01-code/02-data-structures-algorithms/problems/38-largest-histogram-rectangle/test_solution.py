import itertools
import unittest
from solution import largest_rectangle


class Tests(unittest.TestCase):
    def test_examples_plateau_and_flush(self):
        self.assertEqual(largest_rectangle([2, 1, 5, 6, 2, 3]), 10)
        self.assertEqual(largest_rectangle([2, 2, 2]), 6)
        self.assertEqual(largest_rectangle([1, 2, 3, 4]), 6)
        self.assertEqual(largest_rectangle([4, 3, 2, 1]), 6)
        self.assertEqual(largest_rectangle([2, 0, 2]), 2)
        self.assertEqual(largest_rectangle([]), 0)

    def test_exhaustive_interval_oracle(self):
        for length in range(7):
            for heights in itertools.product(range(3), repeat=length):
                expected = max((min(heights[a:b]) * (b-a)
                                for a in range(length) for b in range(a+1, length+1)), default=0)
                self.assertEqual(largest_rectangle(heights), expected)

    def test_validation_and_no_mutation(self):
        heights = [1, 2]
        largest_rectangle(heights)
        self.assertEqual(heights, [1, 2])
        for heights in [[-1], [1.5]]:
            with self.assertRaises(ValueError):
                largest_rectangle(heights)


if __name__ == '__main__':
    unittest.main()
