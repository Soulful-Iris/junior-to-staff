"""Run each independent Python example in its own process.

Many lessons intentionally call their module ``solution``. A single recursive
discovery can skip hyphenated directories or import another lesson's module.
This runner discovers test directories, isolates imports, and bounds hangs.
Candidate starters are intentionally broken; the default suites test references.
"""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coding-only", action="store_true")
    parser.add_argument("--report", type=Path, help="Optional JSON result outside source files")
    args = parser.parse_args()
    base = ROOT / "paths/interviews"
    search = base / "coding/problems" if args.coding_only else base
    directories = sorted({path.parent for path in search.rglob("test_*.py")})
    commands = [(str(path.relative_to(ROOT)), [sys.executable, "-m", "unittest", "discover", "-s", str(path), "-v"])
                for path in directories]
    if not args.coding_only:
        commands.append(("practice/assessor/heldback_importer.py",
                         [sys.executable, str(base / "practice/assessor/heldback_importer.py"), "--package", "reference", "-v"]))
    results = []
    for name, command in commands:
        try:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                       timeout=90, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            output = completed.stdout + completed.stderr
            count = re.search(r"Ran (\d+) tests? in", output)
            result = {"suite": name, "passed": completed.returncode == 0,
                      "tests": int(count.group(1)) if count else 0}
            if not result["passed"] or not count:
                result["passed"] = False
                result["output"] = output
        except subprocess.TimeoutExpired:
            result = {"suite": name, "passed": False, "tests": 0, "output": "Exceeded 90-second suite limit"}
        results.append(result)
        print(f'{"PASS" if result["passed"] else "FAIL"} {name}: {result["tests"]} tests', flush=True)
        if "output" in result:
            print(result["output"], flush=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(results, indent=2) + "\n")
    total = sum(result["tests"] for result in results)
    failures = sum(not result["passed"] for result in results)
    print(f"{len(results)} isolated suites; {total} tests; {failures} failing suites.")
    print("Browser, TypeScript, SQL-session, SVG playback, and AWS deployment checks are separate.")
    return 1 if failures or not results else 0


if __name__ == "__main__":
    raise SystemExit(main())
