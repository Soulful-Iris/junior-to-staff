import itertools
import unittest
from solution import daily_temperatures


class Tests(unittest.TestCase):
    def test_example_and_equal(self):
        self.assertEqual(daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]), [1, 1, 4, 2, 1, 1, 0, 0])
        self.assertEqual(daily_temperatures([5, 5, 5]), [0, 0, 0])
        self.assertEqual(daily_temperatures([]), [])

    def test_exhaustive_against_scan(self):
        for size in range(7):
            for values in itertools.product([-1, 0, 1], repeat=size):
                expected = []
                for i, temperature in enumerate(values):
                    expected.append(next((j-i for j in range(i+1, size) if values[j] > temperature), 0))
                self.assertEqual(daily_temperatures(values), expected)

    def test_invalid_and_no_mutation(self):
        values = [3, 2, 1]
        self.assertEqual(daily_temperatures(values), [0, 0, 0])
        self.assertEqual(values, [3, 2, 1])
        with self.assertRaises(ValueError):
            daily_temperatures([1, None])


if __name__ == '__main__':
    unittest.main()
