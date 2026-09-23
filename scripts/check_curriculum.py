"""Run registered reference suites in isolated processes, reporting skips honestly.

The manifest covers curriculum, AI examples and tooling. Browser, real PostgreSQL
and cloud execution are distinct gates; a Python success never implies they ran.
"""
from pathlib import Path
import argparse
import json
import os
import platform
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]


def run_suite(path, kind, result_path):
    """Child entry point: use TestResult, not human-output regexes."""
    loader = unittest.TestLoader()
    if kind == "directory":
        suite = loader.discover(str(path), pattern="test_*.py")
    else:
        sys.argv = [str(path)]  # assessor module defaults to reference, not starter
        module = types.ModuleType("registered_suite")
        module.__dict__.update(runpy.run_path(str(path), run_name="registered_suite"))
        suite = loader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "testsRun": result.testsRun,
        "failures": [{"test": t.id(), "detail": text} for t, text in result.failures],
        "errors": [{"test": t.id(), "detail": text} for t, text in result.errors],
        "skipped": [{"test": t.id(), "reason": reason} for t, reason in result.skipped],
        "expectedFailures": [t.id() for t, _ in result.expectedFailures],
        "unexpectedSuccesses": [t.id() for t in result.unexpectedSuccesses],
    }
    result_path.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if result.wasSuccessful() else 1


def load_manifest(root, path):
    data = json.loads(path.read_text())
    suites = []
    for entry in data["suites"]:
        spec = {**data["defaults"], **entry}
        target = root / spec["path"]
        if not target.resolve().is_relative_to(root) or not target.exists():
            raise ValueError(f"Missing/unsafe registered suite: {spec['path']}")
        if spec["runtime"] != "python" or spec["skip_policy"] not in ("allow_partial", "forbid", "allow_all"):
            raise ValueError(f"Invalid runtime/skip policy: {spec['path']}")
        if not (root / spec["cwd"]).resolve().is_relative_to(root):
            raise ValueError("Unsafe suite working directory")
        suites.append(spec)
    registered = {s["path"] for s in suites if s["kind"] == "directory"}
    if len({s["path"] for s in suites}) != len(suites):
        raise ValueError("Duplicate suite ID")
    discovered = {str(p.parent.relative_to(root)) for base in data["discovery_roots"]
                  for p in (root / base).rglob("test_*.py")}
    if registered != discovered:
        raise ValueError(f"Suite manifest mismatch: missing={sorted(registered-discovered)}; unregistered={sorted(discovered-registered)}")
    return suites


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coding-only", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT, help="Fixture root for runner tests")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--suite", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--kind", choices=("directory", "file"), default="directory", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.suite:
        return run_suite(args.suite, args.kind, args.report)
    root = args.root.resolve()
    report = {"runtime": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version},
              "suites": [], "manifest_error": None}
    source = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    report["source_commit"] = source.stdout.strip() if source.returncode == 0 else None
    report["scope"] = "coding-only" if args.coding_only else "all-registered-python"
    try:
        suites = load_manifest(root, args.manifest or root / "indexes/python-suites.json")
        if args.coding_only:
            bank = json.loads((root / "indexes/problem-bank.json").read_text())
            selected = {item["directory"] for item in bank}
            if len(bank) != len(selected) or not selected <= {s["path"] for s in suites}:
                raise ValueError("Coding registry contains duplicate or unregistered suites")
            suites = [s for s in suites if s["path"] in selected]
    except (ValueError, KeyError, OSError) as exc:
        report["manifest_error"] = str(exc)
        suites = []
        print(f"FAIL manifest: {exc}", flush=True)
    for spec in suites:
        with tempfile.TemporaryDirectory() as temp:
            result_path = Path(temp) / "result.json"
            command = [sys.executable, str(SCRIPT), "--suite", str(root / spec["path"]),
                       "--kind", spec["kind"], "--report", str(result_path)]
            result = {"suite": spec["path"], "command": command, "required": spec["required"],
                      "passed": False, "testsRun": 0, "skipped": [], "executed": 0}
            try:
                completed = subprocess.run(command, cwd=root / spec["cwd"], capture_output=True,
                    text=True, timeout=spec["timeout_seconds"],
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                result["output"] = completed.stdout + completed.stderr
                if result_path.exists():
                    result.update(json.loads(result_path.read_text()))
                    result["executed"] = result["testsRun"] - len(result["skipped"])
                    all_skipped = result["testsRun"] > 0 and result["executed"] == 0
                    skip_ok = not result["skipped"] or spec["skip_policy"] != "forbid"
                    if all_skipped and (spec["required"] or spec["skip_policy"] != "allow_all"):
                        skip_ok = False
                    result["passed"] = completed.returncode == 0 and result["testsRun"] > 0 and skip_ok
            except subprocess.TimeoutExpired as exc:
                result["output"] = f"Suite exceeded {spec['timeout_seconds']} seconds"
                result["timeout"] = True
            report["suites"].append(result)
            state = "PASS" if result["passed"] else "FAIL"
            print(f"{state} {spec['path']}: {result['executed']} executed, {len(result['skipped'])} skipped", flush=True)
            for skipped in result["skipped"]:
                print(f"  SKIP {skipped['test']}: {skipped['reason']}", flush=True)
            if not result["passed"]:
                print(result.get("output", "No structured result"), flush=True)
    results = report["suites"]
    report["summary"] = {"suites": len(results), "testsRun": sum(r["testsRun"] for r in results),
        "executed": sum(r["executed"] for r in results), "skipped": sum(len(r["skipped"]) for r in results),
        "failing_suites": sum(not r["passed"] for r in results)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"]), flush=True)
    print("Browser, TypeScript, real SQL sessions, diagram rendering and AWS deployment are separate gates.")
    return int(bool(report["manifest_error"] or not results or report["summary"]["failing_suites"]))


if __name__ == "__main__":
    raise SystemExit(main())
