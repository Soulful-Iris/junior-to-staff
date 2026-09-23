#!/usr/bin/env python3
"""Check historical membership; use --historical for the old equality experiment.

The --historical mode requires source git objects and the original reorganization checkout.
The default permits additions and reports changed hashes instead of claiming that
an old green result certifies later corrections. Current test gates remain separate.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def historical_main():
    manifest = json.loads((ROOT / 'docs/reorganization-map.json').read_text())
    source = manifest['source_commit']
    files = manifest['files']
    original = set(git('ls-tree', '-r', '--name-only', source).decode().splitlines())
    assert len(files) == len(original) == 477
    assert {f['source'] for f in files} == original, 'Incomplete source inventory'
    assert len(manifest['groups']) == 4 and len(manifest['chapters']) == 17
    path_helpers = {
        'paths/interviews/practice/assessor/heldback_importer.py',
        'scripts/check_curriculum.py', 'scripts/check_learning.py',
        'scripts/render_visuals.py',
    }
    old_diagrams, new_diagrams = Counter(), Counter()
    svg_count = unchanged_code = 0
    pattern = rb'```mermaid\s*\n(.*?)```'
    for f in files:
        before = git('show', f"{source}:{f['source']}")
        assert sha256(before).hexdigest() == f['source_sha256'], f['source']
        destination = ROOT / f['destination']
        assert destination.is_file(), f"Missing: {destination}"
        after = destination.read_bytes()
        if destination.suffix == '.md':
            old_diagrams.update(re.findall(pattern, before, re.S))
        elif f['source'] not in path_helpers:
            assert before == after, f"Unexpected artifact change: {destination}"
            if destination.suffix == '.svg':
                svg_count += 1
            else:
                unchanged_code += 1
    for p in ROOT.rglob('*.md'):
        if not {'.git', 'node_modules'} & set(p.parts):
            new_diagrams.update(re.findall(pattern, p.read_bytes(), re.S))
    assert old_diagrams == new_diagrams, 'Mermaid diagrams changed or lost'
    assert sum(old_diagrams.values()) == 387 and svg_count == 105
    problems = json.loads((ROOT / 'indexes/problem-bank.json').read_text())
    assert {p['number'] for p in problems} == set(range(1, 43))
    assert len({p['directory'] for p in problems}) == len(problems) == 42
    for p in problems:
        folder = ROOT / p['directory']
        assert (ROOT / p['path']).is_file()
        assert (folder / 'solution.py').is_file(), folder
        assert list(folder.glob('test_*.py')), folder
    briefs = [f for f in files if (
        '/projects/' in f['source'] and f['source'].endswith('.md')
        and f['source'].startswith(('acts/', 'tiers/'))
    ) or re.match(r'projects/p[1-5][^/]*/README.md$', f['source'])]
    assert len(briefs) == 45, f"Expected 45 briefs; found {len(briefs)}"
    assert len({f['destination'] for f in briefs}) == 45
    for old in ('paths', 'tiers', 'acts'):
        assert not list((ROOT / old).rglob('*.md')), f"Old navigation remains: {old}"
    print(f'PASS: 477 mapped files; 4 groups / 17 chapters; 42 problem bundles; 45 briefs; '
          f'105 unchanged SVGs; 387 unchanged Mermaid blocks; '
          f'{unchanged_code} other unchanged non-Markdown artifacts.')
    print('Scope: prose/link edits and four path-dependent helpers require review; this is not a new technical-content audit.')

def check_current(root, manifest):
    """Preservation of membership, not a claim of byte-identical content."""
    destinations = [item['destination'] for item in manifest['files']]
    counts = Counter(destinations)
    if any(counts[item['destination']] > 1 and item.get('kind') != 'navigation' for item in manifest['files']):
        raise ValueError('Only navigation pages may have a recorded merged destination')
    changed = []
    for item in manifest['files']:
        path = root/item['destination']
        if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"Missing historical artifact: {item['destination']}")
        digest = sha256(path.read_bytes()).hexdigest()
        if digest != item['source_sha256']:
            changed.append({'path': item['destination'], 'source_sha256': item['source_sha256'],
                            'current_sha256': digest})
    return {'baseline': manifest['source_commit'], 'preserved_destinations': len(set(destinations)), 'mapped_sources': len(destinations),
            'changed_since_baseline': changed,
            'scope': 'Membership only. Changed artifacts require current tests/review; additions are allowed.'}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical', action='store_true', help='Reproduce the original reorganization-only equality check')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.historical:
        return historical_main()
    result = check_current(ROOT, json.loads((ROOT/'docs/reorganization-map.json').read_text()))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2)+'\n')
    print(f"PASS membership: {result['preserved_destinations']} historical destinations present; "
          f"{len(result['changed_since_baseline'])} have changed bytes.")
    print(result['scope'])


if __name__ == '__main__':
    main()
