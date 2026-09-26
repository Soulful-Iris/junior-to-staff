"""Run a reader's solution against a problem's own unittest file, with limits.

This file runs inside Pyodide, in a Web Worker on the reader's machine, and
under plain CPython in test_harness.py. Standard library only.

Every limit is enforced HERE, in Python, and not in the page:

  time    sys.monitoring JUMP and PY_START events on the reader's code objects
          only. Every 1024th loop turn or call checks the clock and raises
          TimeLimit into the reader's own frame, so the stop carries a real
          traceback: which loop, which lines. The worker's terminate() in the
          page is only the backstop for what this cannot see, such as one C
          call that never returns.
  output  sys.stdout and sys.stderr count bytes. Past the cap the write raises
          OutputLimit, so the page never receives more than the cap.
  stops   a breakpoint is a LINE event. Every line that is not a breakpoint
          returns DISABLE on its first pass and never calls back again, so
          armed breakpoints cost almost nothing (measured 2026-09-26: 11.3 ms
          plain, 11.7 ms armed, 200,000-node list). Recording stops at
          max_stops.

Both limits are BaseException subclasses: `except Exception` in the reader's
code cannot swallow them. Values are shown through bounded_repr, which never
calls the reader's own __repr__ and never recurses without a limit, because a
linked list can be ten thousand nodes long or loop forever, and printing one
is the same runaway as printing in a loop.

Time and memory are measured only while the reader's code runs (Bruno: "It
should only start measuring when the function actually runs"):

  tests   "time in your code": the same monitoring counts entries into and
          exits from the reader's own code objects, and the clock runs only
          while at least one of their frames is live. The 10,000-node list a
          test builds before calling the reader is not charged to the reader.
  inputs  the reader's own cells: setup lines, then a final call. The call's
          arguments are built first and the clock covers the call alone. Its
          memory is tracemalloc's peak during a second call on freshly built
          arguments, so tracing cannot slow the timed call.

Every run starts from the same Python: a fresh module, and afterwards
anything the reader's code added to sys.modules, builtins or sys.path is
removed, and the recursion limit, the collector, trace hooks and random's
state are put back.
"""
from __future__ import annotations

import ast
import builtins
import gc
import io
import random
import reprlib
import sys
import textwrap
import time
import traceback
import types
import unittest
import unittest.case
import unittest.util

SOLUTION = "solution.py"
TESTS = "test_solution.py"


class TimeLimit(BaseException):
    """Raised into the reader's code when the run is out of time."""


class OutputLimit(BaseException):
    """Raised from print() when the run has written its output allowance."""


# --------------------------------------------------------------- showing values
class _Bounded(reprlib.Repr):
    def __init__(self):
        super().__init__()
        self.maxlevel = 3
        self.maxstring = 60
        self.maxlong = 40
        self.maxother = 60
        self.maxlist = self.maxtuple = self.maxset = self.maxfrozenset = 8
        self.maxdict = 6
        self.maxdeque = 8

    def repr1(self, x, level):
        mod = getattr(type(x), "__module__", "")
        if mod in ("solution", "test_solution") and hasattr(x, "__dict__") \
                and not isinstance(x, type):
            return self._instance(x, level)
        try:
            return super().repr1(x, level)
        except Exception:
            return f"<{type(x).__name__}>"

    def _instance(self, x, level):
        # Never the reader's own __repr__: it could loop forever or recurse
        # through ten thousand nodes. Fields, depth-limited, and a short id tag
        # so two nodes holding the same value are still told apart.
        name = type(x).__name__
        tag = f"@{id(x) & 0xFFFF:04x}"
        if level <= 0:
            return f"{name}(…){tag}"
        fields = []
        for k, v in list(vars(x).items())[:4]:
            fields.append(f"{k}={self.repr1(v, level - 1)}")
        more = ", …" if len(vars(x)) > 4 else ""
        return f"{name}({', '.join(fields)}{more}){tag}"


