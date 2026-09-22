"""Assessor-only variants. Select candidate package after its baseline is repaired."""
import argparse
import importlib
from pathlib import Path
import sys
import tempfile
import unittest

parser = argparse.ArgumentParser()
parser.add_argument("--package", choices=["reference", "starter"], default="reference")
args, remaining = parser.parse_known_args()
root = Path(__file__).resolve().parents[2] / "curriculum/02-applications/04-testing/labs/importer"
sys.path.insert(0, str(root))
run = importlib.import_module(args.package + ".importer").run
Store = importlib.import_module(args.package + ".store").Store
transport = importlib.import_module(args.package + ".transport")


def item(ident="held", amount="0.29"):
    return {"id":ident, "amount":amount, "currency":"USD"}


def page(items, cursor=None):
    return {"status":200, "body":{"items":items, "nextCursor":cursor}}


class HeldBack(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "held.db")
        self.store = Store(self.path)
        self.clock = transport.FakeClock()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_multi_hop_cycle(self):
        server = transport.FakeServer({"START":[page([],"p2")],"p2":[page([],"p3")],"p3":[page([],"p2")]},self.clock)
        with self.assertRaisesRegex(ValueError,"cycle"):
            run(server,self.clock,self.store)
        self.assertEqual(len(server.calls),3)

    def test_retry_consumes_transport_budget(self):
        server = transport.FakeServer({"START":[{"status":429,"retryAfter":0.8,"elapsed":0.3}]},self.clock)
        with self.assertRaises(TimeoutError):
            run(server,self.clock,self.store,budget=1)
        self.assertEqual(len(server.calls),1)
        self.assertEqual(self.clock.waits,[])

    def test_crash_and_equal_decimal_spelling(self):
        server = transport.FakeServer({"START":[page([item(amount="0.290")])]},self.clock)
        def crash():
            raise RuntimeError("lost process")
        with self.assertRaises(RuntimeError):
            run(server,self.clock,self.store,after_persist=crash)
        self.store.close()
        self.store = Store(self.path)
        server = transport.FakeServer({"START":[page([item(amount="0.29")])]},self.clock)
        self.assertEqual(run(server,self.clock,self.store),[("held",29,"USD")])

    def test_late_malformed_page_preserves_progress(self):
        server = transport.FakeServer({"START":[page([item("first")],"next")],
                                      "next":[page([item("valid"),item("bad","0.00001")])]},self.clock)
        with self.assertRaises(ValueError):
            run(server,self.clock,self.store)
        self.assertEqual(self.store.rows(),[("first",29,"USD")])
        self.assertEqual(self.store.checkpoint(),("next",0))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + remaining)
