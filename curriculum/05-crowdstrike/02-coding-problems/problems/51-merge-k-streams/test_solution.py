import heapq
import itertools
import random
import unittest
from solution import merge


class MergeTests(unittest.TestCase):
    def test_scenarios(self):
        self.assertEqual(list(merge([iter([(1, "a"), (3, "b")]), iter([(2, "c")])])), [(1, "a"), (2, "c"), (3, "b")])
        self.assertEqual(list(merge([iter([(1, "a")]), iter([(1, "b")])])), [(1, "a"), (1, "b")])
        self.assertEqual(list(merge([iter([(1, "a"), (1, "b")]), iter([])])), [(1, "a"), (1, "b")])
        self.assertEqual(list(merge([iter([]), iter([(5, "x")]), iter([])])), [(5, "x")])
        self.assertEqual(list(merge([])), [])

    def test_lazy(self):
        def exploding():
            yield (1, "a")
            yield (2, "b")
            raise RuntimeError("read too far")
        out = list(itertools.islice(merge([exploding(), iter([(10, "z")])]), 2))
        self.assertEqual(out, [(1, "a"), (2, "b")])

    def test_out_of_order_stream(self):
        with self.assertRaises(ValueError):
            list(merge([iter([(2, "a"), (1, "b")])]))

    def test_matches_heapq_merge_oracle(self):
        rng = random.Random(4)
        for _ in range(200):
            streams = [sorted((rng.randint(0, 9), f"{i}-{j}") for j in range(rng.randint(0, 6)))
                       for i in range(rng.randint(0, 4))]
            expected = list(heapq.merge(*[[(ts, i, p) for ts, p in s] for i, s in enumerate(streams)]))
            expected = [(ts, p) for ts, _, p in expected]
            self.assertEqual(list(merge([iter(s) for s in streams])), expected)


if __name__ == "__main__":
    unittest.main()
