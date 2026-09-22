import random
import unittest
from solution import DisjointSet


class Tests(unittest.TestCase):
    def test_join_duplicate_and_identity(self):
        ds = DisjointSet(4)
        self.assertTrue(ds.union(0, 1))
        self.assertFalse(ds.union(1, 0))
        self.assertTrue(ds.connected(0, 1))
        self.assertTrue(ds.connected(2, 2))
        self.assertFalse(ds.connected(0, 2))
        self.assertEqual(ds.components, 3)

    def test_against_explicit_component_sets(self):
        rng = random.Random(7)
        ds = DisjointSet(12)
        labels = list(range(12))
        for _ in range(80):
            a, b = rng.randrange(12), rng.randrange(12)
            old, new = labels[b], labels[a]
            self.assertEqual(ds.union(a, b), old != new)
            labels = [new if x == old else x for x in labels]
            for x in range(12):
                for y in range(12):
                    self.assertEqual(ds.connected(x, y), labels[x] == labels[y])
            self.assertEqual(ds.components, len(set(labels)))

    def test_compression_and_bounds(self):
        ds = DisjointSet(4)
        ds.union(0, 1)
        ds.union(2, 3)
        ds.union(0, 2)
        root = ds.find(3)
        self.assertEqual(ds.parent[3], root)
        for node in [-1, 4]:
            with self.assertRaises(IndexError):
                ds.find(node)
        self.assertEqual(DisjointSet(0).components, 0)
        with self.assertRaises(ValueError):
            DisjointSet(-1)


if __name__ == "__main__":
    unittest.main()
