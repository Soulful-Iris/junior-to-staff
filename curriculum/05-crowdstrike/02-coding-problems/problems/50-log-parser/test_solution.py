import io
import unittest
from solution import count_errors


class LogParserTests(unittest.TestCase):
    def test_representative(self):
        lines = [
            "2026-09-25T10:14:03Z ERROR auth-api token expired for tenant 42",
            "2026-09-25T10:14:59Z ERROR auth-api token expired for tenant 43",
            "2026-09-25T10:15:00Z ERROR auth-api db timeout",
            "2026-09-25T10:15:01Z INFO auth-api ok",
        ]
        counts, malformed = count_errors(lines)
        self.assertEqual(counts, {("auth-api", "2026-09-25T10:14"): 2, ("auth-api", "2026-09-25T10:15"): 1})
        self.assertEqual(malformed, 0)

    def test_malformed_and_boundaries(self):
        counts, malformed = count_errors(["garbage", "2026-09-25 ERROR svc x", "2026-09-25T10:14:03Z ERROR svc a b c d\n"])
        self.assertEqual(counts, {("svc", "2026-09-25T10:14"): 1})
        self.assertEqual(malformed, 2)
        self.assertEqual(count_errors([]), ({}, 0))

    def test_accepts_a_file_object(self):
        f = io.StringIO("2026-09-25T10:14:03Z ERROR a x\n2026-09-25T10:14:04Z WARN a y\n")
        self.assertEqual(count_errors(f), ({("a", "2026-09-25T10:14"): 1}, 0))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            count_errors([42])


if __name__ == "__main__":
    unittest.main()
