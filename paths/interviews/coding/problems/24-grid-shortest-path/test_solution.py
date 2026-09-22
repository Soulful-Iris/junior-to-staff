import copy
import unittest
from solution import shortest_grid_path


class Tests(unittest.TestCase):
    def test_detour_and_no_mutation(self):
        grid = [[0, 1, 0], [0, 1, 0], [0, 0, 0]]
        original = copy.deepcopy(grid)
        self.assertEqual(shortest_grid_path(grid, (0, 0), (0, 2)),
                         [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)])
        self.assertEqual(grid, original)

    def test_boundaries(self):
        self.assertEqual(shortest_grid_path([[0]], (0, 0), (0, 0)), [(0, 0)])
        self.assertEqual(shortest_grid_path([[1]], (0, 0), (0, 0)), [])
        self.assertEqual(shortest_grid_path([[0, 1, 0]], (0, 0), (0, 2)), [])

    def test_open_grid_distance(self):
        path = shortest_grid_path([[0] * 8 for _ in range(6)], (0, 0), (5, 7))
        self.assertEqual(len(path) - 1, 12)
        for a, b in zip(path, path[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_invalid(self):
        for grid, start in [([], (0, 0)), ([[0], [0, 0]], (0, 0)),
                            ([[2]], (0, 0)), ([[0]], (-1, 0))]:
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                shortest_grid_path(grid, start, (0, 0))


if __name__ == "__main__":
    unittest.main()
