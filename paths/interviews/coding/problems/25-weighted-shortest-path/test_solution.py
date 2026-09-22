import math
import random
import unittest
from solution import weighted_shortest_path


class Tests(unittest.TestCase):
    def test_discovery_is_not_final(self):
        graph = {"a": [("b", 8), ("c", 1)], "c": [("b", 2)], "b": []}
        self.assertEqual(weighted_shortest_path(graph, "a", "b"), (3, ["a", "c", "b"]))

    def test_zero_cycle_ties_and_unreachable(self):
        graph = {0: [(1, 0), ("x", 0)], 1: [(0, 0)], "x": [], 2: []}
        self.assertEqual(weighted_shortest_path(graph, 0, 1), (0, [0, 1]))
        self.assertEqual(weighted_shortest_path(graph, 0, 0), (0, [0]))
        self.assertEqual(weighted_shortest_path(graph, 0, 2), (math.inf, []))

    def test_against_relaxation_oracle(self):
        rng = random.Random(25)
        for _ in range(30):
            graph = {i: [(j, rng.randrange(6)) for j in range(6)
                         if i != j and rng.random() < .35] for i in range(6)}
            expected = [0] + [math.inf] * 5
            for _ in range(5):
                for a, edges in graph.items():
                    for b, weight in edges:
                        expected[b] = min(expected[b], expected[a] + weight)
            for target in graph:
                cost, path = weighted_shortest_path(graph, 0, target)
                self.assertEqual(cost, expected[target])
                if path:
                    actual = sum(dict(graph[a])[b] for a, b in zip(path, path[1:]))
                    self.assertEqual(cost, actual)

    def test_invalid_even_in_disconnected_component(self):
        for weight in [-1, math.inf, math.nan]:
            with self.assertRaises(ValueError):
                weighted_shortest_path({0: [], 1: [(1, weight)]}, 0, 0)
        with self.assertRaises(ValueError):
            weighted_shortest_path({0: [(1, 2)]}, 0, 0)

    def test_none_vertex_and_large_integer_cost(self):
        cost = 10 ** 400
        self.assertEqual(weighted_shortest_path({None: [('end', cost)], 'end': []}, None, 'end'),
                         (cost, [None, 'end']))


if __name__ == "__main__":
    unittest.main()
