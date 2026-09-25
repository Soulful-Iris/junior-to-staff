import random
import unittest
from solution import order, CycleError


class OrderTests(unittest.TestCase):
    def test_scenarios(self):
        self.assertEqual(order(["a", "b", "c"], [("a", "c"), ("b", "c")]), ["a", "b", "c"])
        self.assertEqual(order(["b", "a"], []), ["a", "b"])
        self.assertEqual(order(["a", "b", "c"], [("a", "b"), ("b", "c")]), ["a", "b", "c"])
        self.assertEqual(order(["a", "b"], [("a", "b"), ("a", "b")]), ["a", "b"])

    def test_cycles_carry_a_witness(self):
        with self.assertRaises(CycleError) as ctx:
            order(["a", "b", "c"], [("a", "b"), ("b", "a")])
        cycle = ctx.exception.cycle
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(set(cycle), {"a", "b"})
        with self.assertRaises(CycleError) as ctx:
            order(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "b")])
        self.assertEqual(set(ctx.exception.cycle), {"b", "c"})

    def test_invalid(self):
        with self.assertRaises(ValueError):
            order(["a"], [("a", "zzz")])

    def test_random_dags_respect_every_edge(self):
        rng = random.Random(6)
        for _ in range(200):
            n = rng.randint(1, 8)
            tasks = [f"t{i}" for i in range(n)]
            rng.shuffle(tasks)
            rank = {t: i for i, t in enumerate(tasks)}
            edges = [(a, b) for a in tasks for b in tasks if rank[a] < rank[b] and rng.random() < 0.3]
            result = order(tasks, edges)
            self.assertEqual(sorted(result), sorted(tasks))
            pos = {t: i for i, t in enumerate(result)}
            for a, b in edges:
                self.assertLess(pos[a], pos[b])

    def test_random_cycles_are_detected(self):
        rng = random.Random(12)
        for _ in range(100):
            n = rng.randint(2, 6)
            tasks = [f"t{i}" for i in range(n)]
            cyc = rng.sample(tasks, rng.randint(2, n))
            edges = [(cyc[i], cyc[(i + 1) % len(cyc)]) for i in range(len(cyc))]
            edges += [(a, b) for a in tasks for b in tasks if a != b and rng.random() < 0.2]
            with self.assertRaises(CycleError) as ctx:
                order(tasks, edges)
            witness = ctx.exception.cycle
            self.assertEqual(witness[0], witness[-1])
            edge_set = set(edges)
            for a, b in zip(witness, witness[1:]):
                self.assertIn((a, b), edge_set)


if __name__ == "__main__":
    unittest.main()