_BOUNDED = _Bounded()


def bounded_repr(value, limit: int = 160) -> str:
    try:
        s = _BOUNDED.repr(value)
    except Exception:
        s = f"<{type(value).__name__}>"
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _safe_repr(obj, short=False):
    return bounded_repr(obj, 80 if short else 160)


# ------------------------------------------------------------ source locations
def _loop_around(tree, line: int):
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While, ast.AsyncFor)) \
                and node.lineno <= line <= (node.end_lineno or node.lineno):
            if best is None or node.lineno >= best.lineno:
                best = node
    return [best.lineno, best.end_lineno] if best else None


def _function_around(tree, line: int):
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.lineno <= line <= (node.end_lineno or node.lineno):
            if best is None or node.lineno >= best.lineno:
                best = node
    return best.name if best else None


def _code_objects(co):
    yield co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from _code_objects(c)


# ------------------------------------------------ frees that cannot run away
# CPython frees a linked list recursively, one native frame per node. In a
# browser worker those frames sit on the engine's own stack, which is far
# smaller than CPython assumes. Measured 2026-09-26 in Chromium: dropping a
# 1,000-node chain is fine, 3,000 overflows, and after the overflow that Python
# instance is broken for good. Seven of the guide's problems build 2,000 to
# 10,000 deep structures on purpose, to prove a solution is iterative, and one
# of them frees its trie as a temporary in the middle of an assertion, so
# nothing that waits for a test to finish can catch it.
#
# So the reader's classes get a finalizer that hands each dying object's
# attributes to a queue instead of letting them be freed inside its own free.
# One outer loop drains the queue. Every free is then one level deep, wherever
# it happens.
_GRAVE = []
_DRAINING = [False]


def _finalize(self):
    try:
        d = self.__dict__
        if d:
            _GRAVE.append(tuple(d.values()))
            d.clear()
        if _DRAINING[0]:
            return
        _DRAINING[0] = True
        try:
            while _GRAVE:
                _GRAVE.pop()
        finally:
            _DRAINING[0] = False
    except BaseException:
        pass                   # a finalizer must never raise into the reader's run


def _dataclass_repr(self, level=6):
    """A dataclass's own repr, depth-limited: print(head) on a 10,000-node list
    must print something, not take Python down."""
    cls = type(self)
    if level <= 0:
        return f"{cls.__name__}(…)"
    parts = []
    for name, f in cls.__dataclass_fields__.items():
        if not f.repr:
            continue
        v = getattr(self, name, None)
        if hasattr(type(v), "__dataclass_fields__") and type(v).__repr__ is _dataclass_repr:
            parts.append(f"{name}={_dataclass_repr(v, level - 1)}")
        else:
            parts.append(f"{name}={bounded_repr(v, 200)}")
    out = f"{cls.__name__}({', '.join(parts)})"
    return out if len(out) <= 2000 else out[:1999] + "…"


def make_frees_iterative(module) -> list:
    """Install the finalizer (and the bounded dataclass repr) on every class the
    module defines. Returns the names changed, for the tests."""
    changed = []
    for obj in list(vars(module).values()):
        if not isinstance(obj, type) or obj.__module__ != module.__name__:
            continue
        try:
            if "__del__" not in vars(obj):
                obj.__del__ = _finalize
                changed.append(obj.__name__)
            params = getattr(obj, "__dataclass_params__", None)
            generated = getattr(getattr(vars(obj).get("__repr__"), "__code__", None),
                                "co_filename", SOLUTION) not in (SOLUTION, TESTS)
            if params is not None and params.repr and generated:
                obj.__repr__ = _dataclass_repr      # never a repr the reader wrote
        except (TypeError, AttributeError):
            pass
    return changed


def humanise(method_name: str) -> str:
    words = method_name.removeprefix("test_").replace("_", " ").strip()
    return (words[:1].upper() + words[1:]) or method_name


