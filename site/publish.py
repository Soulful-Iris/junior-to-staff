"""Publish a built static release, automatically adopting an existing out directory.

Old releases are retained. After initial adoption, releases use a symlink switch.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import uuid


def smoke(root):
    if not (root / 'index.html').is_file():
        raise ValueError('release has no index.html')


def replace_link(live, target):
    temporary = live.parent / (live.name + '.next-' + uuid.uuid4().hex)
    try:
        temporary.symlink_to(target, target_is_directory=True)
        os.replace(temporary, live)
    finally:
        temporary.unlink(missing_ok=True)


def record(marker, revision):
    marker.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=marker.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(revision + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, marker)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def publish(stage, live, revision, marker):
    stage, live, marker = Path(stage).absolute(), Path(live).absolute(), Path(marker).absolute()
    if not re.fullmatch(r'[0-9a-f]{7,40}', revision):
        raise ValueError('revision must identify the checked source commit')
    if stage.is_symlink() or stage.parent != live.parent or stage == live:
        raise ValueError('stage must be a separate real directory beside live')
    live.parent.mkdir(parents=True, exist_ok=True)
    with (live.parent / '.publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if live.exists() and not live.is_symlink() and not live.is_dir():
            raise ValueError('live path must be a directory or symlink')
        smoke(stage)
        (stage / 'version.json').write_text(
            json.dumps({'commit': revision}) + '\n')
        previous = os.readlink(live) if live.is_symlink() else None
        releases = live.parent / '.releases'
        releases.mkdir(exist_ok=True)
        release = releases / (revision + '-' + uuid.uuid4().hex)
        os.replace(stage, release)
        switched = False
        adopted = False
        try:
            if live.is_dir() and not live.is_symlink():
                legacy = releases / ('legacy-' + uuid.uuid4().hex)
                os.replace(live, legacy)
                previous = os.path.relpath(legacy, live.parent)
                adopted = True
            replace_link(live, os.path.relpath(release, live.parent))
            switched = True
            smoke(live)
            record(marker, revision)
        except BaseException:
            # Never delete old releases, even if restoration itself fails.
            # A failure before the switch leaves old live; after it, either
            # the complete new release or the restored old release is reachable.
            if (switched or adopted) and previous is not None:
                replace_link(live, previous)
            raise
        return release


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=Path)
    parser.add_argument('live', type=Path)
    parser.add_argument('revision')
    parser.add_argument('marker', type=Path)
    args = parser.parse_args()
    print(publish(args.stage, args.live, args.revision, args.marker))
