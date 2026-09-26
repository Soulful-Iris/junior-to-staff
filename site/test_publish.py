"""The publisher keeps a bounded number of old releases.

    python3.12 -m pytest site/test_publish.py -q

Every release used to be kept. They do not share content (the HTML of every
page changes in every build), so each one cost the whole site again, about
110 MB, and on 2026-09-26 forty-six of them had filled the box's disk to 93%
and the keeper was emailing Bruno every hour.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import publish  # noqa: E402

REV = "b809086cfd47c9f00b5e319ba22af025eb0d0694"


def stage(root: Path, n: int) -> Path:
    s = root / f"out.stage.{n}"
    s.mkdir()
    (s / "index.html").write_text(f"<p>build {n}</p>\n")
    return s


def publish_n(root: Path, count: int, start: int = 0):
    live, marker = root / "out", root / "state" / "last-deployed"
    made = []
    for n in range(start, start + count):
        made.append(publish.publish(stage(root, n), live, REV, marker))
    return live, made


def releases(root: Path):
    return sorted(p.name for p in (root / ".releases").iterdir())


def test_only_the_newest_are_kept(tmp_path):
    live, made = publish_n(tmp_path, publish.KEEP + 4)
    kept = releases(tmp_path)
    assert len(kept) == publish.KEEP
    assert sorted(p.name for p in made[-publish.KEEP:]) == kept
    assert (live / "index.html").read_text() == f"<p>build {publish.KEEP + 3}</p>\n"


def test_fewer_than_the_limit_are_all_kept(tmp_path):
    publish_n(tmp_path, 3)
    assert len(releases(tmp_path)) == 3


def test_a_release_rolled_back_to_survives_the_next_publish(tmp_path):
    """Pointing out at an old release by hand is how a rollback is done. The
    publish after it must not delete the release that was live a moment ago,
    however old it is."""
    live, made = publish_n(tmp_path, publish.KEEP)
    oldest = made[0]
    publish.replace_link(live, os.path.relpath(oldest, live.parent))
    publish_n(tmp_path, 1, start=100)
    assert oldest.is_dir()


def test_a_legacy_directory_is_pruned_like_any_other(tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "index.html").write_text("legacy\n")
    publish_n(tmp_path, publish.KEEP + 2)
    assert not [n for n in releases(tmp_path) if n.startswith("legacy-")]


def test_a_prune_that_fails_does_not_fail_the_publish(tmp_path, monkeypatch, capsys):
    """The site is already switched and recorded when pruning runs. Raising
    then would make deploy.sh log PUBLICATION FAILED about a publication that
    succeeded, which is a lie in the one log anybody reads when it breaks."""
    publish_n(tmp_path, publish.KEEP)

    def refuse(path, *a, **k):
        raise PermissionError(f"refused {path}")

    monkeypatch.setattr(publish.shutil, "rmtree", refuse)
    live, made = publish_n(tmp_path, 1, start=50)
    assert os.path.realpath(live) == str(made[0])
    assert "could not remove" in capsys.readouterr().err
