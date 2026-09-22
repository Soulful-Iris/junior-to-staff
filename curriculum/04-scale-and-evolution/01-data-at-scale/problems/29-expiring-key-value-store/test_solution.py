import math
import unittest
from solution import ExpiringStore


class Clock:
    def __init__(self):
        self.now = 100

    def __call__(self):
        return self.now


class Tests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.store = ExpiringStore(self.clock)

    def test_exact_boundary_and_none_value(self):
        self.store.set('a', None, 5)
        self.clock.now = 104.999
        self.assertIsNone(self.store.get('a'))
        self.clock.now = 105
        with self.assertRaises(KeyError):
            self.store.get('a')
        self.assertNotIn('a', self.store._entries)

    def test_overwrite_zero_and_invalid_atomicity(self):
        self.store.set('a', 'old', 5)
        self.clock.now = 103
        self.store.set('a', 'new', 10)
        self.clock.now = 105
        self.assertEqual(self.store.get('a'), 'new')
        for ttl in [-1, math.inf, math.nan]:
            with self.assertRaises(ValueError):
                self.store.set('a', 'bad', ttl)
            self.assertEqual(self.store.get('a'), 'new')
        self.store.set('a', 'zero', 0)
        with self.assertRaises(KeyError):
            self.store.get('a')

    def test_purge_and_delete(self):
        self.store.set('a', 1, 2)
        self.store.set('b', 2, 3)
        self.store.set('c', 3, 5)
        self.clock.now = 103
        self.assertEqual(self.store.purge(), 2)
        self.assertEqual(self.store.purge(), 0)
        self.assertFalse(self.store.delete('missing'))
        self.assertTrue(self.store.delete('c'))
        self.assertFalse(self.store.delete('c'))

    def test_delete_expired_is_false(self):
        self.store.set('a', 1, 1)
        self.clock.now = 101
        self.assertFalse(self.store.delete('a'))


if __name__ == '__main__':
    unittest.main()
