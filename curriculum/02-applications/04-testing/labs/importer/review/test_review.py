"""Apply each real PR in an isolated copy, and prove its review claim."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReviewTests(unittest.TestCase):
    def copy_and_apply(self, number):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        folder = Path(temp.name)
        shutil.copytree(ROOT / "reference", folder / "reference", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "fixtures", folder / "fixtures")
        shutil.copy(ROOT / "test_importer.py", folder / "test_importer.py")
        subprocess.run(["git","apply","--check",str(ROOT / f"review/pr-{number}.diff")],cwd=folder,check=True,capture_output=True)
        subprocess.run(["git","apply",str(ROOT / f"review/pr-{number}.diff")],cwd=folder,check=True,capture_output=True)
        return folder

    def test_pr101_proves_conflict_suppression_regression(self):
        folder = self.copy_and_apply(101)
        result = subprocess.run([sys.executable,"-m","unittest","test_importer.ImporterTests.test_conflicting_duplicate_rolls_back_page"],cwd=folder,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("ValueError not raised",result.stderr)

    def test_pr102_proves_retry_before_partner_allows(self):
        folder = self.copy_and_apply(102)
        result = subprocess.run([sys.executable,"-m","unittest","test_importer.ImporterTests.test_retry_timing"],cwd=folder,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("0.05",result.stderr)
        self.assertIn("0.75",result.stderr)

    def test_pr103_logs_bounded_metadata_without_payload(self):
        folder = self.copy_and_apply(103)
        script = '''
import unittest
from reference.transport import FakeClock, FakeServer, fetch
clock=FakeClock()
body={"items":[{"id":"private-account","amount":"3.21"}],"nextCursor":None}
server=FakeServer({"START":[{"status":200,"body":body}]},clock)
with unittest.TestCase().assertLogs("reference.transport",level="INFO") as logs:
    assert fetch(server,clock,None,5)==body
assert len(logs.output)==1
assert "attempt=1 status=200" in logs.output[0]
assert "private-account" not in logs.output[0] and "3.21" not in logs.output[0]
'''
        subprocess.run([sys.executable,"-c",script],cwd=folder,check=True,capture_output=True)


if __name__ == "__main__":
    unittest.main()
