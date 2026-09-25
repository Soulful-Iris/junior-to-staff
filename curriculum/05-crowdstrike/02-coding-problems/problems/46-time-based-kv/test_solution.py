import random
import unittest
from solution import TimeMap


class TimeMapTests(unittest.TestCase):
    def test_scenarios(self):
        m = TimeMap()
        m.set("a", "x", 1)
        m.set("a", "y", 5)
        self.assertEqual(m.get("a", 7), "y")
        self.assertEqual(m.get("a", 5), "y")
        self.assertIsNone(m.get("a", 0))
        self.assertIsNone(m.get("b", 9))
        m.set("a", "z", 5)
        self.assertEqual(m.get("a", 5), "z")
        with self.assertRaises(ValueError):
            m.set("a", "w", 3)
        with self.assertRaises(ValueError):
            m.get("a", "5")

    def test_matches_linear_scan_oracle(self):
        rng = random.Random(5)
        m = TimeMap()
        history = {}
        last = {}
        for _ in range(500):
            key = rng.choice("pq")
            if rng.random() < 0.6:
                ts = last.get(key, 0) + rng.randint(0, 3)
                value = rng.randint(0, 99)
                m.set(key, value, ts)
                history.setdefault(key, {})[ts] = value
                last[key] = ts
            else:
                ts = rng.randint(0, 40)
                candidates = [t for t in history.get(key, {}) if t <= ts]
                expected = history[key][max(candidates)] if candidates else None
                self.assertEqual(m.get(key, ts), expected)


if __name__ == "__main__":
    unittest.main()