# ---------------------------------------------------------------------- output
class _Stream(io.TextIOBase):
    def __init__(self, run):
        self._run = run

    def writable(self):
        return True

    def write(self, s):
        return self._run.emit(s)

    def flush(self):
        pass


# ------------------------------------------------------------------- the run
class _Run:
    def __init__(self, code, tests, breakpoints, seconds, max_bytes, max_stops, inputs=()):
        self.inputs = [str(x) for x in (inputs or ()) if str(x).strip()][:5]
        self.code_src = code
        self.test_src = tests
        self.code_lines = code.splitlines()
        self.test_lines = tests.splitlines()
        self.breakpoints = {int(b) for b in (breakpoints or ())}
        self.seconds = float(seconds)
        self.max_bytes = int(max_bytes)
        self.max_stops = int(max_stops)
        self.used_bytes = 0
        self.records = []          # one per test, in order
        self.current = None        # the record being written to
        self.stops = []
        self.stops_truncated = False
        self.stopped = None
        self.deadline = None
        self.tree = None
        self.user_codes = set()
        self.tool = None
        self.inside = [0, 0.0, 0.0]    # live reader frames, clock at first entry, total seconds
        self.quiet = False             # the second, traced call of an input prints nowhere
        self.memory_spent = 0.0        # seconds its memory passes took, given back to the reader

    # -- output -------------------------------------------------------------
    def emit(self, s: str) -> int:
        if not isinstance(s, str):
            s = str(s)
        if self.quiet:
            return len(s)
        data = s.encode("utf-8", "replace")
        room = self.max_bytes - self.used_bytes
        target = self.current["output"] if self.current is not None else self.import_output
        if len(data) > room:
            target.append(data[:max(room, 0)].decode("utf-8", "ignore"))
            # End on a whole line where there is one: a stray "w" as the last
            # line of the log reads as something the reader printed. Across
            # everything written, because print() writes its parts separately
            # and the chunk that crosses the cap rarely holds the newline.
            text = "".join(target)
            if "\n" in text:
                target[:] = [text[: text.rindex("\n") + 1]]
            self.used_bytes = self.max_bytes
            if self.current is not None:
                self.current["output_cut"] = True
            raise OutputLimit()
        self.used_bytes += len(data)
        target.append(s)
        return len(s)

    # -- monitoring ---------------------------------------------------------
    def _arm(self, code_obj):
        M = sys.monitoring
        tool = next((t for t in (M.DEBUGGER_ID, 3, 4, M.PROFILER_ID, M.COVERAGE_ID)
                     if M.get_tool(t) is None), None)
        if tool is None:
            return
        M.use_tool_id(tool, "j2s-codefield")
        self.tool = tool
        counter = [0]
        deadline_check = self._deadline_check
        inside = self.inside
        clock = time.perf_counter
        user_codes = self.user_codes

        def on_jump(co, src, dst):
            counter[0] += 1
            if counter[0] & 1023 == 0:
                deadline_check()

        def on_start(co, offset, *_):
            # A frame of the reader's code starts or resumes. The clock runs
            # from the first one until the last one is gone.
            if inside[0] == 0:
                inside[1] = clock()
            inside[0] += 1
            counter[0] += 1
            if counter[0] & 1023 == 0:
                deadline_check()

        def on_leave(co, offset, *_):
            if inside[0] > 0:
                inside[0] -= 1
                if inside[0] == 0:
                    inside[2] += clock() - inside[1]

        def on_unwind(co, offset, exc):
            # PY_UNWIND and PY_THROW cannot be set per code object, so these
            # arrive for every function; only the reader's count.
            if co in user_codes:
                on_leave(co, offset)

        def on_throw(co, offset, exc):
            if co in user_codes:
                on_start(co, offset)

        stops = self.stops
        bps = self.breakpoints
        run = self
        DISABLE = M.DISABLE

        def on_line(co, line):
            if line not in bps:
                return DISABLE
            if len(stops) >= run.max_stops:
                run.stops_truncated = True
                return DISABLE
            frame = sys._getframe(1)
            stops.append({"test": run.current["index"] if run.current else None,
                          "input": bool(run.current and run.current.get("kind") == "input"),
                          "line": line, "vars": run._locals(frame)})
            return None

        E = M.events
        M.register_callback(tool, E.JUMP, on_jump)
        for ev in (E.PY_START, E.PY_RESUME):
            M.register_callback(tool, ev, on_start)
        for ev in (E.PY_RETURN, E.PY_YIELD):
            M.register_callback(tool, ev, on_leave)
        M.register_callback(tool, E.PY_UNWIND, on_unwind)
        M.register_callback(tool, E.PY_THROW, on_throw)
        events = E.JUMP | E.PY_START | E.PY_RESUME | E.PY_RETURN | E.PY_YIELD
        if bps:
            M.register_callback(tool, E.LINE, on_line)
            events |= E.LINE
        for co in _code_objects(code_obj):
            self.user_codes.add(co)
            M.set_local_events(tool, co, events)
        M.set_events(tool, E.PY_UNWIND | E.PY_THROW)

    def _disarm(self):
        if self.tool is None:
            return
        M = sys.monitoring
        E = M.events
        M.set_events(self.tool, 0)
        for co in self.user_codes:
            try:
                M.set_local_events(self.tool, co, 0)
            except Exception:
                pass
        for ev in (E.JUMP, E.PY_START, E.PY_RESUME, E.PY_RETURN, E.PY_YIELD,
                   E.PY_UNWIND, E.PY_THROW, E.LINE):
            M.register_callback(self.tool, ev, None)
        M.free_tool_id(self.tool)
        self.tool = None

    def in_code_seconds(self, reset=False) -> float:
        """Seconds spent inside the reader's code since the last reset,
        including a frame still live when a limit stopped the run."""
        d, since, total = self.inside
        if d > 0:
            total += time.perf_counter() - since
        if reset:
            self.inside[:] = [0, 0.0, 0.0]
        return total

    @staticmethod
    def _snapshot():
        return {"modules": set(sys.modules), "builtins": dict(vars(builtins)),
                "path": list(sys.path), "limit": sys.getrecursionlimit(),
                "gc": gc.isenabled(), "trace": sys.gettrace(), "profile": sys.getprofile(),
                "random": random.getstate(), "stdin": sys.stdin}

    def _clean_up(self, before):
        """Each run starts from the same Python: anything the reader's code put
        into sys.modules, builtins or sys.path is taken out again, the process
        settings it could have changed are put back, and the garbage is
        collected. Standard-library modules it imported stay loaded; they hold
        no reader data and re-importing some C modules is unsafe."""
        for name in set(sys.modules) - before["modules"]:
            if not _stdlib_module(sys.modules[name]):
                sys.modules.pop(name, None)
        b = vars(builtins)
        for name in set(b) - set(before["builtins"]):
            b.pop(name, None)
        for name, value in before["builtins"].items():
            if b.get(name) is not value:
                b[name] = value
        sys.path[:] = before["path"]
        # A raised limit carries into the next run and, in a browser worker,
        # lets recursion reach the engine's own stack before Python notices.
        sys.setrecursionlimit(before["limit"])
        (gc.enable if before["gc"] else gc.disable)()
        sys.settrace(before["trace"])
        sys.setprofile(before["profile"])
        random.setstate(before["random"])
        sys.stdin = before["stdin"]
        gc.collect()

    def _deadline_check(self):
        if time.monotonic() > self.deadline:
            raise TimeLimit()

    def _locals(self, frame):
        out = {}
        module_scope = frame.f_code.co_name == "<module>"
        for k, v in frame.f_locals.items():
            if k.startswith("__"):
                continue
            if module_scope and (callable(v) or isinstance(v, types.ModuleType)):
                continue
            out[k] = bounded_repr(v, 100)
            if len(out) >= 30:
                break
        return out

    # -- describing what happened --------------------------------------------
    def _where(self, tb):
        frames = traceback.extract_tb(tb)
        user = [f for f in frames if f.filename == SOLUTION]
        check = next((f for f in reversed(frames) if f.filename == TESTS), None)
        return user, check

    def describe_failure(self, err, input_name=None):
        etype, value, tb = err
        user, check = self._where(tb)
        message = str(value)
        if etype is ImportError and "cannot import name" in message:
            missing = message.split("'")[1] if "'" in message else "it"
            message = f"The tests import {missing} from your code, and it is not defined."
        out = {"type": etype.__name__, "message": message[:2000],
               "user_lines": [f.lineno for f in user][-6:],
               "line": user[-1].lineno if user else None}
        if input_name is not None:
            cell = [f for f in traceback.extract_tb(tb) if f.filename == input_name]
            out["input_line"] = cell[-1].lineno if cell else None
        if check is not None and 1 <= check.lineno <= len(self.test_lines):
            out["check"] = {"line": check.lineno,
                            "source": self.test_lines[check.lineno - 1].strip()}
        return out

    def describe_stop(self, err):
        etype, value, tb = err
        user, _ = self._where(tb)
        line = user[-1].lineno if user else None
        loop = None
        # Name the loop the reader is going round, not the helper it happened
        # to be inside when the clock fired: from the innermost frame outward,
        # the first one that sits in a loop. (Found on the live page: a
        # reference-style solution with a _next() helper reported "still
        # inside _next, on line 8", which is true and points at the wrong code.)
        if self.tree is not None:
            for f in reversed(user):
                found = _loop_around(self.tree, f.lineno)
                if found:
                    loop, line = found, f.lineno
                    break
        stop = {"kind": "time" if etype is TimeLimit else "output",
                "test": self.current["index"] if self.current else None,
                "input": bool(self.current and self.current.get("kind") == "input"),
                "line": line, "loop": loop, "function": None,
                "seconds": round(time.monotonic() - self.started, 2),
                "bytes": self.used_bytes}
        if line is not None and self.tree is not None:
            stop["function"] = _function_around(self.tree, line)
        return stop

    # -- the whole thing ------------------------------------------------------
    def _run_inputs(self, module):
        """The reader's own inputs. Each is a small cell: setup lines, then the
        call to run on its last line, like

            a, b = Node("a"), Node("b")
            a.next, b.next = b, a
            cycle_entry(a)

        Time and memory are measured around that last CALL only, after its
        arguments are built, because building a 10,000-node list to pass in is
        not the function's work ("It should only start measuring when the
        function actually runs"). Memory is tracemalloc's peak during a second
        call on freshly built arguments, so the traced run cannot slow the
        timed one. Each cell gets its own namespace: the solution's names, and
        nothing from another cell.
        """
        records = [{"kind": "input", "index": i, "source": src, "status": "not-run",
                    "output": [], "output_cut": False} for i, src in enumerate(self.inputs)]
        for rec in records:
            if self.stopped:
                break
            self.current = rec
            rec["status"] = "running"
            name = f"<input {rec['index'] + 1}>"
            try:
                tree = ast.parse(textwrap.dedent(rec["source"]).strip(), name, mode="exec")
            except SyntaxError as e:
                rec["status"] = "error"
                rec["failure"] = {"type": "SyntaxError", "message": e.msg, "line": None,
                                  "input_line": e.lineno}
                continue
            if not tree.body or not isinstance(tree.body[-1], ast.Expr):
                rec["status"] = "error"
                rec["failure"] = {"type": "No call to run", "line": None,
                                  "message": "The last line of an input is the call to run, "
                                             "and this one ends with something else.",
                                  "input_line": tree.body[-1].lineno if tree.body else None}
                continue
            setup = compile(ast.Module(body=tree.body[:-1], type_ignores=[]), name, "exec")
            self._watch(setup)
            final = tree.body[-1].value
            simple = isinstance(final, ast.Call) and not any(
                isinstance(a, ast.Starred) for a in final.args) and all(k.arg for k in final.keywords)
            if isinstance(final, ast.Call):          # what the page calls the thing it timed
                f = final.func
                rec["call"] = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None

            def prepare():
                """A fresh namespace with the setup run in it, and the thing to
                measure as a no-argument callable whose arguments already exist."""
                ns = dict(vars(module))
                exec(setup, ns)

                def ev(node):
                    code = compile(ast.Expression(node), name, "eval")
                    self._watch(code)
                    return eval(code, ns)
                if simple:
                    fn, args = ev(final.func), [ev(a) for a in final.args]
                    kw = {k.arg: ev(k.value) for k in final.keywords}
                    return lambda: fn(*args, **kw)
                code = compile(ast.Expression(final), name, "eval")
                self._watch(code)
                return lambda: eval(code, ns)

            try:
                go = prepare()
                t0 = time.perf_counter()
                value = go()
                rec["seconds"] = time.perf_counter() - t0
                rec["value"] = bounded_repr(value, 400)
                rec["type"] = type(value).__name__
                rec["status"] = "ok"
                rec["peak_bytes"] = self._measure_memory(prepare, rec["seconds"])
            except (TimeLimit, OutputLimit):
                self.stopped = self.describe_stop(sys.exc_info())
                rec["status"] = "stopped"
            except BaseException:
                rec["status"] = "error"
                rec["failure"] = self.describe_failure(sys.exc_info(), input_name=name)
        self.current = None
        for rec in records:
            rec["output"] = "".join(rec["output"])
        return records

    # Seconds per run for every input's memory pass together. NOT the reader's:
    # whatever a pass takes is given back to their 3 seconds afterwards.
    MEMORY_BUDGET = 1.5

    def _measure_memory(self, prepare, seconds):
        """Peak bytes the call held, from a second, traced call on freshly
        built arguments, or None when that cannot be had in time.

        Tracing makes allocation-heavy code 12 to 15 times slower (measured on
        2026-09-26 by the tips writers: coin change on 100,000 took 0.16 s
        plain and 2.7 s in all, and edit distance on two 600-letter words, on
        the REFERENCE answer, had the whole run stopped before any test ran).
        So this pass has its own small allowance instead of the reader's, and
        running out of it ends in "not measured", never in the reader's run
        being stopped for a number they did not ask to wait for.
        """
        allowance = min(self.MEMORY_BUDGET - self.memory_spent, 1.0)
        if allowance < 0.05 or 15 * seconds > allowance:
            return None
        try:
            import tracemalloc
        except ImportError:
            return None
        saved, t0, started = self.deadline, time.monotonic(), False
        self.deadline = t0 + allowance
        self.quiet = True
        try:
            go = prepare()                # the arguments exist before tracing starts
            started = not tracemalloc.is_tracing()
            if started:
                tracemalloc.start()
            tracemalloc.reset_peak()
            base = tracemalloc.get_traced_memory()[0]
            go()
            return max(0, tracemalloc.get_traced_memory()[1] - base)
        except BaseException:             # out of allowance, or it failed the second time
            return None
        finally:
            if started:
                tracemalloc.stop()
            used = time.monotonic() - t0
            self.memory_spent += used
            self.deadline = saved + used
            self.quiet = False

    def _watch(self, code):
        """Put the time check on code the reader typed into an input: a setup
        loop that never ends must be stopped like one in the solution. Loop
        turns only, and no breakpoints: those are solution line numbers."""
        if self.tool is None:
            return
        M = sys.monitoring
        for co in _code_objects(code):
            try:
                M.set_local_events(self.tool, co, M.events.JUMP)
            except ValueError:
                pass

    def go(self) -> dict:
        self.import_output = []
        result = {"python": sys.version.split()[0], "status": "ok", "tests": [],
                  "stops": self.stops, "stopped": None, "output_bytes": 0,
                  "max_bytes": self.max_bytes, "seconds": self.seconds}
        try:
            self.tree = ast.parse(self.code_src, SOLUTION)
            code_obj = compile(self.tree, SOLUTION, "exec")
        except SyntaxError as e:
            result["status"] = "syntax"
            result["error"] = {"type": "SyntaxError", "message": e.msg,
                               "line": e.lineno, "column": e.offset}
            return result

        clean = self._snapshot()
        saved = (sys.stdout, sys.stderr, sys.modules.get("solution"),
                 sys.modules.get("test_solution"), unittest.case.safe_repr,
                 unittest.util.safe_repr)
        stream = _Stream(self)
        sys.stdout = sys.stderr = stream
        # input() reads an empty line's end at once instead of waiting on a
        # keyboard nobody can type into.
        sys.stdin = io.StringIO("")
        unittest.case.safe_repr = unittest.util.safe_repr = _safe_repr
        self.started = time.monotonic()
        self.deadline = self.started + self.seconds
        try:
            module = types.ModuleType("solution")
            module.__file__ = SOLUTION
            sys.modules["solution"] = module
            self._arm(code_obj)
            try:
                exec(code_obj, module.__dict__)
                make_frees_iterative(module)
            except (TimeLimit, OutputLimit):
                self.stopped = self.describe_stop(sys.exc_info())
                result["status"] = "stopped"
            except BaseException:
                result["status"] = "import-error"
                result["error"] = self.describe_failure(sys.exc_info())
            if result["status"] != "ok":
                return result

            try:
                tmod = types.ModuleType("test_solution")
                tmod.__file__ = TESTS
                sys.modules["test_solution"] = tmod
                exec(compile(self.test_src, TESTS, "exec"), tmod.__dict__)
                make_frees_iterative(tmod)
            except (TimeLimit, OutputLimit):
                self.stopped = self.describe_stop(sys.exc_info())
                result["status"] = "stopped"
                return result
            except BaseException:
                result["status"] = "import-error"
                result["error"] = self.describe_failure(sys.exc_info())
                return result

            result["inputs"] = self._run_inputs(module)
            if self.stopped:
                result["status"] = "stopped"
                return result
            suite = unittest.defaultTestLoader.loadTestsFromModule(tmod)
            cases = list(_flatten(suite))
            classes = {type(c).__name__ for c in cases}
            for i, case in enumerate(cases):
                method = case._testMethodName
                name = humanise(method)
                if len(classes) > 1:
                    name = f"{type(case).__name__}: {name}"
                self.records.append({"index": i, "id": method, "name": name,
                                     "status": "not-run", "ms": None,
                                     "output": [], "output_cut": False})
            res = _Result(self)
            for case in cases:
                if res.shouldStop:
                    break
                case(res)
            if self.stopped:
                result["status"] = "stopped"
            return result
        finally:
            self._disarm()
            sys.stdout, sys.stderr = saved[0], saved[1]
            for name, mod in (("solution", saved[2]), ("test_solution", saved[3])):
                if mod is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = mod
            unittest.case.safe_repr, unittest.util.safe_repr = saved[4], saved[5]
            self._clean_up(clean)
            result["stopped"] = self.stopped
            result["stops_truncated"] = self.stops_truncated
            result["output_bytes"] = self.used_bytes
            result["import_output"] = "".join(self.import_output)
            result["elapsed_ms"] = round((time.monotonic() - self.started) * 1000, 1) \
                if hasattr(self, "started") else 0
            for r in self.records:
                r["output"] = "".join(r["output"])
            result["tests"] = self.records


