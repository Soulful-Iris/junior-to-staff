import itertools
import unittest
from collections import Counter
from solution import minimum_covering_window

class CoverTests(unittest.TestCase):
    def test_examples_and_ties(self):
        self.assertEqual(minimum_covering_window("ABAAC", "AAC"), (2, 5))
        self.assertEqual(minimum_covering_window("abxba", "ab"), (0, 2))
        self.assertIsNone(minimum_covering_window("ab", "aa"))
        self.assertEqual(minimum_covering_window("", ""), (0, 0))
        self.assertEqual(minimum_covering_window("🙂x🙂é", "🙂é"), (2, 4))
        with self.assertRaises(ValueError):
            minimum_covering_window("abc", None)

    def test_all_substrings_oracle(self):
        for n in range(6):
            for chars in itertools.product("ab", repeat=n):
                text = "".join(chars)
                for required in ["", "a", "b", "aa", "ab", "aab"]:
                    candidates = [(i, j) for i in range(n + 1) for j in range(i, n + 1)
                                  if not (Counter(required) - Counter(text[i:j]))]
                    expected = min(candidates, key=lambda pair: (pair[1] - pair[0], pair[0])) if candidates else None
                    self.assertEqual(minimum_covering_window(text, required), expected)

if __name__ == "__main__":
    unittest.main()
