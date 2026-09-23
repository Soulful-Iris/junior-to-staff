"""Temporary transport for reviewed patches; commits to main only after tests.

This file lives only on the temporary transport branch, never in the curriculum.
The caller supplies an exact base commit and a list of locally reviewed patches.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--batch', type=Path, required=True)
parser.add_argument('--evidence', type=Path, required=True)
parser.add_argument('--no-push', action='store_true')
args = parser.parse_args()
root = args.root.resolve()
data = json.loads(args.batch.read_text())
evidence = args.evidence.resolve()
evidence.mkdir(parents=True, exist_ok=True)
results = []

def git(*command, capture=False, **kwargs):
    return subprocess.run(['git', *command], cwd=root, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None, **kwargs)

if git('rev-parse', 'HEAD', capture=True).stdout.strip() != data['base']:
    raise SystemExit('Main moved since review; refusing to apply the batch')
if git('status', '--porcelain', capture=True).stdout.strip():
    raise SystemExit('Checkout is dirty; refusing to apply the batch')
git('config', 'user.name', 'github-actions[bot]')
git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
safe_env = {key: os.environ[key] for key in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR', 'CI') if key in os.environ}
safe_env.update(PYTHONDONTWRITEBYTECODE='1', AWS_EC2_METADATA_DISABLED='true')

def push(*refspec):
    if args.no_push:
        return
    token = os.environ['GH_TOKEN']
    credential = base64.b64encode(('x-access-token:' + token).encode()).decode()
    env = {**os.environ, 'GIT_CONFIG_COUNT': '1',
           'GIT_CONFIG_KEY_0': 'http.https://github.com/.extraheader',
           'GIT_CONFIG_VALUE_0': 'AUTHORIZATION: basic ' + credential}
    subprocess.run(['git', 'push', 'origin', *refspec], cwd=root, env=env, check=True)

try:
    for number, group in enumerate(data['groups'], 1):
        paths = group['paths']
        if not paths or any(Path(p).is_absolute() or '..' in Path(p).parts or
                            p.startswith(('.git/', '.github/')) for p in paths):
            raise SystemExit('Invalid or out-of-scope patch path')
        item = {'name': group['name'], 'parent': git('rev-parse', 'HEAD', capture=True).stdout.strip(),
                'paths': paths, 'checks': [], 'pushed': False}
        results.append(item)
        git('apply', '--index', '--check', input=group['patch'])
        git('apply', '--index', input=group['patch'])
        actual = git('diff', '--cached', '--name-only', capture=True).stdout.splitlines()
        if sorted(actual) != sorted(paths):
            raise SystemExit('Patch changes do not match the reviewed path inventory')
        git('diff', '--cached', '--check')
        if not group['commands']:
            raise SystemExit('Each chapter must provide verification commands')
        for index, command in enumerate(group['commands'], 1):
            name = f'{number:02}-{index:02}.log'
            print('VERIFY', group['name'], command, flush=True)
            with (evidence / name).open('w') as log:
                result = subprocess.run(command, cwd=root, env=safe_env, stdout=log,
                                        stderr=subprocess.STDOUT, text=True, timeout=240)
            item['checks'].append({'command': command, 'returncode': result.returncode, 'log': name})
            if result.returncode:
                print((evidence / name).read_text(), flush=True)
                raise SystemExit('Verification failed; this chapter was not pushed')
        git('commit', '-m', group['message'])
        item['commit'] = git('rev-parse', 'HEAD', capture=True).stdout.strip()
        push('HEAD:refs/heads/main')
        item['pushed'] = not args.no_push
        print('VERIFIED_COMMIT', item['commit'], group['name'], flush=True)
    if data.get('cleanup_transport'):
        push('--delete', 'audit-remediation-transport-20260923')
finally:
    (evidence / 'commits.json').write_text(json.dumps(results, indent=2) + '\n')
    (evidence / 'runtime.txt').write_text(subprocess.check_output(['python3', '--version'], text=True))
    with (evidence / 'source.tar').open('wb') as output:
        subprocess.run(['git', 'archive', '--format=tar', 'HEAD'], cwd=root, stdout=output, check=True)
