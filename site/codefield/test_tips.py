"""Every coding problem's tips.json, checked the way a reader would meet it.

    python3.12 -m pytest site/codefield/test_tips.py -q
    python3.12 -m pytest site/codefield/test_tips.py -q -k 15-linked

What tips.validate() refuses, and why each is a tip that lies: an example that
does not run on the reference, a key naming a test that does not exist, a line
of the reference answer handed over, a snippet that passes the tests on its
own, a first tip list too short to be progressive, a wall of text.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tips  # noqa: E402
from test_harness import CASES  # noqa: E402


@pytest.mark.parametrize("d", CASES, ids=lambda d: d.name)
def test_tips_are_honest(d):
    assert tips.validate(d) == []
