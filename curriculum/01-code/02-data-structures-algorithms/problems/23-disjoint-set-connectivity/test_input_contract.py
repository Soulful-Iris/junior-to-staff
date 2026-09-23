import unittest
from solution import DisjointSet


class InputContractTests(unittest.TestCase):
    def test_invalid_size(self):
        for value in (True, None, [], -1, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                DisjointSet(value)
        self.assertEqual(DisjointSet(0).components, 0)

    def test_invalid_union_is_atomic(self):
        ds = DisjointSet(3)
        ds.union(0, 1)
        before = (ds.parent[:], ds.size[:], ds.components)
        for value in (True, None, [], -1, 3):
            with self.subTest(value=value), self.assertRaises(IndexError):
                ds.union(0, value)
            self.assertEqual((ds.parent, ds.size, ds.components), before)
        self.assertTrue(ds.connected(0, 1))
