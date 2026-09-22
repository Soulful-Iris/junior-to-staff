import random
import unittest
from solution import merge_intervals

class MergeTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(merge_intervals([(5, 7), (1, 3), (3, 6)]), [(1, 7)])
        self.assertEqual(merge_intervals([(1, 10), (2, 3), (1, 10)]), [(1, 10)])
        self.assertEqual(merge_intervals([]), [])
        self.assertEqual(merge_intervals([[5, 7], (1, 3), [3, 6]]), [(1, 7)])
        pairs = [[1, 2], [3, 4]]
        result = merge_intervals(pairs)
        self.assertEqual(result, [(1, 2), (3, 4)])
        self.assertEqual(pairs, [[1, 2], [3, 4]])
        for value in [[(2, 2)], [(3, 1)], [(1, True)], [(1,)], None]:
            with self.assertRaises(ValueError):
                merge_intervals(value)

    def test_discrete_coverage_oracle(self):
        rng = random.Random(109)
        for _ in range(400):
            pairs = []
            for _ in range(rng.randrange(15)):
                start = rng.randrange(-8, 8)
                pairs.append((start, start + rng.randrange(1, 6)))
            result = merge_intervals(pairs)
            expected = {x for start, end in pairs for x in range(start, end)}
            actual = {x for start, end in result for x in range(start, end)}
            self.assertEqual(actual, expected)
            self.assertTrue(all(result[i][1] < result[i+1][0] for i in range(len(result)-1)))
            self.assertEqual(merge_intervals(result), result)

if __name__ == "__main__":
    unittest.main()
