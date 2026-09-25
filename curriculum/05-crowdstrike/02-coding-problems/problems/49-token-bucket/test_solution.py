import unittest
from solution import TokenBucket


class TokenBucketTests(unittest.TestCase):
    def test_burst_and_refill(self):
        b = TokenBucket(2, 1)
        self.assertEqual([b.allow("t", 0) for _ in range(3)], [True, True, False])
        self.assertFalse(b.allow("t", 0.5))
        self.assertTrue(b.allow("t", 1.0))

    def test_refill_is_capped(self):
        b = TokenBucket(2, 1)
        for _ in range(2):
            b.allow("t", 0)
        self.assertEqual([b.allow("t", 100) for _ in range(3)], [True, True, False])

    def test_tenants_are_independent(self):
        b = TokenBucket(1, 1)
        self.assertTrue(b.allow("a", 0))
        self.assertTrue(b.allow("b", 0))
        self.assertFalse(b.allow("a", 0))

    def test_backward_clock(self):
        b = TokenBucket(1, 1)
        self.assertTrue(b.allow("t", 5))
        self.assertFalse(b.allow("t", 3))
        self.assertFalse(b.allow("t", 5.5))
        self.assertTrue(b.allow("t", 6))

    def test_exact_boundary(self):
        b = TokenBucket(1, 2)
        self.assertTrue(b.allow("t", 0))
        self.assertTrue(b.allow("t", 0.5))

    def test_sustained_rate_over_time(self):
        b = TokenBucket(5, 10)
        admitted = sum(b.allow("t", i / 100) for i in range(1000))  # 10 seconds at 100 req/s
        self.assertGreaterEqual(admitted, 100)
        self.assertLessEqual(admitted, 106)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            TokenBucket(0, 1)
        with self.assertRaises(ValueError):
            TokenBucket(1, 0)


if __name__ == "__main__":
    unittest.main()
