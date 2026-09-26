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
import time
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


def test_a_stop_inside_a_helper_names_the_loop_that_keeps_calling_it():
    # The output cap makes the stop land INSIDE the helper every time (at its
    # print). A clock-based version of this test passed with the old logic,
    # because in CPython the clock check happened to land on the loop's own
    # event, so it proved nothing; the live page had landed in the helper.
    code = ("def _next(n):\n    print('step')\n    return n\n\n"
            "def spin(x):\n    while x is not None:\n        x = _next(x)\n    return x\n")
    tests = "import unittest\nfrom solution import spin\nclass T(unittest.TestCase):\n    def test_it(self):\n        spin(1)\n"
    r = harness.run(code, tests, max_bytes=200)
    s = r["stopped"]
    assert s["kind"] == "output"
    assert s["loop"] == [6, 7] and s["function"] == "spin", s


# --- v2: the reader's own inputs, and a clean Python every run ----------------

TWO = PROBLEMS / "01-two-sum"


def test_an_input_returns_its_value_with_time_and_memory():
    r = harness.run((TWO / "solution.py").read_text(), _tests(TWO),
                    inputs=["two_sum([2, 7, 11, 15], 9)", "   "])
    assert len(r["inputs"]) == 1                          # blank ones are dropped
    i = r["inputs"][0]
    assert i["status"] == "ok" and i["value"] in ("[0, 1]", "(0, 1)")
    assert i["seconds"] >= 0 and isinstance(i["peak_bytes"], int)
    assert all(t["status"] == "pass" for t in r["tests"])


def test_time_counts_the_call_not_building_its_arguments():
    code = "def build(n):\n    return list(range(n))\n\ndef first(xs):\n    return xs[0]\n"
    tests = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n"
    r = harness.run(code, tests, inputs=["first(build(3_000_000))"], seconds=20)
    i = r["inputs"][0]
    assert i["value"] == "0" and i["seconds"] < 0.005, i


def test_memory_is_the_peak_during_the_call():
    code = "def grow(n):\n    return [0] * n\n\ndef nothing():\n    return None\n"
    tests = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n"
    r = harness.run(code, tests, inputs=["grow(250_000)", "nothing()"])
    big, small = r["inputs"]
    assert big["peak_bytes"] > 1_900_000 and small["peak_bytes"] < 10_000, (big, small)


def test_an_input_that_never_ends_is_stopped_and_the_tests_do_not_run():
    code = "def spin():\n    while True:\n        pass\n"
    tests = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n"
    r = harness.run(code, tests, inputs=["spin()"], seconds=0.3)
    assert r["status"] == "stopped" and r["stopped"]["input"] is True
    assert r["inputs"][0]["status"] == "stopped" and r["stopped"]["loop"] == [2, 3]
    assert r["tests"] == [] or all(t["status"] == "not-run" for t in r["tests"])


def test_an_input_that_fails_says_how_and_where():
    code = "def half(x):\n    return x / 0\n"
    tests = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n"
    r = harness.run(code, tests, inputs=["half(4)", "half(", "1, 2, 3, 4, 5, 6"] + ["half(1)"] * 5)
    assert len(r["inputs"]) == 5                           # never more than five
    a, b = r["inputs"][:2]
    assert a["status"] == "error" and a["failure"]["type"] == "ZeroDivisionError" and a["failure"]["line"] == 2
    assert b["status"] == "error" and b["failure"]["type"] == "SyntaxError"


def test_every_run_starts_from_a_clean_python():
    import builtins
    leaky = ("import builtins, sys, types\ncount = 0\ncount += 1\n"
             "builtins.LEAKED = count\nsys.modules['leaky'] = types.ModuleType('leaky')\n"
             "sys.path.append('/nowhere')\n")
    tests = "import unittest\nfrom solution import count\nclass T(unittest.TestCase):\n    def test_fresh(self):\n        self.assertEqual(count, 1)\n"
    path = list(sys.path)
    for _ in range(2):                                     # the second run sees nothing of the first
        r = harness.run(leaky, tests)
        assert r["tests"][0]["status"] == "pass"
        assert not hasattr(builtins, "LEAKED")
        assert "leaky" not in sys.modules
        assert sys.path == path


# --- v2: an input is a cell, and a test is timed only inside the reader's code

_NOOP_TESTS = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n"


def test_an_input_cell_can_build_what_one_expression_cannot():
    cell = """
        a, b, c = Node("a"), Node("b"), Node("c")
        a.next, b.next, c.next = b, c, b
        cycle_entry(a)
    """
    r = harness.run((CYCLE / "solution.py").read_text(), _tests(CYCLE), inputs=[cell])
    i = r["inputs"][0]
    assert i["status"] == "ok", i
    assert i["value"].startswith("Node(value='b'") and i["type"] == "Node", i
    assert isinstance(i["peak_bytes"], int) and i["seconds"] >= 0


def test_a_cell_that_does_not_end_in_a_call_says_so():
    r = harness.run((TWO / "solution.py").read_text(), _tests(TWO),
                    inputs=["x = two_sum([1, 2], 3)"])
    f = r["inputs"][0]["failure"]
    assert f["type"] == "No call to run" and f["input_line"] == 1


