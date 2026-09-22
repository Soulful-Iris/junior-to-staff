#!/usr/bin/env python3.12
"""Check the BUILT site, not the markdown.

The markdown link checker on the old site validated the source. This one walks
`site/out` and resolves every href and src against what is actually on disk,
because the thing a reader clicks is the built page, and the step in between is
where a link breaks without anybody editing a link.

Reports, in order of how much they matter:
  dead   — a link or image that resolves to nothing. A 404 or a broken image.
  empty  — a page with almost no body. Usually a conversion that silently failed.
  orphan — a built page nothing links to. Reachable only by typing the URL.

Exit code is non-zero if anything is dead, so it can gate a deploy.
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urldefrag

OUT = Path(os.environ.get("SITE_OUT")) if os.environ.get("SITE_OUT") \
      else Path(__file__).resolve().parent / "out"
HREF = re.compile(r'(?:href|src)="([^"]+)"')


def main() -> int:
    if not OUT.is_dir():
        print("no build at site/out — run site/build.py first", file=sys.stderr)
        return 2

    pages = sorted(OUT.rglob("*.html"))
    dead: list[tuple[str, str]] = []
    linked: set[Path] = set()
    checked = 0
    empty: list[str] = []

    for page in pages:
        html = page.read_text(encoding="utf-8", errors="replace")

        # a page whose body is basically furniture is a conversion that failed
        body = re.sub(r"<(script|style|nav).*?</\1>", "", html, flags=re.S)
        body = re.sub(r"<[^>]+>", " ", body)
        # A short page is not a failed page if it is a list of links: the
        # index pages are deliberately terse. Only flag pages that are short
        # AND go nowhere, which is what a failed conversion looks like.
        if len(body.split()) < 40 and len(HREF.findall(html)) < 12:
            empty.append(str(page.relative_to(OUT)))

        for raw in HREF.findall(html):
            url, _ = urldefrag(raw)
            if not url or url.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            checked += 1
            rel = unquote(url)
            target = (OUT / rel.lstrip("/")) if rel.startswith("/") else (page.parent / rel)
            target = Path(target).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                dead.append((str(page.relative_to(OUT)), raw))
            else:
                try:
                    linked.add(target.relative_to(OUT.resolve()))
                except ValueError:
                    pass

    orphans = [str(p.relative_to(OUT)) for p in pages
               if p.relative_to(OUT) not in linked and p.name != "index.html"
               or (p.parent == OUT and p.name == "index.html") is False
               and p.relative_to(OUT) not in linked]
    orphans = sorted(set(o for o in orphans if o != "index.html" and not o.startswith("_")))

    print(f"checked {checked} links across {len(pages)} built pages")
    if dead:
        by_target = defaultdict(list)
        for src, url in dead:
            by_target[url].append(src)
        print(f"\nDEAD ({len(dead)} links, {len(by_target)} distinct targets):")
        for url, srcs in sorted(by_target.items(), key=lambda kv: -len(kv[1]))[:30]:
            print(f"  {url}\n      from {len(srcs)} page(s), e.g. {srcs[0]}")
    else:
        print("  all links resolve")

    if empty:
        print(f"\nEMPTY ({len(empty)}):")
        for e in empty[:20]:
            print(f"  {e}")

    if orphans:
        print(f"\nORPHANS ({len(orphans)}) — built but nothing links to them:")
        for o in orphans[:20]:
            print(f"  {o}")

    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
