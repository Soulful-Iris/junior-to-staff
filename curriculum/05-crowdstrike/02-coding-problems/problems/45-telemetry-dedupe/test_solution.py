import random
import unittest
from solution import Deduper


class DedupeTests(unittest.TestCase):
    def test_scenarios(self):
        d = Deduper(10)
        self.assertTrue(d.accept("s1", 7, 100))
        self.assertFalse(d.accept("s1", 7, 100))
        self.assertTrue(d.accept("s2", 7, 100))
        self.assertTrue(d.accept("s1", 6, 101))
        self.assertTrue(d.accept("s1", 8, 120))
        self.assertTrue(d.accept("s1", 7, 120))  # forgotten, so re-emitted
        self.assertEqual(d.size(), 2)

    def test_too_old_is_dropped(self):
        d = Deduper(10)
        self.assertTrue(d.accept("s", 1, 100))
        self.assertFalse(d.accept("s", 2, 80))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            Deduper(0)
        with self.assertRaises(ValueError):
            Deduper(5).accept("s", "1", 1)

    def test_matches_brute_force_oracle(self):
        rng = random.Random(11)
        window = 5
        d = Deduper(window)
        history = []  # (ts, key) of emitted events
        now = None
        for _ in range(400):
            ts = rng.randint(0, 60)
            key = (rng.choice("ab"), rng.randint(0, 6))
            now = ts if now is None else max(now, ts)
            expected = ts > now - window and all(
                not (k == key and t > now - window) for t, k in history)
            got = d.accept(key[0], key[1], ts)
            self.assertEqual(got, expected, (ts, key, now))
            if got:
                history.append((ts, key))
            self.assertLessEqual(d.size(), len({k for t, k in history if t > now - window}) + 0)


if __name__ == "__main__":
    unittest.main()
