"""End-to-end controls for the aggregate runner; no nested real repository runs."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "check_curriculum.py"


class RunnerTests(unittest.TestCase):
    def run_fixture(self, source, *, optional=False, registered=True, actual=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "examples/ai-systems"
            if actual:
                path.mkdir(parents=True)
                (path / "test_example.py").write_text(source)
            manifest = {"discovery_roots": ["examples"], "defaults": {
                "runtime": "python", "kind": "directory", "cwd": ".", "timeout_seconds": 10,
                "required": not optional, "skip_policy": "allow_all" if optional else "allow_partial"},
                "suites": [{"path": "examples/ai-systems"}] if registered else []}
            mf, rf = root / "manifest.json", root / "report.json"
            mf.write_text(json.dumps(manifest))
            proc = subprocess.run([sys.executable, str(RUNNER), "--root", str(root),
                "--manifest", str(mf), "--report", str(rf)], capture_output=True, text=True, timeout=15)
            return proc, json.loads(rf.read_text())

    def test_pass(self):
        proc, data = self.run_fixture("import unittest\nclass Test(unittest.TestCase):\n def test_ok(self): self.assertEqual(1+1,2)\n")
        self.assertEqual(proc.returncode, 0, proc.stdout+proc.stderr)
        self.assertEqual(data["summary"]["executed"], 1)
        self.assertIn("PASS examples/ai-systems", proc.stdout)

    def test_ai_failure_reaches_aggregate(self):
        proc, data = self.run_fixture("import unittest\nclass Test(unittest.TestCase):\n def test_bad(self): self.fail('injected AI defect')\n")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("injected AI defect", data["suites"][0]["failures"][0]["detail"])
        self.assertIn("FAIL examples/ai-systems", proc.stdout)

    def test_required_all_skipped_fails_and_keeps_reason(self):
        source = "import unittest\nclass Test(unittest.TestCase):\n @unittest.skip('fixture dependency absent')\n def test_skip(self): pass\n"
        proc, data = self.run_fixture(source)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(data["summary"]["executed"], 0)
        self.assertEqual(data["summary"]["skipped"], 1)
        self.assertIn("fixture dependency absent", proc.stdout)
        proc, data = self.run_fixture(source, optional=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["suites"][0]["skipped"][0]["reason"], "fixture dependency absent")

    def test_mixed_skips_visible(self):
        source = "import unittest\nclass Test(unittest.TestCase):\n def test_ok(self): pass\n @unittest.skip('optional adapter')\n def test_skip(self): pass\n"
        proc, data = self.run_fixture(source)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual((data["summary"]["executed"], data["summary"]["skipped"]), (1,1))
        self.assertIn("optional adapter", proc.stdout)

    def test_zero_tests_fails_explicitly(self):
        proc, data = self.run_fixture("# deliberately no tests\n")
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(data["summary"]["testsRun"], 0)

    def test_missing_and_unregistered_suites_fail(self):
        for options in ({"actual": False}, {"registered": False}):
            proc, data = self.run_fixture("# fixture\n", **options)
            self.assertNotEqual(proc.returncode, 0)
            self.assertTrue(data["manifest_error"])

    def test_expected_failure_and_unexpected_success_are_distinct(self):
        source = "import unittest\nclass Test(unittest.TestCase):\n @unittest.expectedFailure\n def test_expected(self): self.fail('known bug')\n"
        proc, data = self.run_fixture(source)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(len(data["suites"][0]["expectedFailures"]), 1)
        proc, data = self.run_fixture(source.replace("self.fail('known bug')", "pass"))
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(len(data["suites"][0]["unexpectedSuccesses"]), 1)
