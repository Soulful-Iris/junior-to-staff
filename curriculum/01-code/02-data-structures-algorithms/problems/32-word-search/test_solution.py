import copy
import unittest
from solution import word_search


class Tests(unittest.TestCase):
    def test_standard_and_restoration(self):
        board = [list('ABCE'), list('SFCS'), list('ADEE')]
        original = copy.deepcopy(board)
        for word, expected in [('ABCCED', True), ('SEE', True), ('ABCB', False)]:
            self.assertEqual(word_search(board, word), expected)
            self.assertEqual(board, original)

    def test_backtrack_to_alternative(self):
        self.assertTrue(word_search([list('AAA'), list('ABA'), list('AAA')], 'AAAAAB'))
        self.assertFalse(word_search([list('AB')], 'ABA'))
        self.assertFalse(word_search([list('AB'), list('CD')], 'AD'))

    def test_empty_and_deep(self):
        self.assertTrue(word_search([], ''))
        self.assertFalse(word_search([], 'A'))
        self.assertTrue(word_search([['A'] * 1500], 'A' * 1500))

    def test_invalid(self):
        for board in [[['A'], ['B', 'C']], [['AB']], [[1]]]:
            with self.assertRaises(ValueError):
                word_search(board, 'A')


if __name__ == '__main__':
    unittest.main()
