#!/usr/bin/env python3
"""Check every relative link and image path in every markdown file in this repo.

Written 2026-09-21 because a section was renumbered (05-testing became
06-testing) and a link in a different file went on pointing at the old path. It
was found by a person reading, not by me, and my own check at the time looked at
exactly two files out of twelve.

That is the sibling failure: fix the call site in front of you, leave the twin.
So this walks everything.

Exit code 1 if anything is broken, so it can gate a commit.

    python3 docs/check-links.py
"""
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")

def main() -> int:
    broken = []
    checked = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT)
            text = open(path, encoding="utf-8", errors="ignore").read()
            for link in LINK.findall(text):
                if link.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                checked += 1
                target = urllib.parse.unquote(link.split("#")[0]).rstrip("/")
                if not target:
                    continue
                resolved = os.path.normpath(os.path.join(dirpath, target))
                if not os.path.exists(resolved):
                    broken.append(f"{rel}  ->  {link}")

    print(f"checked {checked} relative links across the repo")
    if broken:
        print(f"BROKEN ({len(broken)}):")
        for b in broken:
            print("   ", b)
        return 1
    print("all resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
