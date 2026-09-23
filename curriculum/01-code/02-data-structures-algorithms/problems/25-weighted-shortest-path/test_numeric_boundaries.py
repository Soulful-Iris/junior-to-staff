import copy
import math
import unittest
from solution import weighted_shortest_path


class NumericBoundaryTests(unittest.TestCase):
    def test_finite_edges_cannot_silently_overflow_to_unreachable(self):
        graph = {'a': [('b', 1e308)], 'b': [('c', 1e308)], 'c': []}
        before = copy.deepcopy(graph)
        with self.assertRaises(OverflowError):
            weighted_shortest_path(graph, 'a', 'c')
        self.assertEqual(graph, before)

    def test_mixed_magnitudes_report_overflow(self):
        graph = {'a': [('b', 10**400)], 'b': [('c', 0.5)], 'c': []}
        with self.assertRaises(OverflowError):
            weighted_shortest_path(graph, 'a', 'c')

    def test_large_integer_sums_remain_exact(self):
        graph = {'a': [('b', 10**400)], 'b': [('c', 10**400)], 'c': []}
        self.assertEqual(weighted_shortest_path(graph, 'a', 'c'),
                         (2 * 10**400, ['a', 'b', 'c']))

    def test_float_and_unreachable_positive_controls(self):
        graph = {'a': [('b', 0.25)], 'b': [('c', 0.5)], 'c': [], 'd': []}
        self.assertEqual(weighted_shortest_path(graph, 'a', 'c'),
                         (0.75, ['a', 'b', 'c']))
        self.assertEqual(weighted_shortest_path(graph, 'a', 'd'), (math.inf, []))

    def test_bool_is_not_a_cost(self):
        with self.assertRaises(ValueError):
            weighted_shortest_path({'a': [('b', True)], 'b': []}, 'a', 'b')
