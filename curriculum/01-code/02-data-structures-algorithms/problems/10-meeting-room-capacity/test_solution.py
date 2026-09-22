import random
import unittest
from solution import meeting_room_capacity

class RoomTests(unittest.TestCase):
    def test_endpoints_and_multiplicity(self):
        self.assertEqual(meeting_room_capacity([(0, 10), (5, 7), (7, 12)]), 2)
        self.assertEqual(meeting_room_capacity([(1, 2), (2, 3)]), 1)
        self.assertEqual(meeting_room_capacity([(1, 2)] * 4), 4)
        self.assertEqual(meeting_room_capacity([]), 0)
        for intervals in [[(4, 4)], [(4, 3)], [(1, False)], ["ab"], None]:
            with self.assertRaises(ValueError):
                meeting_room_capacity(intervals)

    def test_active_at_starts_oracle(self):
        rng = random.Random(110)
        for _ in range(500):
            intervals = []
            for _ in range(rng.randrange(20)):
                start = rng.randrange(-5, 10)
                intervals.append((start, start + rng.randrange(1, 8)))
            expected = max((sum(start <= time < end for start, end in intervals)
                            for time, _ in intervals), default=0)
            original = intervals[:]
            self.assertEqual(meeting_room_capacity(intervals), expected)
            self.assertEqual(intervals, original)

if __name__ == "__main__":
    unittest.main()
