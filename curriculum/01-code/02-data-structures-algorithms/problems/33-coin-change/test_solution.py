from collections import deque
import unittest
from solution import minimum_coins


class Tests(unittest.TestCase):
    def test_greedy_failure_and_witness(self):
        self.assertEqual(minimum_coins([1, 3, 4], 6), (2, [3, 3]))
        self.assertEqual(minimum_coins([2, 2], 3), (-1, []))
        self.assertEqual(minimum_coins([], 0), (0, []))
        self.assertEqual(minimum_coins([], 5), (-1, []))

    def test_against_bfs_amount_oracle(self):
        for coins in [[1, 3, 4], [2, 5], [4, 6, 9]]:
            for amount in range(35):
                queue, seen, expected = deque([(0, 0)]), {0}, -1
                while queue:
                    subtotal, distance = queue.popleft()
                    if subtotal == amount:
                        expected = distance
                        break
                    for coin in coins:
                        new = subtotal + coin
                        if new <= amount and new not in seen:
                            seen.add(new)
                            queue.append((new, distance + 1))
                count, used = minimum_coins(coins, amount)
                self.assertEqual(count, expected)
                if count >= 0:
                    self.assertEqual(len(used), count)
                    self.assertEqual(sum(used), amount)
                    self.assertTrue(all(c in coins for c in used))

    def test_invalid(self):
        for coins, amount in [([0], 1), ([-2], 3), ([1], -1)]:
            with self.assertRaises(ValueError):
                minimum_coins(coins, amount)


if __name__ == '__main__':
    unittest.main()
