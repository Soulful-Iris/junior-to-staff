from fractions import Fraction
import random
import unittest
from solution import StreamingMedian


class Tests(unittest.TestCase):
    def test_every_prefix_and_invariants(self):
        rng = random.Random(41)
        stream, values = StreamingMedian(), []
        for _ in range(300):
            value = rng.randrange(-20, 21)
            stream.add(value)
            values.append(value)
            ordered = sorted(values)
            n = len(ordered)
            expected = Fraction(ordered[n // 2]) if n % 2 else Fraction(ordered[n//2-1] + ordered[n//2], 2)
            self.assertEqual(stream.median(), expected)
            self.assertIn(len(stream.low) - len(stream.high), (0, 1))
            if stream.high:
                self.assertLessEqual(max(-x for x in stream.low), min(stream.high))

    def test_huge_integers_without_float_overflow(self):
        stream = StreamingMedian()
        stream.add(10 ** 400)
        stream.add(10 ** 400 + 1)
        self.assertEqual(stream.median(), Fraction(2 * 10 ** 400 + 1, 2))

    def test_empty_and_invalid(self):
        stream = StreamingMedian()
        with self.assertRaises(ValueError):
            stream.median()
        with self.assertRaises(ValueError):
            stream.add(float('nan'))
        self.assertEqual(stream.low, [])


if __name__ == '__main__':
    unittest.main()
