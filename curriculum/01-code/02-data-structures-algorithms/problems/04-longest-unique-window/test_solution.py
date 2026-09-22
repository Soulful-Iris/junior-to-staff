import itertools
import unittest
from solution import longest_unique_window

class WindowTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(longest_unique_window("abba"), (0, 2))
        self.assertEqual(longest_unique_window(""), (0, 0))
        self.assertEqual(longest_unique_window("aaaa"), (0, 1))
        self.assertEqual(longest_unique_window("🙂é🙂x"), (1, 4))
        with self.assertRaises(ValueError):
            longest_unique_window([])

    def test_substring_oracle(self):
        for n in range(7):
            for chars in itertools.product("abc", repeat=n):
                text = "".join(chars)
                candidates = [(i, j) for i in range(n + 1) for j in range(i, n + 1)
                              if len(set(text[i:j])) == j - i]
                expected = min(candidates, key=lambda pair: (-(pair[1] - pair[0]), pair[0]))
                self.assertEqual(longest_unique_window(text), expected)

if __name__ == "__main__":
    unittest.main()
