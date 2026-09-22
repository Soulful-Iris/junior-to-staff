import itertools
import unittest
from solution import decode_ways


class Tests(unittest.TestCase):
    def test_examples_zero_rules(self):
        examples = {'': 0, '12': 2, '226': 3, '0': 0, '06': 0, '10': 1,
                    '100': 0, '101': 1, '27': 1, '11106': 2}
        for text, count in examples.items():
            self.assertEqual(decode_ways(text), count, text)

    def test_against_partition_oracle(self):
        def oracle(text):
            if not text:
                return 1
            total = 0
            for length in (1, 2):
                part = text[:length]
                if len(part) == length and part[0] != '0' and 1 <= int(part) <= 26:
                    total += oracle(text[length:])
            return total
        for length in range(1, 6):
            for chars in itertools.product('0126', repeat=length):
                text = ''.join(chars)
                self.assertEqual(decode_ways(text), oracle(text), text)

    def test_large_exact_result_and_invalid(self):
        self.assertGreater(decode_ways('1' * 100), 2 ** 63)
        for text in ['1x', '１２', ' 1']:
            with self.assertRaises(ValueError):
                decode_ways(text)


if __name__ == '__main__':
    unittest.main()
