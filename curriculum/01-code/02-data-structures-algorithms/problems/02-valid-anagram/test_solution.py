import itertools
import unittest
from solution import valid_anagram

class AnagramTests(unittest.TestCase):
    def test_exact_text(self):
        self.assertTrue(valid_anagram("", ""))
        self.assertTrue(valid_anagram("aab", "aba"))
        self.assertFalse(valid_anagram("aab", "abb"))
        self.assertFalse(valid_anagram("é", "e\u0301"))
        self.assertFalse(valid_anagram("A", "a"))
        self.assertTrue(valid_anagram("🙂 a", "a🙂 "))
        with self.assertRaises(ValueError):
            valid_anagram(None, "")

    def test_sorting_oracle(self):
        words = ["".join(chars) for n in range(4)
                 for chars in itertools.product("abé", repeat=n)]
        for first in words:
            for second in words:
                self.assertEqual(valid_anagram(first, second), sorted(first) == sorted(second))

if __name__ == "__main__":
    unittest.main()
