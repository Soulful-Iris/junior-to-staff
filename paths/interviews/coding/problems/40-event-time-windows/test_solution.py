import itertools
import unittest
from solution import TumblingCounter


class Tests(unittest.TestCase):
    def test_late_event_and_exact_close(self):
        counter = TumblingCounter(10, 5)
        self.assertTrue(counter.add(9))
        self.assertTrue(counter.add(10))
        self.assertEqual(counter.advance_watermark(10), [])
        self.assertTrue(counter.add(2))
        self.assertEqual(counter.advance_watermark(14), [])
        self.assertEqual(counter.advance_watermark(15), [(0, 10, 2)])
        self.assertFalse(counter.add(9))
        self.assertTrue(counter.add(10))
        self.assertEqual(counter.advance_watermark(25), [(10, 20, 2)])
        self.assertEqual(counter.advance_watermark(25), [])

    def test_arrival_order_independence_before_close(self):
        for events in itertools.permutations([-1, 0, 9, 10]):
            counter = TumblingCounter(10)
            for event in events:
                self.assertTrue(counter.add(event))
            self.assertEqual(counter.advance_watermark(20), [(-10, 0, 1), (0, 10, 2), (10, 20, 1)])
            self.assertEqual(counter._counts, {})

    def test_empty_window_not_emitted_and_duplicate_counts(self):
        counter = TumblingCounter(10)
        counter.add(1)
        counter.add(1)
        counter.add(31)
        self.assertEqual(counter.advance_watermark(40), [(0, 10, 2), (30, 40, 1)])
        self.assertFalse(counter.add(21))

    def test_invalid_does_not_move_watermark_back(self):
        counter = TumblingCounter(10)
        counter.advance_watermark(20)
        with self.assertRaises(ValueError):
            counter.advance_watermark(19)
        self.assertEqual(counter.watermark, 20)
        for width, lateness in [(0, 0), (10, -1)]:
            with self.assertRaises(ValueError):
                TumblingCounter(width, lateness)
        with self.assertRaises(ValueError):
            counter.add(1.5)


if __name__ == '__main__':
    unittest.main()
