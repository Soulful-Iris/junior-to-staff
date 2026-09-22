import random
import unittest
from solution import TopK


class Tests(unittest.TestCase):
    def test_every_prefix_against_sort(self):
        rng = random.Random(26)
        values = [rng.randrange(-8, 9) for _ in range(100)]
        for k in [0, 1, 4, 110]:
            top = TopK(k)
            seen = []
            for value in values:
                seen.append(value)
                top.add(value)
                self.assertEqual(top.largest(), sorted(seen, reverse=True)[:k])
                self.assertLessEqual(len(top._heap), k)

    def test_duplicates_and_snapshot(self):
        top = TopK(2)
        for x in [5, 5, 4]:
            top.add(x)
        result = top.largest()
        result.clear()
        self.assertEqual(top.largest(), [5, 5])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            TopK(-1)
        with self.assertRaises(ValueError):
            TopK(2).add(float('nan'))


if __name__ == "__main__":
    unittest.main()
