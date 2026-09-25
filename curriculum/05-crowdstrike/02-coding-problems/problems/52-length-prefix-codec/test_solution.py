import random
import unittest
from solution import encode, decode, FrameDecoder


class CodecTests(unittest.TestCase):
    def test_scenarios(self):
        self.assertEqual(encode([b"a", b"bc"]), b"\x00\x00\x00\x01a\x00\x00\x00\x02bc")
        self.assertEqual(decode(encode([b"a", b"bc"])), [b"a", b"bc"])
        self.assertEqual(encode([b""]), b"\x00\x00\x00\x00")
        self.assertEqual(decode(b"\x00\x00\x00\x00"), [b""])
        self.assertEqual(encode([]), b"")
        items = [b"\x00\x00\x00\x05", b"\n", b"a" * 1000]
        self.assertEqual(decode(encode(items)), items)

    def test_chunked_feed(self):
        data = encode([b"a", b"bc"])
        dec = FrameDecoder()
        seen = []
        for i in range(len(data)):
            frames = dec.feed(data[i:i + 1])
            seen.append(frames)
        self.assertEqual([f for fs in seen for f in fs], [b"a", b"bc"])
        self.assertEqual(seen[4], [b"a"])
        self.assertEqual(seen[-1], [b"bc"])
        self.assertEqual(dec.pending(), 0)

    def test_errors(self):
        with self.assertRaises(ValueError):
            decode(b"\x00\x00\x00\x05ab")
        with self.assertRaises(ValueError):
            decode(b"\x80\x00\x00\x00" + b"x")
        with self.assertRaises(ValueError):
            encode(["a"])

    def test_random_round_trips_with_random_chunking(self):
        rng = random.Random(8)
        for _ in range(100):
            items = [bytes(rng.randrange(256) for _ in range(rng.randint(0, 20))) for _ in range(rng.randint(0, 6))]
            data = encode(items)
            dec = FrameDecoder()
            out = []
            i = 0
            while i < len(data):
                j = min(len(data), i + rng.randint(1, 7))
                out.extend(dec.feed(data[i:j]))
                i = j
            self.assertEqual(out, items)
            self.assertEqual(dec.pending(), 0)


if __name__ == "__main__":
    unittest.main()
