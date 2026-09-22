"""Structural provenance/local-link checks only; not a truth or freshness oracle."""
from pathlib import Path
import re

BASE=Path(__file__).resolve().parent
ledger=(BASE/'claim-ledger.md').read_text()
for expected in ('Publication','event','Sample','primary','2025-09-22','2026-03-22','2026-09-22'):
    assert expected in ledger, expected
for n in range(1,14):
    assert f'C{n:02}:' in ledger, n
checked=0
for path in BASE.glob('*.md'):
    text=path.read_text()
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if re.match(r'https?://',target) or target.startswith('#'):
            continue
        assert (path.parent/target.split('#')[0]).exists(), (path,target)
        checked+=1
print(f'13 claim IDs and {checked} local links checked; remote support/date quality requires human/source review.')