def _stdlib_dirs():
    import sysconfig
    paths = sysconfig.get_paths()
    return tuple({paths["stdlib"], paths["platstdlib"]})


def _stdlib_module(mod) -> bool:
    """Built in, frozen, or a file in the standard library's own directory.
    (Not sys.prefix: in Pyodide that can be "/", which is every file.)"""
    f = getattr(mod, "__file__", None)
    if f:
        return f.startswith(_stdlib_dirs())
    spec = getattr(mod, "__spec__", None)
    return spec is not None and getattr(spec, "origin", None) in ("built-in", "frozen")


def _flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


class _Result(unittest.TestResult):
    def __init__(self, run: _Run):
        super().__init__()
        self.run = run

    def _rec(self, test):
        return next(r for r in self.run.records if r["id"] == test._testMethodName
                    and r["status"] in ("not-run", "running"))

    def startTest(self, test):
        super().startTest(test)
        rec = self._rec(test)
        rec["status"] = "running"
        self.run.in_code_seconds(reset=True)
        rec["_t"] = time.perf_counter()
        self.run.current = rec

    def stopTest(self, test):
        super().stopTest(test)
        rec = self.run.current
        if rec is not None:
            rec["ms"] = round((time.perf_counter() - rec.pop("_t")) * 1000, 2)
            rec["code_ms"] = round(self.run.in_code_seconds() * 1000, 3)
            if rec["status"] == "running":
                rec["status"] = "pass"
        self.run.current = None

    def _limit(self, err):
        if err[0] in (TimeLimit, OutputLimit):
            self.run.stopped = self.run.describe_stop(err)
            self.run.current["status"] = "stopped"
            self.stop()
            return True
        return False

    def addSuccess(self, test):
        super().addSuccess(test)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if not self._limit(err):
            self.run.current["status"] = "fail"
            self.run.current.setdefault("failure", self.run.describe_failure(err))

    def addError(self, test, err):
        super().addError(test, err)
        if not self._limit(err):
            self.run.current["status"] = "error"
            self.run.current.setdefault("failure", self.run.describe_failure(err))

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None or self._limit(err):
            return
        rec = self.run.current
        rec["status"] = "fail" if issubclass(err[0], test.failureException) else "error"
        if "failure" not in rec:
            desc = self.run.describe_failure(err)
            desc["subtest"] = {k: bounded_repr(v, 80) for k, v in subtest.params.items()}
            rec["failure"] = desc

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.run.current["status"] = "skip"
        self.run.current["skip_reason"] = reason

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.run.current["status"] = "fail"


def run(code: str, tests: str, breakpoints=(), seconds: float = 3.0,
        max_bytes: int = 65536, max_stops: int = 200, inputs=()) -> dict:
    """Run `tests` against `code`. Returns a JSON-ready dict. Never raises."""
    try:
        return _Run(code, tests, breakpoints, seconds, max_bytes, max_stops, inputs).go()
    except BaseException as e:            # a bug in the harness, never the reader's
        return {"python": sys.version.split()[0], "status": "harness-error",
                "error": {"type": type(e).__name__, "message": str(e)[:500]},
                "tests": [], "stops": [], "stopped": None}


def run_json(payload: str) -> str:
    """The worker's entry point: one JSON string in, one JSON string out, so no
    value ever has to be converted between JavaScript and Python objects."""
    import json
    try:
        p = json.loads(payload)
        r = run(p["code"], p["tests"], p.get("breakpoints", ()), p.get("seconds", 3.0),
                p.get("max_bytes", 65536), p.get("max_stops", 200), p.get("inputs", ()))
    except BaseException as e:
        r = {"status": "harness-error", "error": {"type": type(e).__name__,
             "message": str(e)[:500]}, "tests": [], "stops": [], "stopped": None}
    return json.dumps(r)
