import unittest
from solution import Trie


class InputContractTests(unittest.TestCase):
    def test_invalid_text_is_rejected_without_mutation(self):
        trie = Trie(["car", "card"])
        for value in (None, True, 1, [], "", "Car"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                trie.add(value)
            self.assertEqual(trie.suggest(""), ["car", "card"])
        for value in (None, True, 1, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                trie.suggest(value)
        self.assertEqual(trie.suggest("", 0), [])

    def test_constructor_and_limit(self):
        for value in (None, True, 1, "car"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Trie(value)
        self.assertEqual(Trie().suggest(""), [])
        trie = Trie(iter(["car"]))
        for limit in (True, None, [], -1, 0.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                trie.suggest("c", limit)
        self.assertEqual(trie.suggest("c", 1), ["car"])
