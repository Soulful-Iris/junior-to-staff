import itertools
import random
import unittest
from solution import longest_increasing_subsequence


class Tests(unittest.TestCase):
    def test_example_duplicates_and_empty(self):
        self.assertEqual(longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18]), [2, 3, 7, 18])
        self.assertEqual(longest_increasing_subsequence([2, 2, 2]), [2])
        self.assertEqual(longest_increasing_subsequence([]), [])
        self.assertEqual(len(longest_increasing_subsequence([5, 4, 3, 2])), 1)

    def test_exhaustive_subset_oracle(self):
        rng = random.Random(34)
        for _ in range(60):
            values = [rng.randrange(-3, 5) for _ in range(8)]
            expected = 0
            for size in range(9):
                for indices in itertools.combinations(range(8), size):
                    seq = [values[i] for i in indices]
                    if all(a < b for a, b in zip(seq, seq[1:])):
                        expected = max(expected, size)
            answer = longest_increasing_subsequence(values)
            self.assertEqual(len(answer), expected)
            self.assertTrue(all(a < b for a, b in zip(answer, answer[1:])))
            iterator = iter(values)
            self.assertTrue(all(any(item == value for item in iterator) for value in answer))

    def test_tails_are_not_necessarily_a_subsequence(self):
        answer = longest_increasing_subsequence([3, 5, 6, 2, 4])
        self.assertEqual(answer, [3, 5, 6])
        with self.assertRaises(ValueError):
            longest_increasing_subsequence([1, None])


if __name__ == '__main__':
    unittest.main()
