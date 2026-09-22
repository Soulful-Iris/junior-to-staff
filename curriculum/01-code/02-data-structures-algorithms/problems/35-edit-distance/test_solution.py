from functools import lru_cache
import itertools
import unittest
from solution import edit_distance


class Tests(unittest.TestCase):
    def test_operations_and_boundaries(self):
        for a, b, expected in [('kitten', 'sitting', 3), ('cat', 'cut', 1),
                                ('', '', 0), ('', 'abc', 3), ('same', 'same', 0),
                                ('ab', 'ba', 2)]:
            self.assertEqual(edit_distance(a, b), expected)
            self.assertEqual(edit_distance(b, a), expected)

    def test_against_recursive_oracle(self):
        @lru_cache(None)
        def oracle(a, b):
            if not a or not b:
                return len(a) + len(b)
            return min(1 + oracle(a[1:], b), 1 + oracle(a, b[1:]),
                       (a[0] != b[0]) + oracle(a[1:], b[1:]))
        words = [''.join(chars) for n in range(4) for chars in itertools.product('ab', repeat=n)]
        for a in words:
            for b in words:
                self.assertEqual(edit_distance(a, b), oracle(a, b))

    def test_unicode_codepoints_and_invalid(self):
        self.assertEqual(edit_distance('é', 'e'), 1)
        self.assertEqual(edit_distance('é', 'e\u0301'), 2)
        with self.assertRaises(ValueError):
            edit_distance([], '')


if __name__ == '__main__':
    unittest.main()
