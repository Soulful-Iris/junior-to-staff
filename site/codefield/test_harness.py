"""The code field's harness, run under CPython against the real problems.

    python3.12 -m pytest site/codefield/test_harness.py -q

The browser runs the same file under Pyodide; site/tools/codefield-check.mjs
drives that half. What these prove, and why each exists:

  * every reference solution passes through the harness. If the harness
    changed what a test means, a correct answer would fail on the page.
  * every starter runs and fails honestly: the page's "Write this:" block
    imports cleanly and does not pass by accident.
  * each limit fires, on the kind of code that really trips it, and says
    where: a loop that never ends, a print inside it, a recursion.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402
import starter  # noqa: E402

ROOT = HERE.parents[1]
PROBLEMS = ROOT / "curriculum/01-code/02-data-structures-algorithms/problems"
CASES = sorted(d for d in PROBLEMS.iterdir()
               if (d / "test_solution.py").is_file()
               and starter.starter_for((d / "README.md").read_text()))
CYCLE = PROBLEMS / "15-linked-list-cycle-entry"


def _tests(d: Path) -> str:
    return (d / "test_solution.py").read_text()


def _starter(d: Path) -> str:
    return starter.starter_for((d / "README.md").read_text())["code"]


def test_there_are_thirty_eight():
    assert len(CASES) == 38


@pytest.mark.parametrize("d", CASES, ids=lambda d: d.name)
def test_every_reference_solution_passes(d):
    r = harness.run((d / "solution.py").read_text(), _tests(d), seconds=20)
    assert r["status"] == "ok", r
    bad = [(t["name"], t.get("failure")) for t in r["tests"] if t["status"] != "pass"]
    assert not bad
    assert r["tests"], "no tests were found"


@pytest.mark.parametrize("d", CASES, ids=lambda d: d.name)
def test_every_starter_runs_and_fails_honestly(d):
    r = harness.run(_starter(d), _tests(d), seconds=20)
    assert r["status"] in ("ok", "stopped"), r
    assert any(t["status"] != "pass" for t in r["tests"])


def test_given_lines_are_the_data_not_the_answer():
    cyc = starter.starter_for((CYCLE / "README.md").read_text())
    lines = cyc["code"].splitlines()
    assert lines[0] == "from dataclasses import dataclass"
    assert cyc["given"] == [[1, 1], [3, 6]]
    assert lines[2].startswith("@dataclass") and lines[5].strip().startswith("next")
    trie = starter.starter_for((PROBLEMS / "30-trie-autocomplete/README.md").read_text())
    assert trie["given"] == []


BUGGY = _starter(CYCLE).replace("def cycle_entry(head):\n    ...", '''def cycle_entry(head):
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None
    p = head
    while p is not slow:
        PRINT
        slow = slow.next
    return p''')


def _line_of(code, text):
    return next(i for i, l in enumerate(code.splitlines(), 1) if text in l)


def test_a_loop_that_never_ends_is_stopped_at_the_loop():
    code = BUGGY.replace("        PRINT\n", "")
    r = harness.run(code, _tests(CYCLE), seconds=0.5)
    assert r["status"] == "stopped"
    s = r["stopped"]
    assert s["kind"] == "time"
    head = _line_of(code, "while p is not slow")
    assert s["loop"] == [head, head + 1]
    assert s["function"] == "cycle_entry"
    assert r["tests"][s["test"]]["status"] == "stopped"
    assert all(t["status"] == "not-run" for t in r["tests"][s["test"] + 1:])


def test_printing_forever_is_cut_at_the_allowance():
    code = BUGGY.replace("PRINT", 'print("walking from", p.value)')
    r = harness.run(code, _tests(CYCLE), seconds=5, max_bytes=4096)
    assert r["status"] == "stopped"
    s = r["stopped"]
    assert s["kind"] == "output" and s["bytes"] == 4096
    t = r["tests"][s["test"]]
    assert t["output_cut"] and len(t["output"].encode()) <= 4096
    assert t["output"].startswith("walking from 7")
    assert t["output"].endswith("\n")                # cut on a line boundary
    head = _line_of(code, "while p is not slow")
    assert s["loop"] == [head, head + 2]


def test_except_exception_cannot_swallow_the_stop():
    code = "def f():\n    while True:\n        try:\n            x = 1\n        except Exception:\n            pass\n"
    tests = "import unittest\nfrom solution import f\nclass T(unittest.TestCase):\n    def test_f(self):\n        f()\n"
    r = harness.run(code, tests, seconds=0.3)
    assert r["status"] == "stopped" and r["stopped"]["kind"] == "time"


def test_a_runaway_recursion_is_stopped_with_its_name():
    code = "def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\n"
    tests = "import unittest\nfrom solution import fib\nclass T(unittest.TestCase):\n    def test_big(self):\n        fib(60)\n"
    r = harness.run(code, tests, seconds=0.3)
    assert r["status"] == "stopped"
    assert r["stopped"]["function"] == "fib" and r["stopped"]["loop"] is None


def test_a_syntax_error_names_its_line():
    r = harness.run("def f(:\n    pass\n", _tests(CYCLE))
    assert r["status"] == "syntax" and r["error"]["line"] == 1


def test_a_missing_function_is_said_plainly():
    r = harness.run("x = 1\n", _tests(CYCLE))
    assert r["status"] == "import-error"
    assert "The tests import" in r["error"]["message"]


def test_a_failure_points_at_the_readers_line_and_the_check():
    code = BUGGY.replace("        PRINT\n", "").replace(
        "    p = head\n    while p is not slow:\n        slow = slow.next\n    return p",
        "    return slow")
    r = harness.run(code, _tests(CYCLE))
    t = next(t for t in r["tests"] if t["status"] == "fail")
    assert "assertIs" in t["failure"]["check"]["source"]
    assert "@" in t["failure"]["message"]          # bounded repr, identity tag


def test_breakpoints_record_the_values_and_stop_recording_at_the_cap():
    code = BUGGY.replace("        PRINT\n", "")
    line = _line_of(code, "slow = slow.next") if False else _line_of(code, "        slow = slow.next\n    return p") if False else None
    line = [i for i, l in enumerate(code.splitlines(), 1) if l.strip() == "slow = slow.next"][-1]
    r = harness.run(code, _tests(CYCLE), breakpoints=[line], seconds=0.5, max_stops=50)
    assert len(r["stops"]) == 50 and r["stops_truncated"]
    first = r["stops"][0]
    assert first["line"] == line and set(first["vars"]) >= {"p", "slow", "head"}
    assert first["test"] == r["stopped"]["test"]
    assert all(s["vars"]["p"] == first["vars"]["p"] for s in r["stops"])  # p never moves


def test_passing_tests_keep_their_own_prints():
    code = "def f(x):\n    print('saw', x)\n    return x\n"
    tests = ("import unittest\nfrom solution import f\nclass T(unittest.TestCase):\n"
             "    def test_a(self):\n        self.assertEqual(f(1), 1)\n"
             "    def test_b(self):\n        self.assertEqual(f(2), 2)\n")
    r = harness.run(code, tests)
    assert [t["output"] for t in r["tests"]] == ["saw 1\n", "saw 2\n"]


def test_values_never_run_away():
    code = ("class N:\n    def __init__(s, v, n=None):\n        s.value, s.next = v, n\n"
            "    def __repr__(s):\n        while True: pass\n")
    ns = {}
    exec(compile(code, "solution.py", "exec"), ns)
    N = ns["N"]
    N.__module__ = "solution"
    head = None
    for i in range(10000):
        head = N(i, head)
    a = N("a"); a.next = a
    assert len(harness.bounded_repr(head)) <= 160
    assert harness.bounded_repr(a).startswith("N(value='a'")


def test_the_world_is_put_back_after_every_run():
    out = sys.stdout
    harness.run(BUGGY.replace("PRINT", "print(1)"), _tests(CYCLE), seconds=0.3, max_bytes=100)
    harness.run(BUGGY.replace("        PRINT\n", ""), _tests(CYCLE), seconds=0.3)
    assert sys.stdout is out
    assert "solution" not in sys.modules and "test_solution" not in sys.modules
    assert all(sys.monitoring.get_tool(t) is None for t in range(6))


def test_the_json_door_round_trips():
    import json
    r = json.loads(harness.run_json(json.dumps({
        "code": (CYCLE / "solution.py").read_text(), "tests": _tests(CYCLE)})))
    assert r["status"] == "ok" and all(t["status"] == "pass" for t in r["tests"])
    bad = json.loads(harness.run_json("not json"))
    assert bad["status"] == "harness-error"


def _module(src):
    import types
    m = types.ModuleType("solution")
    sys.modules["solution"] = m          # as the harness does: dataclasses look it up
    try:
        exec(compile(src, "solution.py", "exec"), m.__dict__)
    finally:
        sys.modules.pop("solution", None)
    return m


def test_the_readers_classes_get_the_finalizer_and_it_finalizes_everything():
    """What CPython can show: the finalizer is installed and every node of a
    long chain goes through it. What it CANNOT show is the point of it, native
    stack depth during the free: CPython's own trashcan keeps that shallow
    here, and in the browser it does not. That property is checked where it
    bites, in site/tools/codefield-check.mjs, and that check was run red with
    the finalizer removed. (An earlier version of this test asserted
    finalizer nesting depth and passed with the queue deleted: a finalizer
    returns before its object's children are freed, so Python-level nesting
    never grows either way.)"""
    m = _module("class N:\n    def __init__(s, v, n=None):\n        s.value, s.next = v, n\n")
    assert harness.make_frees_iterative(m) == ["N"]
    seen = [0]
    real = harness._finalize

    def counting(self):
        seen[0] += 1
        real(self)
    m.N.__del__ = counting
    head = None
    for i in range(50_000):
        head = m.N(i, head)
    del head
    assert seen[0] == 50_000


def test_a_dataclass_prints_without_running_away_and_a_written_repr_is_kept():
    m = _module("from dataclasses import dataclass\n@dataclass(eq=False)\nclass N:\n"
                "    value: object\n    next: 'N | None' = None\n"
                "class Own:\n    def __repr__(self):\n        return 'mine'\n"
                "@dataclass\nclass Mine:\n    x: int = 1\n    def __repr__(self):\n        return 'written'\n")
    harness.make_frees_iterative(m)
    head = None
    for i in range(10_000):
        head = m.N(i, head)
    text = repr(head)
    assert text.startswith("N(value=9999, next=N(value=9998") and len(text) < 2100
    assert repr(m.N(1)) == "N(value=1, next=None)"
    assert repr(m.Own()) == "mine" and repr(m.Mine()) == "written"


@pytest.mark.parametrize("name", ["14-reverse-linked-list", "15-linked-list-cycle-entry",
                                  "16-merge-sorted-lists", "17-tree-level-order",
                                  "18-validate-bst", "20-tree-diameter"])
def test_the_deep_problems_still_pass_with_teardown(name):
    d = PROBLEMS / name
    r = harness.run((d / "solution.py").read_text(), _tests(d), seconds=20)
    assert r["status"] == "ok" and all(t["status"] == "pass" for t in r["tests"]), r
