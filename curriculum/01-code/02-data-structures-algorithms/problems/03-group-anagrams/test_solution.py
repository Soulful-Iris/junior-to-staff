import random
import unittest
from collections import Counter
from solution import group_anagrams

class GroupTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(group_anagrams(["eat", "tea", "tan", "eat", "ate"]),
                         [["eat", "tea", "eat", "ate"], ["tan"]])
        self.assertEqual(group_anagrams([]), [])
        self.assertEqual(group_anagrams(["", ""]), [["", ""]])
        self.assertEqual(group_anagrams(["é", "e\u0301", "é"]), [["é", "é"], ["e\u0301"]])
        with self.assertRaises(ValueError):
            group_anagrams(["ok", 7])

    def test_pairwise_inventory_oracle(self):
        rng = random.Random(103)
        for _ in range(200):
            words = ["".join(rng.choices("abc", k=rng.randrange(6)))
                     for _ in range(rng.randrange(20))]
            expected = []
            for word in words:
                for group in expected:
                    if Counter(word) == Counter(group[0]):
                        group.append(word)
                        break
                else:
                    expected.append([word])
            original = words[:]
            self.assertEqual(group_anagrams(words), expected)
            self.assertEqual(words, original)

if __name__ == "__main__":
    unittest.main()
