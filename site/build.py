#!/usr/bin/env python3.12
"""Build the static site from the concept-first curriculum.

    python3.12 site/build.py          # markdown -> site/out/
    python3.12 site/serve.py          # http://127.0.0.1:8901

Three decisions worth knowing about, because each one removes a class of bug
rather than adding a feature.

* **The output mirrors the repo tree.** `curriculum/01-code/.../README.md`
  becomes `curriculum/01-code/.../index.html`. That does not remove the need to
  rewrite links — this content links to `.md` files, which is right on GitHub
  and dead on a website, and there are 1,421 of them. What the mirroring buys
  is that the rewrite is total and mechanical: every `.md` path maps to exactly
  one output path by a rule with no lookups in it, so directory structure can
  never drift out from under a link. `site/check.py` walks the BUILT pages and
  resolves every href against disk, because the old checker validated the
  markdown and would have passed this build with 1,421 dead links in it.

* **Mermaid is pre-rendered to SVG at build time**, by `tools/render-mermaid.mjs`,
  in the house palette. 387 diagrams that need three megabytes of JavaScript to
  appear are 387 diagrams that sometimes do not appear. They are also emitted at
  natural size rather than scaled to fit, because scaling a wide diagram down to
  the text column shrinks its labels to the point of uselessness — the wide ones
  scroll instead.

* **`<details>` gets `markdown="1"` injected before conversion.** Without it the
  197 collapsible solutions in this curriculum render their insides as raw
  markdown: tables as pipes, emphasis as asterisks. It looks completely fine in
  the build log.

The curriculum's own vocabulary carries the teaching — `Changed requirement`,
`Follow-up N`, `Senior expectation`, `Invariant` — so those are styled as
first-class objects rather than left as bold paragraphs. They are the part a
reader is here for.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
from functools import lru_cache
import diagram_cache

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("SITE_OUT")) if os.environ.get("SITE_OUT") \
      else Path(__file__).resolve().parent / "out"
TOOLS = Path(__file__).resolve().parent / "tools"
MERMAID_CACHE = Path(__file__).resolve().parent / ".mermaid-cache"

SITE_TITLE = "Software engineering, in depth"
SITE_SHORT = "software engineering, in depth"
SITE_LEDE = (
    "A learning guide that starts every concept from a concrete problem and goes as "
    "deep as the follow-ups take it. For interviews, for the job, and for directing "
    "an AI without losing the judgment."
)

# ---------------------------------------------------------------- content map

# Four groups, in reading order. The accent is an identity mark used in small
# doses — a chip, a rule, the active nav item — not a theme. Green stays the
# base ink throughout so the site reads as one thing.
GROUPS = {
    "01-code": ("Write correct code", "#1f5b76", "Correctness, data structures, and directing an AI without losing the judgment."),
    "02-applications": ("Build a complete application", "#2f6f4e", "Backend, data, frontend, tests, and authorisation that actually holds."),
    "03-production": ("Design, ship, and operate", "#a8682f", "Design under constraints, then deliver it and keep it alive at three in the morning."),
    "04-scale-and-evolution": ("Scale and evolve", "#6f4a7d", "Load, cost, models, migrations, and the decisions that outlast you."),
}

# Content kinds, derived from the tree rather than invented. Each one changes
# what a reader is being asked to do, which is why it gets a visible badge.
KINDS = {
    "problem":  ("problem",  "Try it, then open the solution"),
    "lab":      ("lab",      "Hands-on"),
    "project":  ("project",  "Build brief"),
    "case":     ("case",     "Real incident"),
    "lesson":   ("lesson",   "Worked lesson"),
    "design":   ("design",   "System design"),
    "aws":      ("aws",      "AWS implementation"),
    "practice": ("practice", "Mock interview"),
    "index":    ("index",    "Index"),
    "concept":  ("concept",  ""),
    "company":  ("company studio", "Senior interview rehearsal"),
}

SECTION_DIRS = {"problems": "problem", "labs": "lab", "projects": "project",
                "cases": "case", "lessons": "lesson", "aws": "aws"}


LEAD_NUM = re.compile(r"^\d+[.)]\s+")


def first_heading(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    t = re.sub(r"[*`\[\]]|\(.*?\)", "", m.group(1)).strip() if m else "Untitled"
    # Sub-chapter titles arrive numbered from the file they came from, and two
    # project sets in one chapter produce 1,2,3,4,5 followed by 4,5 again. The
    # chapter number and the sub-chapter position are the only numbering the
    # reader should see, and this build assigns both.
    return LEAD_NUM.sub("", t)


def summary_of(text: str) -> str:
    """First real paragraph, stripped, for search results and cards."""
    body = re.sub(r"^#.*$", "", text, flags=re.M)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    body = re.sub(r"<[^>]+>", "", body)
    for para in body.split("\n\n"):
        p = " ".join(para.split())
        p = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", p)
        p = re.sub(r"[*_`#|>]", "", p).strip()
        if len(p) > 60 and not p.startswith("Curriculum"):
            return p
    return ""


def prose_of(text: str) -> str:
    """Readable prose for full-text search.

    Code, tables and mermaid come out: searching a 190,000-word curriculum for
    "queue" should land on the paragraph explaining queues, not on the forty
    diagrams with a node called `queue`.
    """
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"^\s*\|.*$", " ", t, flags=re.M)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[*_#>]", " ", t)
    return " ".join(t.split())


def kind_for(rel: Path) -> str:
    parts = rel.parts
    if parts[0] == "companies":
        return "company"
    if parts[0] == "practice":
        return "practice"
    if parts[0] == "indexes":
        return "index"
    if parts[0] == "projects":
        return "project"
    if parts[0] == "docs":
        return "concept"
    for p in parts:
        if p in SECTION_DIRS:
            return SECTION_DIRS[p]
    if len(parts) >= 4 and parts[0] == "curriculum" and parts[-1].endswith(".md"):
        if parts[-1] == "README.md":
            return "concept"
        return "concept"
    return "concept"



# The chapter READMEs already state the pedagogy: "Learn in this order" is an
# ordered table, "Apply the concept" an ordered list of project briefs. That
# order is the author's, it interleaves labs and problems deliberately, and it
# is not the order a directory walk produces. Use it.
NAV_SECTIONS = ("Learn in this order", "Apply the concept", "Supporting material")
SEC_LABEL = {"Learn in this order": "Learn", "Apply the concept": "Apply",
             "Supporting material": "Supporting material"}
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)#]+\.md)(?:#[^)]*)?\)")

# Answer keys and repo meta are not lessons. They were in the reading sequence
# because they are markdown files in the right directory, which is the only
# thing a directory walk can know.
def is_lesson(name: str) -> bool:
    n = name.lower()
    return not (n.endswith("assessor.md") or n == "validation.md")


def chapter_sequence(chapter_readme: Path) -> list[tuple[str, str]]:
    """(path relative to repo root, section label) in the order he wrote."""
    text = chapter_readme.read_text(encoding="utf-8")
    here = chapter_readme.parent
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for sec in NAV_SECTIONS:
        m = re.search(rf"^## {re.escape(sec)}$(.*?)(?=^## |\Z)", text, re.M | re.S)
        if not m:
            continue
        for link in MD_LINK.finditer(m.group(1)):
            target = (here / link.group(2)).resolve()
            if not target.exists():
                continue
            try:
                rel = target.relative_to(ROOT)
            except ValueError:
                continue
            rels = str(rel).replace(os.sep, "/")
            # only things inside this chapter; a cross-chapter link is a
            # prerequisite, not a step
            if not rels.startswith(str(here.relative_to(ROOT)).replace(os.sep, "/") + "/"):
                continue
            if rels in seen or not is_lesson(target.name):
                continue
            seen.add(rels)
            out.append((rels, SEC_LABEL[sec]))

    # anything in the chapter he did not list still has to be reachable in the
    # flow, in a stable order, after what he did list
    rest = []
    for f in sorted(here.rglob("*.md")):
        rels = str(f.relative_to(ROOT)).replace(os.sep, "/")
        if f == chapter_readme or rels in seen or not is_lesson(f.name):
            continue
        rest.append((rels, "More practice"))
    return out + rest


def chapter_blurbs() -> dict[str, str]:
    """The `You will learn to...` line each part README already gives per chapter.

    Harvested rather than written again, so the subtitle on the contents page
    and the one in the markdown cannot say different things.
    """
    out: dict[str, str] = {}
    row = re.compile(r"\|\s*\d+\s*\|\s*\[[^\]]+\]\(([^)/]+)/README\.md\)\s*\|\s*([^|]+?)\s*\|")
    for gdir in GROUPS:
        f = ROOT / "curriculum" / gdir / "README.md"
        if not f.exists():
            continue
        for m in row.finditer(f.read_text(encoding="utf-8")):
            out[f"{gdir}/{m.group(1)}"] = m.group(2).strip()
    return out


CHAPTER_BLURBS: dict[str, str] = {}


def collect() -> list[dict]:
    """Every page we publish, in reading order.

    The shape is a book and the reading order says so:

        home
        Part 1 — what this part is for
          Chapter 1 — the context and the teaching
            1.1, 1.2, ...  the problems, labs and projects of chapter 1
          Chapter 2
            2.1, 2.2, ...
        Part 2 — ...

    Parts are back in the sequence as short intros. They are not a gate: the
    contents page still reaches any chapter in one click. They are there so
    that reading straight through has a moment that says "this is what the
    next two chapters are for", which is what a book does and what jumping
    from chapter 2 straight into part 2 does not.
    """
    pages: list[dict] = []
    chapter_no = [0]

    def add(src: Path, **kw):
        if not (ROOT / src).exists():
            return
        pages.append({"src": str(src).replace(os.sep, "/"), **kw})

    add(Path("README.md"), kind="home", title=SITE_TITLE, group=None, subject=None)

    for gi, (gdir, (gname, gcolour, gblurb)) in enumerate(GROUPS.items(), 1):
        gpath = ROOT / "curriculum" / gdir
        if not gpath.is_dir():
            continue
        add(Path("curriculum") / gdir / "README.md", kind="group",
            title=gname, group=gdir, subject=None, gnum=gi)

        for sdir in sorted(p for p in gpath.iterdir() if p.is_dir()):
            srel = Path("curriculum") / gdir / sdir.name
            chapter_no[0] += 1
            ch = chapter_no[0]
            add(srel / "README.md", kind="subject", group=gdir, subject=sdir.name,
                gnum=gi, chapter=ch,
                blurb=CHAPTER_BLURBS.get(f"{gdir}/{sdir.name}", ""))

            # Sub-chapters in the order the chapter README states, not the
            # order the filesystem happens to be in.
            sub_no = 0
            for rels, section in chapter_sequence(sdir / "README.md"):
                sub_no += 1
                add(Path(rels), kind=kind_for(Path(rels)), group=gdir,
                    subject=sdir.name, gnum=gi, chapter=ch, sub=sub_no,
                    section=section)

    for extra in ("curriculum/README.md",):
        add(Path(extra), kind="toc", group=None, subject=None)

    # Assessor packs and validation notes are linked from the practice material
    # and from the repo docs, so they are built — just never handed to a learner
    # as the next thing to read.
    for f in sorted((ROOT / "curriculum").rglob("*.md")):
        if is_lesson(f.name):
            continue
        add(f.relative_to(ROOT), kind="practice", group=None, subject=None,
            area="assessor")

    for d in ("indexes", "practice", "projects", "docs", "scripts", "companies", "examples/link-watcher"):
        base = ROOT / d
        if not base.is_dir():
            continue
        readme = base / "README.md"
        if readme.exists():
            add(readme.relative_to(ROOT), kind=kind_for(Path(d, "README.md")),
                group=None, subject=None, area=d)
        for f in sorted(base.rglob("*.md")):
            if f.name == "README.md" and f.parent == base:
                continue
            add(f.relative_to(ROOT), kind=kind_for(f.relative_to(ROOT)),
                group=None, subject=None, area=d)

    seen, ordered = set(), []
    for p in pages:
        if p["src"] in seen:
            continue
        seen.add(p["src"])
        ordered.append(p)

    subject_titles = {}
    group_titles = {g: v[0] for g, v in GROUPS.items()}
    for p in ordered:
        text = (ROOT / p["src"]).read_text(encoding="utf-8")
        p["text"] = text
        p.setdefault("title", first_heading(text))
        p["summary"] = summary_of(text)
        p["url"] = url_for(p["src"])
        if p["kind"] == "subject":
            subject_titles[(p["group"], p["subject"])] = p["title"]
    for p in ordered:
        p["subject_title"] = subject_titles.get((p.get("group"), p.get("subject")), "")
        p["group_title"] = group_titles.get(p.get("group"), "")
    return ordered


def url_for(src: str) -> str:
    if src == "README.md":
        return "/"
    if src.endswith("/README.md"):
        return "/" + src[: -len("README.md")]
    return "/" + src[:-3] + ".html"


def dest_for(src: str) -> str:
    if src.endswith("README.md"):
        return src[: -len("README.md")] + "index.html"
    return src[:-3] + ".html"


# ------------------------------------------------------------------- mermaid

MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.S)


@lru_cache(maxsize=1)
def renderer_inputs() -> dict:
    chrome = os.environ.get("CHROME_PATH") or next(
        (str(p) for p in Path.home().glob(".cache/ms-playwright/chromium*/chrome-*/chrome")), "")
    if not chrome:
        raise RuntimeError("Chromium is required; set CHROME_PATH. No preview fallback in a release build.")
    browser = subprocess.check_output([chrome, "--version"], text=True).strip()
    node = subprocess.check_output(["node", "--version"], text=True).strip()
    # Font bytes, not installation paths, are part of the renderer environment.
    fonts = subprocess.check_output(["fc-list", "--format", "%{file}\n"], text=True).splitlines()
    font_hashes = sorted({hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in fonts})
    return {"renderer": hashlib.sha256((TOOLS / "render-mermaid.mjs").read_bytes()).hexdigest(),
            "lock": hashlib.sha256((TOOLS / "package-lock.json").read_bytes()).hexdigest(),
            "browser": browser, "node": node,
            "fonts": hashlib.sha256("\n".join(font_hashes).encode()).hexdigest()}


def diagram_key(code: str) -> str:
    return diagram_cache.key(code, renderer_inputs())


def mermaid_blocks(pages) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in pages:
        for m in MERMAID_RE.finditer(p["text"]):
            code = m.group(1).strip()
            out[diagram_key(code)] = code
    return out


def render_mermaid(blocks: dict[str, str]) -> set[str]:
    """Pre-render to SVG. Returns the set of hashes that have an SVG on disk."""
    MERMAID_CACHE.mkdir(parents=True, exist_ok=True)
    manifest = [{"hash": h, "code": c} for h, c in sorted(blocks.items())]
    mf = MERMAID_CACHE / "_manifest.json"
    mf.write_text(json.dumps(manifest), encoding="utf-8")

    (MERMAID_CACHE / "_inputs.json").write_text(json.dumps(renderer_inputs(), indent=2) + "\n")
    missing = [h for h in blocks if not diagram_cache.valid_svg(MERMAID_CACHE / f"{h}.svg")]
    for h in missing:
        (MERMAID_CACHE / f"{h}.svg").unlink(missing_ok=True)
    if missing:
        chrome = os.environ.get("CHROME_PATH") or next(
            (str(p) for p in Path.home().glob(".cache/ms-playwright/chromium*/chrome-*/chrome")), "")
        if not chrome:
            raise RuntimeError("No Chromium available for required diagram rendering")
        else:
            env = dict(os.environ, CHROME_PATH=chrome)
            sysroot = Path.home() / "sysroot"
            if sysroot.is_dir():
                env["LD_LIBRARY_PATH"] = f"{sysroot}/usr/lib64:{sysroot}/lib64:" + env.get("LD_LIBRARY_PATH", "")
            r = subprocess.run(["node", str(TOOLS / "render-mermaid.mjs"), str(mf), str(MERMAID_CACHE)],
                               env=env, capture_output=True, text=True, check=True)
            for line in (r.stdout + r.stderr).strip().splitlines():
                print(f"  {line}")
    have = {h for h in blocks if diagram_cache.valid_svg(MERMAID_CACHE / f"{h}.svg")}
    if len(have) != len(blocks):
        print(f"  ! {len(blocks) - len(have)} diagrams missing an SVG", file=sys.stderr)
    return have


def substitute_mermaid(text: str, have: set[str], depth: int) -> str:
    """Replace each mermaid fence with a reference to its pre-rendered SVG."""
    up = "../" * depth
    def repl(m):
        code = m.group(1).strip()
        h = diagram_key(code)
        if h not in have:
            raise RuntimeError(f"Required diagram missing: {h}")
        return (f'\n<div class="mer"><img src="{up}assets/mermaid/{h}.svg" '
                f'alt="Diagram" loading="lazy"></div>\n')
    return MERMAID_RE.sub(repl, text)


# -------------------------------------------------------------------- render

MD_EXT = ["extra", "toc", "sane_lists", "md_in_html"]

# The curriculum's recurring bold leads. These are the teaching objects, so the
# page gives them shape instead of leaving them as another bold paragraph.
MARKERS = [
    (r"Changed requirement:",   "changed",  "changed requirement"),
    (r"Follow-up\s*\d*\s*[—:-]", "followup", "follow-up"),
    (r"Follow-up:",             "followup", "follow-up"),
    (r"Senior expectation:",    "depth",    "senior expectation"),
    (r"Staff(?:/lead)? expectation:", "depth", "staff expectation"),
    (r"Invariant:",             "invariant", "invariant"),
    (r"Redraw challenge:",      "redraw",   "redraw challenge"),
    (r"Not covered here:",      "aside",    "not covered"),
]


def style_markers(html: str) -> str:
    """Turn `<p><strong>Changed requirement:</strong> ...` into a marked block.

    Where the bold lead is *only* the marker phrase it is dropped, because the
    block already carries that word as its label and printing it twice is the
    decoration my own style rules forbid. Where the bold carries more than the
    phrase — `Follow-up 1 — background heap cleanup.` — it is a real title and
    stays.
    """
    for pat, cls, label in MARKERS:
        def repl(m, cls=cls, label=label):
            inner = m.group(1)
            rest = re.sub(rf"^{pat}\s*", "", inner).strip()
            lead = f"<strong>{inner}</strong>" if rest else ""
            return f'<p class="mk mk-{cls}" data-mk="{label}">{lead}'
        html = re.sub(rf"<p><strong>({pat}(?:[^<]|<(?!/strong>))*)</strong>", repl, html)
    return html


NAV_SECTION_RE = re.compile(
    r"^## (?:Learn in this order|Apply the concept|Supporting material)\s*$.*?(?=^## |\Z)",
    re.M | re.S)
TRAILING_NAV = re.compile(r"^Next chapter: \[[^\]]+\]\([^)]+\)\.?\s*$", re.M)


def strip_chapter_menus(text: str) -> str:
    """Take the link menus off a chapter page.

    A chapter page used to be a title, a blurb and then three lists of links:
    learn these in this order, then open each of these, then here is some
    supporting material. That is a directory listing wearing prose, and it puts
    the work of sequencing on the reader. The order is now enforced by the
    reading flow, so the menus are not information, they are a second way to
    move that disagrees with the first.
    """
    text = NAV_SECTION_RE.sub("", text)
    text = TRAILING_NAV.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def render_body(text: str, have: set[str], depth: int) -> tuple[str, list]:
    text = substitute_mermaid(text, have, depth)
    # md_in_html only descends into elements that ask it to
    text = text.replace("<details>", '<details markdown="1">')
    md = markdown.Markdown(extensions=MD_EXT)
    html = md.convert(text)
    toc = getattr(md, "toc_tokens", [])

    html = html.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    html = re.sub(r"<p>(<img[^>]*>)</p>", r'<div class="figwrap">\1</div>', html)
    html = style_markers(html)
    html = rewrite_md_links(html)
    return html, flatten_toc(toc)


MD_HREF = re.compile(r'(href=")([^"]+?)\.md(#[^"]*)?(")')


def rewrite_md_links(html: str) -> str:
    """`../x/README.md` -> `../x/`, `../x/y.md` -> `../x/y.html`.

    The curriculum links to `.md` files because that is what works on GitHub.
    On a site every one of them is a 404, and there are more than fourteen
    hundred. The mapping is the same rule `dest_for` uses when writing the
    files, which is why it cannot disagree with where they landed.
    """
    def repl(m):
        pre, path, frag, post = m.group(1), m.group(2), m.group(3) or "", m.group(4)
        if path.startswith(("https://", "http://", "//")):
            return m.group(0)
        if path.endswith("README"):
            out = path[: -len("README")] or "./"
        else:
            out = path + ".html"
        return f"{pre}{out}{frag}{post}"
    return MD_HREF.sub(repl, html)


CRUMB_P = re.compile(r"<p>((?:\s*<a [^>]*>[^<]*</a>\s*(?:·|\|)?\s*)+)</p>", re.S)
LINK_RE = re.compile(r'<a href="([^"]*)"[^>]*>([^<]*)</a>')


def lift_crumb(html: str, page) -> tuple[str, str]:
    """Pull the markdown's own breadcrumb out of the body.

    166 of these files open with `[Curriculum](..) · [Subject](..)`, which the
    page shell already shows above the title. Left in place it reads as the
    same line printed twice. The links that are NOT duplicates — "All coding
    problems", a prerequisite — are worth keeping, so they become chips instead
    of being thrown away with the rest.
    """
    m = CRUMB_P.search(html[:1400])
    if not m:
        return html, ""
    links = LINK_RE.findall(m.group(1))
    if len(links) < 2:
        return html, ""
    dupes = {"curriculum", "home", (page.get("subject_title") or "").lower()}
    for p in ("group_title",):
        if page.get(p):
            dupes.add(page[p].lower())
    keep = [(h, t) for h, t in links if t.strip().lower() not in dupes]
    html = html[: m.start()] + html[m.end():]
    if not keep:
        return html, ""
    chips = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in keep)
    return html, f'<div class="pair">{chips}</div>'


def flatten_toc(tokens) -> list[str]:
    """python-markdown gives nested dicts; search only wants the heading text."""
    names: list[str] = []
    def walk(items):
        for t in items:
            names.append(t.get("name", ""))
            walk(t.get("children", []))
    walk(tokens or [])
    return names


def main():
    import reader
    return reader.build(sys.modules[__name__])


if __name__ == "__main__":
    sys.exit(main())
