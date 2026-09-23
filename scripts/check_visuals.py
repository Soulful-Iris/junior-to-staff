"""Inventory visual bytes and distinguish inspection from parse/render checks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def inventory(root, paths, reviewed):
    records = []
    seen = set()
    for name in sorted(paths):
        path = root / name
        if path.suffix == '.svg':
            data = path.read_bytes()
            element = ET.fromstring(data)
            if element.tag != '{http://www.w3.org/2000/svg}svg':
                raise ValueError(f'Not an SVG: {name}')
            digest = hashlib.sha256(data).hexdigest()
            review = reviewed.get(name)
            if review and review['sha256'] != digest:
                raise ValueError(f'Visual changed since inspection: {name}; reinspect or mark pending')
            seen.add(name)
            text = [e.text for e in element if e.tag.rsplit('}', 1)[-1] in {'title', 'desc'} and e.text]
            animated = any(e.tag.rsplit('}', 1)[-1] in {'animate', 'animateTransform', 'animateMotion'} for e in element.iter())
            records.append({'path': name, 'sha256': digest, 'kind': 'svg',
                'description': ' '.join(text) or element.get('aria-label', ''),
                'status': 'static-inspected' if review else 'semantic-review-pending',
                'review': review.get('review') if review else None,
                'motion_gate': 'playback-and-static-equivalence-pending' if animated else 'not-applicable'})
        elif path.suffix == '.md':
            for number, match in enumerate(re.finditer(r'```mermaid\s*\n(.*?)```', path.read_text(), re.S), 1):
                code = match[1].replace('\r\n', '\n').strip()
                records.append({'path': f'{name}#mermaid-{number}', 'kind': 'mermaid-source',
                    'sha256': hashlib.sha256(code.encode()).hexdigest(),
                    'contract_source': name, 'status': 'semantic-review-pending',
                    'render_gate': 'See commit-scoped reader content-inventory.json and render log'})
    if set(reviewed) - seen:
        raise ValueError('Inspection record references a missing visual')
    if not records:
        raise ValueError('No visual artifacts found')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    records = inventory(ROOT, [p for p in paths if p], json.loads((ROOT/'docs/visual-review.json').read_text()))
    report = {'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'owner': 'repository maintainers', 'artifacts': records,
              'limits': 'Parsing and byte identity do not prove semantic accuracy; pending status is explicit, not a passed review.'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(records)} visual artifacts inventoried; {len(json.loads((ROOT/"docs/visual-review.json").read_text()))} current static inspections.')
    print(report['limits'])


if __name__ == '__main__':
    main()
