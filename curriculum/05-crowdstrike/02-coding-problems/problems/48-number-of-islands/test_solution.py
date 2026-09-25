import copy
import random
import unittest
from solution import count_islands


def oracle(grid):
    """Union-find over cells, independent of the DFS reference."""
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                parent[(r, c)] = (r, c)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 1:
                continue
            for nr, nc in ((r + 1, c), (r, c + 1)):
                if (nr, nc) in parent:
                    parent[find((r, c))] = find((nr, nc))
    return len({find(x) for x in parent})


class IslandTests(unittest.TestCase):
    def test_scenarios(self):
        grid = [[1, 1, 0], [0, 0, 1], [1, 0, 1]]
        snapshot = copy.deepcopy(grid)
        self.assertEqual(count_islands(grid), 3)
        self.assertEqual(grid, snapshot)
        self.assertEqual(count_islands([[1, 0], [0, 1]]), 2)
        self.assertEqual(count_islands([[0, 0], [0, 0]]), 0)
        self.assertEqual(count_islands([[1, 1], [1, 1]]), 1)
        self.assertEqual(count_islands([]), 0)
        self.assertEqual(count_islands([[]]), 0)
        self.assertEqual(count_islands([[1] * 1000]), 1)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            count_islands([[1, 2]])
        with self.assertRaises(ValueError):
            count_islands([[1], [1, 1]])

    def test_matches_union_find_oracle(self):
        rng = random.Random(9)
        for _ in range(150):
            rows, cols = rng.randint(1, 7), rng.randint(1, 7)
            grid = [[1 if rng.random() < 0.55 else 0 for _ in range(cols)] for _ in range(rows)]
            self.assertEqual(count_islands(grid), oracle(grid), grid)


if __name__ == "__main__":
    unittest.main()
