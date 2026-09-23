import concurrent.futures
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from storage import LocalStore, encode, fingerprint


class ObjectPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = LocalStore(self.temp.name)
        self.addCleanup(self.store.db.close)

    def test_duplicate_does_not_reopen_published_bytes(self):
        value = {"total_cents": 1234}
        key = self.store.write_object(value)
        self.store.put("invoice", {"artifact": key}, 0)
        with patch("storage.tempfile.NamedTemporaryFile", side_effect=OSError("injected")):
            self.assertEqual(self.store.write_object(value), key)
        self.assertEqual(self.store.read_object(self.store.get("invoice")[1]["artifact"]), value)

    def test_failure_before_link_leaves_object_absent(self):
        value = {"total_cents": 1234}
        for target in ("storage.os.fsync", "storage.os.link"):
            with self.subTest(target=target), patch(target, side_effect=OSError("injected")):
                with self.assertRaises(OSError):
                    self.store.write_object(value)
            self.assertFalse((Path(self.temp.name) / (fingerprint(value) + ".json")).exists())
            self.assertEqual(list(Path(self.temp.name).glob(".object-*")), [])

    def test_failure_after_link_leaves_complete_unreferenced_object(self):
        value = {"total_cents": 1234}
        import os
        real_sync = os.fsync
        calls = []
        def fail_directory(fd):
            calls.append(fd)
            if len(calls) == 2:
                raise OSError("injected directory sync failure")
            return real_sync(fd)
        with patch("storage.os.fsync", side_effect=fail_directory):
            with self.assertRaises(OSError):
                self.store.write_object(value)
        self.assertEqual(self.store.read_object(fingerprint(value) + ".json"), value)
        self.assertEqual(self.store.get("invoice"), (0, None))

    def test_concurrent_publishers_agree_on_complete_bytes(self):
        value = {"large": "é" * 10000}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            keys = list(pool.map(lambda _: self.store.write_object(value), range(24)))
        self.assertEqual(len(set(keys)), 1)
        self.assertEqual(self.store.read_object(keys[0]), value)
        self.assertEqual((Path(self.temp.name) / keys[0]).read_bytes(), encode(value).encode())

    def test_existing_corruption_is_reported_not_overwritten(self):
        value = {"total_cents": 1234}
        destination = Path(self.temp.name) / (fingerprint(value) + ".json")
        destination.write_text("{")
        with self.assertRaises(ValueError):
            self.store.write_object(value)
        self.assertEqual(destination.read_text(), "{")
