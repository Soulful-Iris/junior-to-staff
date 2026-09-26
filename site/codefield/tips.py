"""Tips for the code field: what each problem's page can say when a reader asks.

Bruno, 2026-09-26: "IT WOULD BE A NICE PLUS if the user can ask for a tip. But
thats definitely harder without depending on AI. Maybe have some metadata for
the problems and depending on the error or something we expect them to mess
around with, have those answers ready. Show code snippets if needed."

So no model at read time. Each problem keeps a tips.json beside its README,
written ahead of time, and the page picks from it by what just happened:

  {
    "example": an input cell for the "Your inputs" box: setup lines, then the
               call on the last line. Must run against the reference solution.
    "start":   [tip, ...]  the approach, from least to most given away: an
               idea to reach for, then the technique and what it keeps true,
               then a skeleton with the key lines left as `...`
    "tests":   {"test_method": [tip, ...]}  what that test really checks, and
               the usual reason an answer fails it
    "errors":  {"ExceptionName": [tip, ...]}  errors typical of this problem
    "stopped": [tip, ...]  the loop that usually never ends here, and why
    "passing": tip  once everything passes: what to try next
  }

  tip = "text, `code` in backticks"  or  {"text": "...", "code": "python"}

validate() is what keeps them honest: an example that does not run, a key
naming a test that does not exist, or a snippet that would pass the tests on
its own is a tip that lies, and test_tips.py fails on each.
"""
from __future__ import annotations

import ast
import builtins
import json
import re
from pathlib import Path

KEYS = {"example", "start", "tests", "errors", "stopped", "passing"}
MAX_TIP = 520
# The page lists tests by name, sorted as unittest sorts them, not in the
# order the file defines them: "the second test" pointed at the wrong one in
# seven tips on 2026-09-26. Name the test as the page shows it, in quotes.
BY_POSITION = re.compile(r"\b(first|second|third|fourth|fifth|last|next|previous|other) test\b", re.I)


def load(problem_dir: Path) -> dict | None:
    f = Path(problem_dir) / "tips.json"
    return json.loads(f.read_text()) if f.is_file() else None


def _tips(value):
    return value if isinstance(value, list) else [value]


def _all_tips(t: dict):
    for k in ("start", "stopped"):
        yield from ((k, x) for x in t.get(k, []))
    for k in ("tests", "errors"):
        for name, lst in t.get(k, {}).items():
            yield from ((f"{k}.{name}", x) for x in lst)
    if "passing" in t:
        yield ("passing", t["passing"])


def test_names(tests_src: str) -> set[str]:
    return {n.name for n in ast.walk(ast.parse(tests_src))
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test")}


def validate(problem_dir: Path) -> list[str]:
    """Every way this problem's tips.json could mislead a reader. Empty is good."""
    import harness                    # here, not at the top: the site build only loads
    import starter                    # tips, and should not import the runner to do it
    d = Path(problem_dir)
    out = []
    try:
        t = load(d)
    except json.JSONDecodeError as e:
        return [f"not JSON: {e}"]
    if t is None:
        return ["no tips.json"]
    extra = set(t) - KEYS
    if extra:
        out.append(f"unknown keys {sorted(extra)}")
    tests_src = (d / "test_solution.py").read_text()
    solution = (d / "solution.py").read_text()
    start = starter.starter_for((d / "README.md").read_text())

    # the example runs, on the reference, as a reader's input would
    ex = t.get("example")
    if not isinstance(ex, str) or not ex.strip():
        out.append("example missing")
    else:
        r = harness.run(solution, tests_src, inputs=[ex], seconds=20)
        i = (r.get("inputs") or [{}])[0]
        if i.get("status") != "ok":
            out.append(f"example does not run on the reference: {i.get('failure') or r.get('status')}")

    if not (2 <= len(t.get("start", [])) <= 4):
        out.append("start needs 2 to 4 tips, from an idea to a skeleton")
    if not (1 <= len(t.get("stopped", [])) <= 3):
        out.append("stopped needs 1 to 3 tips")
    if "passing" not in t:
        out.append("passing missing")
    names = test_names(tests_src)
    for k in t.get("tests", {}):
        if k not in names:
            out.append(f"tests.{k}: no such test (have {sorted(names)})")
    for k in t.get("errors", {}):
        cls = getattr(builtins, k, None)
        if not (isinstance(cls, type) and issubclass(cls, BaseException)):
            out.append(f"errors.{k}: not a built-in exception name")

    # the reference's own lines must not be handed over in a tip
    given = set(start["code"].splitlines()) if start else set()
    answer_lines = {ln.strip() for ln in solution.splitlines()
                    if len(ln.strip()) >= 30 and ln not in given}
    for where, tip in _all_tips(t):
        text = tip.get("text", "") if isinstance(tip, dict) else tip
        code = tip.get("code", "") if isinstance(tip, dict) else ""
        if not isinstance(text, str) or not (15 <= len(text) <= MAX_TIP):
            out.append(f"{where}: text must be 15 to {MAX_TIP} characters")
        if BY_POSITION.search(text):
            out.append(f"{where}: counts tests by position; name the test as the page shows it")
        if isinstance(tip, dict) and set(tip) - {"text", "code"}:
            out.append(f"{where}: a tip is text and code, nothing else")
        both = text + "\n" + code
        for ln in sorted(answer_lines):
            if ln in both:
                out.append(f"{where}: gives away a reference line: {ln!r}")
        if code:
            try:
                ast.parse(code)
            except SyntaxError as e:
                out.append(f"{where}: snippet does not parse: {e.msg}")
                continue
            # A snippet, dropped in as the whole answer, must not pass.
            if start:
                r = harness.run(start["code"] + "\n\n" + code, tests_src, seconds=5)
                if r.get("tests") and all(x["status"] == "pass" for x in r["tests"]):
                    out.append(f"{where}: this snippet passes every test on its own")
    return out
