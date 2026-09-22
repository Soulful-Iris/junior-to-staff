import itertools
import unittest
from solution import shipping_capacity

class ShippingTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(shipping_capacity([3, 2, 2, 4, 1, 4], 3), 6)
        self.assertEqual(shipping_capacity([], 2), 0)
        self.assertEqual(shipping_capacity([5, 1], 20), 5)
        self.assertEqual(shipping_capacity([5, 1], 1), 6)
        for weights, days in [([0, 3], 2), ([1], 0), ([1], True), ([-1], 2), ([1.0], 2)]:
            with self.assertRaises(ValueError):
                shipping_capacity(weights, days)

    def test_enumerated_partition_oracle(self):
        for n in range(1, 6):
            for weights in itertools.product(range(1, 4), repeat=n):
                for days in range(1, n + 2):
                    candidates = []
                    for mask in range(1 << (n - 1)):
                        groups = []
                        start = 0
                        for i in range(n - 1):
                            if mask & (1 << i):
                                groups.append(sum(weights[start:i + 1]))
                                start = i + 1
                        groups.append(sum(weights[start:]))
                        if len(groups) <= days:
                            candidates.append(max(groups))
                    self.assertEqual(shipping_capacity(weights, days), min(candidates))

if __name__ == "__main__":
    unittest.main()
