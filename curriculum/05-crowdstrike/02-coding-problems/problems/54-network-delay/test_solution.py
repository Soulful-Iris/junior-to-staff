import random
import unittest
from solution import network_delay


def bellman_ford_oracle(n, links, source):
    inf = float("inf")
    dist = [inf] * (n + 1)
    dist[source] = 0
    for _ in range(n):
        for u, v, w in links:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    reach = dist[1:]
    return None if inf in reach else max(reach)


class DelayTests(unittest.TestCase):
    def test_scenarios(self):
        self.assertEqual(network_delay(4, [(2, 1, 1), (2, 3, 1), (3, 4, 1)], 2), 2)
        self.assertIsNone(network_delay(2, [], 1))
        self.assertEqual(network_delay(1, [], 1), 0)
        self.assertEqual(network_delay(3, [(1, 3, 5), (1, 2, 1), (2, 3, 1)], 1), 2)
        self.assertEqual(network_delay(2, [(1, 2, 0)], 1), 0)
        self.assertEqual(network_delay(2, [(1, 2, 5), (1, 2, 2)], 1), 2)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            network_delay(2, [(1, 2, -1)], 1)
        with self.assertRaises(ValueError):
            network_delay(2, [], 0)
        with self.assertRaises(ValueError):
            network_delay(2, [(1, 3, 1)], 1)

    def test_matches_bellman_ford(self):
        rng = random.Random(21)
        for _ in range(200):
            n = rng.randint(1, 7)
            links = [(rng.randint(1, n), rng.randint(1, n), rng.randint(0, 9)) for _ in range(rng.randint(0, 12))]
            source = rng.randint(1, n)
            self.assertEqual(network_delay(n, links, source), bellman_ford_oracle(n, links, source))


if __name__ == "__main__":
    unittest.main()
