"""Test exact reviewed file changes on current main; never overwrite concurrent edits."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

payload_path = Path(sys.argv[1]).resolve()
out = payload_path.parent
payload = json.loads(payload_path.read_text())
root = Path.cwd().resolve()
clean_env = {k: v for k, v in os.environ.items() if k != 'GH_TOKEN'}


def run(args, *, env=clean_env, log=None):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env, timeout=600)
    if log:
        log.write_text(p.stdout)
    print(p.stdout, end='', flush=True)
    if p.returncode:
        raise RuntimeError(f'Command failed: {args[0]} (exit {p.returncode})')
    return p.stdout.strip()


def checked_path(name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('Unsafe delivery path')
    p = root / name
    if Path(name).parts[0] in {'.git', '.github', '.audit-delivery'} or p.is_symlink() or not p.resolve().is_relative_to(root):
        raise ValueError('Unsafe or protected delivery path')
    return p


run(['git', 'fetch', 'origin', 'main'])
current = run(['git', 'rev-parse', 'origin/main'])
concurrent = payload.get('allow_unrelated', False)
if concurrent:
    run(['git', 'merge-base', '--is-ancestor', payload['base'], current])
elif current != payload['base']:
    raise RuntimeError('main changed; refresh before retrying')
run(['git', 'checkout', '--detach', current])
run(['git', 'config', 'user.name', 'github-actions[bot]'])
run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'])
for number, command in enumerate(payload.get('prepare', []), 1):
    run(command, log=out / f'prepare-{number:02d}.log')
askpass = out / 'askpass.sh'
askpass.write_text('#!/bin/sh\ncase "$1" in *Username*) printf "%s" x-access-token;; *Password*) printf "%s" "$GH_TOKEN";; esac\n')
askpass.chmod(0o700)
receipts = []
for number, batch in enumerate(payload['batches'], 1):
    changed = []
    for edit in batch['edits']:
        path = checked_path(edit['path'])
        if concurrent:
            before = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if before != edit['before_sha256']:
                raise ValueError(f'Concurrent edit to reviewed file: {edit["path"]}')
        if 'generated' in edit:
            name = edit['generated']
            if not isinstance(name, str) or Path(name).name != name:
                raise ValueError('Generated input must be a basename')
            data = (out / 'generated' / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != edit['sha256']:
                raise ValueError('Generated input differs from reviewed bytes')
            edit = {**edit, 'content': data.decode('utf-8')}
        if 'content' in edit:
            if path.exists():
                raise ValueError(f'New file already exists: {edit["path"]}')
            path.parent.mkdir(parents=True, exist_ok=True)
            text = edit['content']
        else:
            text = path.read_text()
            for replacement in edit['replacements']:
                if 'offset' in replacement:
                    start, length = replacement['offset'], replacement['length']
                    old = text[start:start + length]
                    if start < 0 or length < 1 or hashlib.sha256(old.encode()).hexdigest() != replacement['sha256']:
                        raise ValueError(f'Edit range mismatch: {edit["path"]}')
                    text = text[:start] + replacement['new'] + text[start + length:]
                else:
                    old, new = replacement['old'], replacement['new']
                    if not old or text.count(old) != replacement.get('count', 1):
                        raise ValueError(f'Edit precondition mismatch: {edit["path"]}')
                    text = text.replace(old, new)
        if concurrent and hashlib.sha256(text.encode()).hexdigest() != edit['after_sha256']:
            raise ValueError(f'Output differs from reviewed bytes: {edit["path"]}')
        path.write_text(text)
        changed.append(edit['path'])
    run(['git', 'add', '--', *changed])
    run(['git', 'diff', '--cached', '--check'])
    tree = run(['git', 'write-tree'])
    if not concurrent and tree != batch['tree']:
        raise RuntimeError('Tree differs from locally checked tree')
    for name in changed:
        path = root / name
        if path.suffix == '.py':
            compile(path.read_text(), name, 'exec')
        if path.suffix == '.md':
            text = path.read_text()
            if text.count('```') % 2 or text.count('<details>') != text.count('</details>'):
                raise ValueError(f'Unbalanced Markdown: {name}')
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', re.sub(r'```.*?```', '', text, flags=re.S)):
                if not target.startswith(('http:', 'https:', 'mailto:', '#')) and not (path.parent / target.split('#')[0]).exists():
                    raise ValueError(f'Broken link: {name} -> {target}')
    for i, command in enumerate(batch.get('tests', []), 1):
        run(command, log=out / f'{number:02d}-test-{i:02d}.log')
    run(['git', 'diff', '--exit-code'])
    run(['git', 'commit', '-m', batch['message']])
    sha = run(['git', 'rev-parse', 'HEAD'])
    run(['git', 'push', 'origin', 'HEAD:refs/heads/main'], env={**clean_env,
        'GH_TOKEN': os.environ['GH_TOKEN'], 'GIT_ASKPASS': str(askpass), 'GIT_TERMINAL_PROMPT': '0'})
    receipt = {'chapter': batch['message'].splitlines()[0], 'sha': sha, 'tree': tree,
               'files': changed, 'commands': batch.get('tests', []), 'status': 'tested-and-pushed'}
    receipts.append(receipt)
    (out / 'receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print('DELIVERED ' + json.dumps(receipt), flush=True)
