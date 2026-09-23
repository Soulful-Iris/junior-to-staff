"""Check current learning catalogs against source paths, not historical totals."""
from pathlib import Path
import argparse
import hashlib
import subprocess
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def collect(root):
    root = root.resolve()
    chapters = sorted(root.glob('curriculum/*/*/README.md'))
    bank = json.loads((root/'indexes/problem-bank.json').read_text())
    paths = [item['path'] for item in bank]
    directories = [item['directory'] for item in bank]
    numbers = [item['number'] for item in bank]
    if any(len(set(items)) != len(items) for items in (paths, directories, numbers)):
        raise ValueError('Duplicate coding registry entry')
    for item in bank:
        path, directory = root/item['path'], root/item['directory']
        if (not path.resolve().is_relative_to(root) or path.parent != directory
                or not path.is_file() or not (directory/'solution.py').is_file()
                or not list(directory.glob('test_*.py'))):
            raise ValueError(f"Incomplete or unsafe coding bundle: {item['path']}")
    discovered = {p.relative_to(root).as_posix() for p in root.glob('curriculum/*/*/problems/*/README.md')}
    if set(paths) != discovered:
        raise ValueError('Coding registry has missing or orphan bundles')
    project_paths = sorted(p for p in root.glob('curriculum/**/projects/**/*.md') if p.name != 'README.md')
    project_paths += sorted(root.glob('projects/reading-list/stages/*/README.md'))
    projects = []
    for p in project_paths:
        path = p.relative_to(root).as_posix()
        kind = ('continuing-stage' if path.startswith('projects/reading-list/stages/') else
                'runnable-reference' if re.search(r'/03-ai-systems/projects/0[1-4]-', path) else 'build-assignment')
        projects.append({'path': path, 'kind': kind})
    excluded = {'README.md', 'foundations-index.md', 'advanced-index.md'}
    designs = sorted(p for p in root.glob('curriculum/*/*/problems/*.md') if p.name not in excluded)
    data = {'chapters': [p.relative_to(root).as_posix() for p in chapters], 'coding': paths,
            'projects': projects, 'designs': [p.relative_to(root).as_posix() for p in designs]}
    if any(not items for items in data.values()):
        raise ValueError('Empty learning inventory')
    return data


def check(root, data):
    errors = []
    targets = {
        'curriculum/README.md': {p.removeprefix('curriculum/') for p in data['chapters']},
        'indexes/coding.md': {'../'+p for p in data['coding']},
        'indexes/projects.md': {'../'+p['path'] for p in data['projects']},
        'indexes/system-designs.md': {'../'+p for p in data['designs']},
    }
    for name, expected in targets.items():
        text = (root/name).read_text()
        links = re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text)
        for target in sorted(expected):
            if links.count(target) != 1:
                errors.append(f'{name}: expected exactly one link to {target}; found {links.count(target)}')
        for link in links:
            if not link.startswith(('https://', 'http://', '#')):
                dest = (root/name).parent/link.split('#', 1)[0]
                if not dest.exists():
                    errors.append(f'{name}: missing target {link}')
    root_text = (root/'README.md').read_text()
    for chapter in data['chapters']:
        if f']({chapter})' not in root_text:
            errors.append(f'Root navigation missing chapter: {chapter}')
    expected_counts = (len(data['chapters']), len(data['coding']), len(data['projects']), len(data['designs']))
    recorded = re.search(r'(\d+) subject chapters.*?(\d+) coding bundles.*?(\d+) project entries.*?(\d+) design/architecture pages', root_text)
    if not recorded or tuple(map(int, recorded.groups())) != expected_counts:
        errors.append(f'Root inventory counts must match {expected_counts}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        data = collect(ROOT)
        errors = check(ROOT, data)
        if errors:
            print('\n'.join(errors)); return 1
        if args.report:
            paths = data['chapters'] + data['coding'] + data['designs'] + [p['path'] for p in data['projects']]
            report = {'counts': {k: len(v) for k, v in data.items()}, 'inventory': data,
                      'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                      'sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}}
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2)+'\n')
        print('; '.join(f'{len(v)} {k}' for k, v in data.items()) + '; exact catalogs agree')
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f'Catalog check failed: {exc}', file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
