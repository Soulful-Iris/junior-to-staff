import itertools
import unittest
from solution import combinations


class Tests(unittest.TestCase):
    def test_example_and_boundaries(self):
        self.assertEqual(combinations([2, 3, 6, 7, 2], 7), [[2, 2, 3], [7]])
        self.assertEqual(combinations([], 0), [[]])
        self.assertEqual(combinations([], 3), [])
        self.assertEqual(combinations([4, 6], 5), [])

    def test_against_count_vector_oracle(self):
        values = [2, 3, 5]
        for target in range(21):
            expected = []
            for counts in itertools.product(*(range(target // x + 1) for x in values)):
                if sum(x * count for x, count in zip(values, counts)) == target:
                    expected.append([x for x, count in zip(values, counts) for _ in range(count)])
            self.assertEqual(combinations(values, target), sorted(expected))

    def test_long_path_and_no_mutation(self):
        values = [3, 1]
        original = values.copy()
        combinations(values, 6)
        self.assertEqual(values, original)
        self.assertEqual(combinations([1], 1500), [[1] * 1500])

    def test_invalid(self):
        for values, target in [([0], 3), ([-1], 3), ([2], -1), ([1.5], 3)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                combinations(values, target)


if __name__ == '__main__':
    unittest.main()
