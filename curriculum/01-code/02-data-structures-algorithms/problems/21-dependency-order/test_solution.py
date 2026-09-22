import unittest
from solution import dependency_order


class Tests(unittest.TestCase):
    def test_order_and_isolated(self):
        tasks = ["fetch", "parse", "save", "metrics"]
        edges = [("fetch", "parse"), ("parse", "save")]
        order = dependency_order(tasks, edges)
        self.assertEqual(set(order), set(tasks))
        for a, b in edges:
            self.assertLess(order.index(a), order.index(b))
        self.assertEqual(order, ["fetch", "metrics", "parse", "save"])

    def test_duplicate_edge_and_empty(self):
        self.assertEqual(dependency_order([], []), [])
        self.assertEqual(dependency_order([1, 2], [(1, 2), (1, 2)]), [1, 2])

    def test_invalid_and_cycles(self):
        for tasks, edges in [([1], [(1, 1)]), ([1, 2, 3], [(1, 2), (2, 1)]),
                             ([1], [(1, 2)]), ([1, 1], [])]:
            with self.subTest(tasks=tasks, edges=edges), self.assertRaises(ValueError):
                dependency_order(tasks, edges)

    def test_long_chain(self):
        self.assertEqual(dependency_order(range(2000), zip(range(1999), range(1, 2000))),
                         list(range(2000)))


if __name__ == "__main__":
    unittest.main()
