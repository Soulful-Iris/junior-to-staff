from collections.abc import Mapping
import unittest
from solution import evaluate, lex


class Tests(unittest.TestCase):
    def test_precedence_and_parentheses(self):
        record = {'a': True, 'b': False, 'c': False}
        self.assertTrue(evaluate('a == TRUE OR b == TRUE AND c == TRUE', record))
        self.assertFalse(evaluate('(a == TRUE OR b == TRUE) AND c == TRUE', record))
        self.assertTrue(evaluate('((a == TRUE))', record))

    def test_missing_types_and_strings(self):
        self.assertFalse(evaluate('missing != "admin"', {}))
        self.assertFalse(evaluate('missing == "admin"', {}))
        self.assertFalse(evaluate('active == 1', {'active': True}))
        self.assertFalse(evaluate('active != 1', {'active': True}))
        self.assertTrue(evaluate('name == "A\\\"B" AND age == -2', {'name': 'A"B', 'age': -2}))
        self.assertTrue(evaluate('user.role != "guest"', {'user.role': 'admin'}))

    def test_malformed_input_is_not_hidden_by_short_circuit(self):
        cases = ['', 'a = 1', 'a ==', 'a == 1 OR', '(a == 1', 'a == 1)',
                 'a == 1 b == 2', 'a == 1 OR ???', 'a == "bad\\q"',
                 'a == 01', 'f(a) == 1', 'a == 1 and b == 2', 'a == "unterminated']
        for expression in cases:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                evaluate(expression, {'a': 1})

    def test_short_circuit_skips_record_access(self):
        class Record(Mapping):
            def __iter__(self):
                return iter(['a', 'danger'])
            def __len__(self):
                return 2
            def __getitem__(self, key):
                if key == 'danger':
                    raise AssertionError('short circuit failed')
                if key == 'a':
                    return 1
                raise KeyError(key)
        self.assertTrue(evaluate('a == 1 OR danger == 2', Record()))
        self.assertFalse(evaluate('a != 1 AND danger == 2', Record()))

    def test_resource_limits_and_long_chain(self):
        self.assertTrue(evaluate(' OR '.join(['a == 1'] * 700), {'a': 1}))
        with self.assertRaises(ValueError):
            evaluate('(' * 101 + 'a == 1' + ')' * 101, {'a': 1})
        with self.assertRaises(ValueError):
            lex(' OR '.join(['a == 1'] * 1100))
        with self.assertRaises(ValueError):
            evaluate('a == 1', [])


if __name__ == '__main__':
    unittest.main()
