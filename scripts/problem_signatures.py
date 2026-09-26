#!/usr/bin/env python3.12
"""Emit the public API of each coding problem, taken from the code its tests run.

Bruno, 2026-09-26, on a problem page: "Why not make the function name object
type input and the class of the object so one can see what it is."

He was right, and it was not one page. Across 38 problems, 37 never showed the
reader a function signature at all: the contract was written as English prose
in a two-column table, so you could read the whole page and still not know what
you were being asked to write.

The signature is derived rather than hand-written, and the source is
`test_solution.py`'s import line. That line names exactly the objects the tests
exercise, so the block on the page cannot drift away from the code that is
actually graded. A hand-copied signature would be correct on the day it was
written and unverifiable afterwards, which is the whole failure this repo keeps
finding in its own prose.
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBLEMS = ROOT / "curriculum/01-code/02-data-structures-algorithms/problems"


def public_names(problem: Path) -> list[str]:
    """The names the tests import. Definitive: these are what gets graded."""
    test = problem / "test_solution.py"
    if not test.is_file():
        return []
    tree = ast.parse(test.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "solution":
            return [a.name for a in node.names]
    return []


def render(problem: Path) -> str | None:
    """A python block showing each imported class and function, in import order."""
    src_path = problem / "solution.py"
    names = public_names(problem)
    if not names or not src_path.is_file():
        return None
    src = src_path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.splitlines()

    defined = {}
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            defined[node.name] = node

    out: list[str] = []
    for name in names:
        node = defined.get(name)
        if node is None:
            continue
        if isinstance(node, ast.ClassDef):
            # Fields yes, method signatures yes, method BODIES never. The first
            # version of this emitted whole classes, on the assumption they were
            # small data holders like Node. Five of the eleven exported classes
            # are the solution itself, so that version printed the answer at the
            # top of the question. Checked on a dataclass and two plain
            # functions, all of which passed, and never on the case that broke.
            start = min([d.lineno for d in node.decorator_list] + [node.lineno]) - 1
            head = "\n".join(lines[start:node.lineno]).rstrip()
            fields: list[str] = []
            methods: list[str] = []
            for item in node.body:
                if isinstance(item, (ast.AnnAssign, ast.Assign)):
                    fields.append("\n".join(
                        lines[item.lineno - 1:item.end_lineno]).rstrip())
                elif isinstance(item, ast.FunctionDef):
                    # Private helpers are the author's business, not the
                    # reader's. __init__ is part of how you construct it.
                    if item.name.startswith("_") and item.name != "__init__":
                        continue
                    end = item.body[0].lineno - 1 if item.body else item.lineno
                    methods.append("\n".join(
                        lines[item.lineno - 1:end]).rstrip() + "\n        ...")
            parts = ["\n".join(fields)] if fields else []
            parts += methods
            out.append(head + "\n" + ("\n\n".join(parts) if parts else "    ..."))
        else:
            # Signature only. The body is the answer and belongs behind the
            # solution toggle, not in the statement of the question.
            end = node.body[0].lineno - 1 if node.body else node.lineno
            sig = "\n".join(lines[node.lineno - 1:end]).rstrip()
            doc = ast.get_docstring(node)
            first = doc.strip().splitlines()[0] if doc else None
            out.append(f"{sig}\n    ...  # {first}" if first else f"{sig}\n    ...")
    if not out:
        return None
    return "```python\n" + "\n\n".join(out) + "\n```"


LABEL = "**Write this:**"


def insert(problem: Path) -> str:
    """Put the block straight after the brief, before any contract table.

    The anchor is the first blockquote rather than a heading: every problem has
    one, and only twenty of the thirty-eight use the same heading above it.
    """
    block = render(problem)
    readme = problem / "README.md"
    if block is None:
        return "no API"
    text = readme.read_text(encoding="utf-8")
    if LABEL in text:
        return "already present"

    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("> ")), None)
    if start is None:
        return "no blockquote"
    end = start
    while end + 1 < len(lines) and (lines[end + 1].startswith(">") or lines[end + 1].strip() == ">"):
        end += 1

    new = lines[:end + 1] + ["", LABEL, "", block] + lines[end + 1:]
    readme.write_text("\n".join(new) + "\n", encoding="utf-8")
    return "inserted"


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    targets = [Path(a) for a in args] or sorted(
        d for d in PROBLEMS.iterdir() if (d / "README.md").is_file())
    counts: dict[str, int] = {}
    for p in targets:
        if apply:
            status = insert(p)
            counts[status] = counts.get(status, 0) + 1
            print(f"{status:16} {p.name}")
        else:
            block = render(p)
            print(f"\n===== {p.name}")
            print(block if block else "  !! no public API found")
    if apply:
        print(f"\n{len(targets)} problems: " +
              ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
