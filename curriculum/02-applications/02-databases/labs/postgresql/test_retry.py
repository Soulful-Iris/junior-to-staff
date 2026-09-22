import unittest
from retry import transaction_retry


class DatabaseError(Exception):
    def __init__(self, state):
        self.sqlstate = state


class RetryTests(unittest.TestCase):
    def test_reexecutes_full_callback_and_bounds_attempts(self):
        attempts, waits = [], []
        def operation():
            attempts.append("begin-read-decide-write-commit")
            if len(attempts) < 3:
                raise DatabaseError("40001")
            return "committed"
        self.assertEqual(transaction_retry(operation, wait=waits.append, jitter=lambda: .5), "committed")
        self.assertEqual(len(attempts), 3)
        self.assertEqual(waits, [.005, .01])
        failures = []
        def unavailable():
            failures.append(1)
            raise DatabaseError("40P01")
        with self.assertRaises(DatabaseError):
            transaction_retry(unavailable, wait=lambda _: None)
        self.assertEqual(len(failures), 3)

    def test_does_not_retry_integrity_error(self):
        calls = []
        def operation():
            calls.append(1)
            raise DatabaseError("23505")
        with self.assertRaises(DatabaseError):
            transaction_retry(operation, wait=lambda _: self.fail("must not wait"))
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
