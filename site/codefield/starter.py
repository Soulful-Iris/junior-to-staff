"""The editor's opening code, derived from the page the reader is looking at.

The starter IS the page's "Write this:" block, so the code field can never
disagree with the question printed above it (that block is itself generated
from what the tests import, by scripts/problem_signatures.py). Two additions:

  * `from dataclasses import dataclass` when the block uses @dataclass. The
    printed block leaves it out for readability; a runnable file cannot.
  * the GIVEN ranges: that import, and every @dataclass class written out in
    full (no `...` in its body). Those are the problem's data, not the
    reader's answer, and the tests depend on their exact shape. A class the
    reader has to implement (Trie, TopK, ...) is written with `...` stubs and
    is never given.
"""
from __future__ import annotations

import ast
import re

_BLOCK = re.compile(r"\*\*Write this:\*\*\s*\n+```python\n(.*?)```", re.S)
_IMPORT = "from dataclasses import dataclass"


def write_this_block(readme_text: str) -> str | None:
    m = _BLOCK.search(readme_text)
    return m.group(1) if m else None


def starter_for(readme_text: str) -> dict | None:
    """{'code': str, 'given': [[first, last], ...]} (1-based, inclusive), or None."""
    block = write_this_block(readme_text)
    if block is None:
        return None
    code = block.rstrip() + "\n"
    given = []
    if "@dataclass" in code and _IMPORT not in code:
        code = f"{_IMPORT}\n\n{code}"
        given.append([1, 1])
    tree = ast.parse(code)
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        decorated = any(
            (isinstance(d, ast.Name) and d.id == "dataclass")
            or (isinstance(d, ast.Call) and getattr(d.func, "id", None) == "dataclass")
            for d in node.decorator_list)
        stubbed = any(isinstance(n, ast.Constant) and n.value is Ellipsis
                      for n in ast.walk(node))
        if decorated and not stubbed:
            first = min([node.lineno] + [d.lineno for d in node.decorator_list])
            given.append([first, node.end_lineno])
    return {"code": code, "given": given}
