import itertools
import random
import unittest
from solution import merge_streams


class Tests(unittest.TestCase):
    def test_examples_empty_duplicates(self):
        self.assertEqual(list(merge_streams([[1, 4], [], [1, 3, 8]])), [1, 1, 3, 4, 8])
        self.assertEqual(list(merge_streams([])), [])

    def test_seeded_oracle(self):
        rng = random.Random(27)
        for _ in range(30):
            streams = [sorted(rng.randrange(-10, 11) for _ in range(rng.randrange(10)))
                       for _ in range(rng.randrange(8))]
            self.assertEqual(list(merge_streams(streams)), sorted(itertools.chain.from_iterable(streams)))

    def test_lazy_consumption(self):
        calls = [0, 0]
        def stream(index, values):
            for value in values:
                calls[index] += 1
                yield value
        result = merge_streams([stream(0, [1, 4, 7]), stream(1, [2, 3, 8])])
        self.assertEqual(calls, [0, 0])
        self.assertEqual(next(result), 1)
        self.assertEqual(calls, [1, 1])
        self.assertEqual(next(result), 2)
        self.assertEqual(calls, [2, 1])

    def test_late_invalid_order(self):
        result = merge_streams([[1, 0]])
        self.assertEqual(next(result), 1)
        with self.assertRaises(ValueError):
            next(result)
        with self.assertRaises(ValueError):
            list(merge_streams([[None]]))


if __name__ == "__main__":
    unittest.main()
