import unittest
from solution import Trie


class Tests(unittest.TestCase):
    def test_shared_prefix_and_terminal(self):
        trie = Trie(['cart', 'cat', 'car', 'dog', 'car'])
        self.assertEqual(trie.suggest('ca'), ['car', 'cart', 'cat'])
        self.assertEqual(trie.suggest('car', 1), ['car'])
        self.assertEqual(trie.suggest('ca', 2), ['car', 'cart'])
        self.assertEqual(trie.suggest('z'), [])

    def test_against_filter_sort_and_dynamic_add(self):
        words = ['a', 'ab', 'abc', 'ac', 'b', 'ba', 'bac', 'bb', 'z']
        trie = Trie(reversed(words))
        for prefix in ['', 'a', 'ab', 'b', 'ba', 'x']:
            for limit in range(12):
                self.assertEqual(trie.suggest(prefix, limit),
                                 sorted(w for w in words if w.startswith(prefix))[:limit])
        trie.add('az')
        self.assertEqual(trie.suggest('az'), ['az'])

    def test_long_word_and_validation(self):
        word = 'a' * 2000
        self.assertEqual(Trie([word]).suggest('a'), [word])
        for word in ['', 'Car', 'a-b']:
            with self.assertRaises(ValueError):
                Trie([word])
        with self.assertRaises(ValueError):
            Trie().suggest('', -1)


if __name__ == '__main__':
    unittest.main()
