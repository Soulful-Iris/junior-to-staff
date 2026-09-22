import unittest
from solution import word_ladder


class Tests(unittest.TestCase):
    def test_shortest_and_valid(self):
        words = ["hot", "dot", "dog", "lot", "log", "cog"]
        path = word_ladder("hit", "cog", words)
        self.assertEqual(len(path), 5)
        self.assertEqual((path[0], path[-1]), ("hit", "cog"))
        self.assertTrue(all(word in words for word in path[1:]))
        self.assertTrue(all(sum(a != b for a, b in zip(x, y)) == 1
                            for x, y in zip(path, path[1:])))

    def test_missing_and_unreachable(self):
        self.assertEqual(word_ladder("hit", "cog", ["hot"]), [])
        self.assertEqual(word_ladder("hit", "cog", ["hot", "cog"]), [])

    def test_identity_direct_duplicates(self):
        self.assertEqual(word_ladder("a", "a", []), ["a"])
        self.assertEqual(word_ladder("a", "b", ["b", "b"]), ["a", "b"])

    def test_validation(self):
        for start, end, words in [("", "", []), ("a", "bb", []),
                                  ("a", "b", ["C"]), ("a", "b", ["zz"])]:
            with self.subTest(start=start, words=words), self.assertRaises(ValueError):
                word_ladder(start, end, words)


if __name__ == "__main__":
    unittest.main()