def test_an_error_in_the_setup_names_the_input_line():
    r = harness.run((TWO / "solution.py").read_text(), _tests(TWO),
                    inputs=["nums = [1, 2]\nnums.appendd(3)\ntwo_sum(nums, 3)"])
    f = r["inputs"][0]["failure"]
    assert f["type"] == "AttributeError" and f["input_line"] == 2 and f["line"] is None, f


def test_prints_during_the_memory_measurement_are_not_shown_twice():
    code = "def loud(n):\n    print('called with', n)\n    return n\n"
    r = harness.run(code, _NOOP_TESTS, inputs=["print('setup')\nloud(3)"])
    assert r["inputs"][0]["output"] == "setup\ncalled with 3\n", r["inputs"][0]


def test_measuring_memory_never_stops_a_correct_run():
    # The tips writers' case, on the reference answer: tracing a 600 x 600
    # table is about 13 times slower than running it, and when the memory pass
    # shared the reader's 3 seconds this whole run was stopped before a test ran.
    d = PROBLEMS / "35-edit-distance"
    r = harness.run((d / "solution.py").read_text(), _tests(d),
                    inputs=['edit_distance("ab" * 300, "ba" * 300)'])
    i = r["inputs"][0]
    assert r["status"] == "ok" and i["status"] == "ok", (r["status"], i)
    assert i["peak_bytes"] is None, "a call this slow is not traced"
    assert r["tests"] and all(t["status"] == "pass" for t in r["tests"])


def test_the_memory_pass_is_given_back_to_the_readers_time():
    run = harness._Run("", _NOOP_TESTS, (), 3.0, 65536, 200)
    run.deadline = before = time.monotonic() + 3.0
    peak = run._measure_memory(lambda: (lambda: time.sleep(0.25)), 0.001)
    assert isinstance(peak, int)
    assert 0.24 < run.memory_spent < 0.6
    assert abs(run.deadline - before - run.memory_spent) < 1e-9


def test_a_loop_in_an_inputs_own_lines_is_stopped():
    r = harness.run((TWO / "solution.py").read_text(), _tests(TWO),
                    inputs=["while True:\n    pass\ntwo_sum([1, 2], 3)"], seconds=0.3)
    assert r["status"] == "stopped" and r["stopped"]["input"] is True, r["status"]


def test_a_test_is_timed_inside_the_readers_code_not_its_setup():
    code = "def first(xs):\n    return xs[0]\n"
    tests = ("import unittest\nfrom solution import first\nclass T(unittest.TestCase):\n"
             "    def test_big_setup(self):\n        xs = list(range(2_000_000))\n"
             "        self.assertEqual(first(xs), 0)\n")
    t = harness.run(code, tests, seconds=20)["tests"][0]
    assert t["status"] == "pass"
    assert t["ms"] > 5 and t["code_ms"] < 1, t


def test_the_readers_own_loop_is_counted():
    code = "def count(n):\n    k = 0\n    for _ in range(n):\n        k += 1\n    return k\n"
    tests = ("import unittest\nfrom solution import count\nclass T(unittest.TestCase):\n"
             "    def test_loop(self):\n        self.assertEqual(count(300_000), 300_000)\n")
    t = harness.run(code, tests, seconds=20)["tests"][0]
    assert t["code_ms"] > 0.5 * t["ms"], t


def test_a_generator_is_timed_across_its_yields_and_not_between_them():
    code = ("def gen(n):\n    for i in range(n):\n        s = 0\n        for _ in range(2000):\n"
            "            s += 1\n        yield s\n")
    tests = ("import unittest\nfrom solution import gen\nclass T(unittest.TestCase):\n"
             "    def test_gen(self):\n        total = 0\n        for v in gen(100):\n"
             "            waste = list(range(20_000))\n            total += v\n"
             "        self.assertEqual(total, 200_000)\n")
    t = harness.run(code, tests, seconds=20)["tests"][0]
    assert t["status"] == "pass"
    assert 0 < t["code_ms"] < 0.6 * t["ms"], t        # the test's own list-building is not counted


def test_an_exception_leaving_the_readers_code_stops_the_clock():
    code = "def boom(depth):\n    if depth == 0:\n        raise ValueError('no')\n    return boom(depth - 1)\n"
    tests = ("import unittest\nfrom solution import boom\nclass T(unittest.TestCase):\n"
             "    def test_raise(self):\n        with self.assertRaises(ValueError):\n"
             "            boom(50)\n        waste = [list(range(1000)) for _ in range(2000)]\n")
    t = harness.run(code, tests, seconds=20)["tests"][0]
    assert t["status"] == "pass"
    assert t["code_ms"] < 0.2 * t["ms"], t            # still running after the raise would count the waste


def test_settings_the_reader_changes_do_not_reach_the_next_run():
    import gc, random
    code = ("import sys, gc, random\nsys.setrecursionlimit(50_000)\ngc.disable()\n"
            "random.seed(1)\nsys.settrace(lambda *a: None)\n"
            "def ask():\n    return input()\n")
    tests = ("import unittest\nfrom solution import ask\nclass T(unittest.TestCase):\n"
             "    def test_input(self):\n        with self.assertRaises(EOFError):\n            ask()\n")
    limit, state = sys.getrecursionlimit(), random.getstate()
    r = harness.run(code, tests)
    assert r["tests"][0]["status"] == "pass", r["tests"][0]   # input() did not wait
    assert sys.getrecursionlimit() == limit and gc.isenabled()
    assert sys.gettrace() is None and random.getstate() == state
