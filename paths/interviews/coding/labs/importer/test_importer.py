"""Run from this directory. PACKAGE=starter switches the same contract tests."""
import copy
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path

package = os.environ.get("PACKAGE", "reference")
run = importlib.import_module(package + ".importer").run
Store = importlib.import_module(package + ".store").Store
transport = importlib.import_module(package + ".transport")
FakeServer, FakeClock = transport.FakeServer, transport.FakeClock
BASE = json.loads((Path(__file__).parent / "fixtures/basic.json").read_text())


class ImporterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "state.db")
        self.store = Store(self.path)
        self.clock = FakeClock()
        self.data = copy.deepcopy(BASE)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def execute(self, **kwargs):
        self.server = FakeServer(self.data, self.clock)
        return run(self.server, self.clock, self.store, **kwargs)

    def test_integer_money_dedup_and_completion(self):
        self.assertEqual(self.execute(), [("a", 29, "USD"), ("b", -110, "USD"), ("c", 0, "USD")])
        self.assertEqual(self.store.checkpoint(), (None, 1))
        self.assertEqual(self.execute(), self.store.rows())
        self.assertEqual(self.server.calls, [])

    def test_cycle_and_page_budget(self):
        self.data["p2"][0]["body"]["nextCursor"] = "p2"
        with self.assertRaisesRegex(ValueError, "cycle"):
            self.execute()
        self.assertEqual(len(self.server.calls), 2)

    def test_maximum_pages(self):
        with self.assertRaisesRegex(ValueError, "page budget"):
            self.execute(max_pages=1)
        self.assertEqual(self.store.checkpoint(), ("p2", 0))

    def test_retry_timing(self):
        self.data["START"].insert(0, {"status": 429, "retryAfter": 0.75})
        self.execute()
        self.assertEqual(self.clock.waits, [0.75])
        self.assertEqual(self.server.calls[1][1], 0.75)

    def test_total_deadline_includes_transport_and_wait(self):
        self.data["START"].insert(0, {"status": 429, "retryAfter": 0.8, "elapsed": 0.3})
        with self.assertRaises(TimeoutError):
            self.execute(budget=1)
        self.assertEqual(len(self.server.calls), 1)
        self.assertEqual(self.store.rows(), [])

    def test_transport_timeout_and_attempt_cap(self):
        self.data["START"] = [{"status": 503}]
        with self.assertRaisesRegex(TimeoutError, "attempt budget"):
            self.execute()
        self.assertEqual(len(self.server.calls), 3)
        self.data["START"] = [{"status": 200, "elapsed": 10}]
        with self.assertRaises(TimeoutError):
            self.execute(budget=1)

    def test_deadline_after_commit_leaves_replayable_checkpoint(self):
        def slow_persist_boundary():
            self.clock.now += 6
        with self.assertRaisesRegex(TimeoutError, "after persistence"):
            self.execute(after_persist=slow_persist_boundary)
        self.assertEqual(self.store.checkpoint(), (None, 0))
        self.assertEqual(len(self.store.rows()), 2)
        self.assertEqual(len(self.execute()), 3)

    def test_malformed_page_has_no_partial_page_effect(self):
        self.data["p2"][0]["body"]["items"].append({"id": "bad", "amount": "0.001", "currency": "USD"})
        with self.assertRaises(ValueError):
            self.execute()
        self.assertEqual(self.store.rows(), [("a", 29, "USD"), ("b", -110, "USD")])
        self.assertEqual(self.store.checkpoint(), ("p2", 0))

    def test_conflicting_duplicate_rolls_back_page(self):
        self.data["p2"][0]["body"]["items"] = [
            {"id": "new", "amount": "1", "currency": "USD"},
            {"id": "a", "amount": "2", "currency": "USD"}]
        with self.assertRaisesRegex(ValueError, "conflicting"):
            self.execute()
        self.assertNotIn("new", [row[0] for row in self.store.rows()])

    def test_restart_after_persist_before_checkpoint(self):
        def crash():
            raise RuntimeError("power loss")
        with self.assertRaises(RuntimeError):
            self.execute(after_persist=crash)
        self.assertEqual(self.store.checkpoint(), (None, 0))
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual(len(self.execute()), 3)

    def test_invalid_money_and_response_shapes(self):
        normalize = importlib.import_module(package + ".model").normalize
        for amount in ["NaN", "Infinity", "0.001", 0.29, "wat", "100000000000",
                       "0.290000000000000000000000000001", "9999999999.999999999999999999999",
                       "1e-1000000", "0" * 129]:
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                normalize({"id":"x", "currency":"USD", "amount":amount})
        self.data["START"][0]["body"] = {"items": []}
        with self.assertRaises(ValueError):
            self.execute()

    def test_money_is_independent_of_decimal_context(self):
        from decimal import localcontext
        normalize = importlib.import_module(package + ".model").normalize
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(normalize({"id":"x", "currency":"USD", "amount":"1234567.89"}), ("x", 123456789, "USD"))
            self.assertEqual(normalize({"id":"x", "currency":"USD", "amount":"0e-1000000"}), ("x", 0, "USD"))


if __name__ == "__main__":
    unittest.main()
