import unittest
from solution import TopK


class InputContractTests(unittest.TestCase):
    def test_invalid_capacity(self):
        for value in (True, None, [], -1, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                TopK(value)

    def test_invalid_observation_preserves_state_even_at_zero_capacity(self):
        for k in (0, 2):
            top = TopK(k)
            top.add(3)
            before = top.largest()
            for value in (True, None, [], 1.5):
                with self.subTest(k=k, value=value), self.assertRaises(ValueError):
                    top.add(value)
                self.assertEqual(top.largest(), before)
