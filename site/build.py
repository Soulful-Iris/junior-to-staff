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

    for d in ("indexes", "practice", "projects", "docs", "scripts"):
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


def mermaid_blocks(pages) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in pages:
        for m in MERMAID_RE.finditer(p["text"]):
            code = m.group(1).strip()
            out[hashlib.sha256(code.encode()).hexdigest()[:16]] = code
    return out


def render_mermaid(blocks: dict[str, str]) -> set[str]:
    """Pre-render to SVG. Returns the set of hashes that have an SVG on disk."""
    MERMAID_CACHE.mkdir(parents=True, exist_ok=True)
    manifest = [{"hash": h, "code": c} for h, c in sorted(blocks.items())]
    mf = MERMAID_CACHE / "_manifest.json"
    mf.write_text(json.dumps(manifest), encoding="utf-8")

    missing = [h for h in blocks if not (MERMAID_CACHE / f"{h}.svg").exists()]
    if missing:
        chrome = os.environ.get("CHROME_PATH") or next(
            (str(p) for p in Path.home().glob(".cache/ms-playwright/chromium*/chrome-linux/chrome")), "")
        if not chrome:
            print("  ! no chromium found; diagrams will be skipped", file=sys.stderr)
        else:
            env = dict(os.environ, CHROME_PATH=chrome)
            sysroot = Path.home() / "sysroot"
            if sysroot.is_dir():
                env["LD_LIBRARY_PATH"] = f"{sysroot}/usr/lib64:{sysroot}/lib64:" + env.get("LD_LIBRARY_PATH", "")
            r = subprocess.run(["node", str(TOOLS / "render-mermaid.mjs"), str(mf), str(MERMAID_CACHE)],
                               env=env, capture_output=True, text=True)
            for line in (r.stdout + r.stderr).strip().splitlines():
                print(f"  {line}")
    have = {h for h in blocks if (MERMAID_CACHE / f"{h}.svg").exists()}
    if len(have) != len(blocks):
        print(f"  ! {len(blocks) - len(have)} diagrams missing an SVG", file=sys.stderr)
    return have


def substitute_mermaid(text: str, have: set[str], depth: int) -> str:
    """Replace each mermaid fence with a reference to its pre-rendered SVG."""
    up = "../" * depth
    def repl(m):
        code = m.group(1).strip()
        h = hashlib.sha256(code.encode()).hexdigest()[:16]
        if h not in have:
            return m.group(0)
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


# ----------------------------------------------------------------------- css

CSS = """
@font-face{font-family:"Source Serif 4"; src:url("fonts/source-serif-4-400.woff2") format("woff2");
  font-weight:400; font-style:normal; font-display:swap}
@font-face{font-family:"Source Serif 4"; src:url("fonts/source-serif-4-600.woff2") format("woff2");
  font-weight:600; font-style:normal; font-display:swap}
:root{
  --ground:#e8ece9; --paper:#fcfcfa; --ink:#1b2420; --muted:#5c675f;
  --rule:#d6dcd7; --green:#2f6f4e; --green-tint:#eaf0ec; --warm:#b2632f;
  --warm-tint:#f9efe7; --measure:66ch; --wide:860px;
  --accent:#2f6f4e; --accent-tint:#eaf0ec;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%; scroll-behavior:smooth}
body{margin:0; background:var(--ground); color:var(--ink);
  font:18px/1.68 "Source Serif 4","Iowan Old Style",Palatino,Georgia,serif}
.ui,.rail,.crumb,.pair,.nextprev,.bar,.badge,.mk::before{
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}

a{color:var(--accent); text-decoration-color:color-mix(in srgb, var(--accent) 38%, transparent);
  text-decoration-thickness:1px; text-underline-offset:2.5px;
  transition:text-decoration-color .12s, color .12s}
a:hover{color:var(--ink); text-decoration-color:currentColor}
.col table a{text-decoration-color:color-mix(in srgb, var(--accent) 26%, transparent)}
:focus-visible{outline:2px solid var(--warm); outline-offset:2px; border-radius:2px}

/* ---- frame ---- */
.frame{display:grid; grid-template-columns:282px minmax(0,1fr); min-height:100vh}
.main,.sheet,.col{min-width:0}
.rail{position:sticky; top:0; align-self:start; height:100vh; overflow-y:auto;
  padding:24px 16px 60px 26px; border-right:1px solid var(--rule);
  font-size:13.5px; line-height:1.45}
.main{padding:0 0 96px}
.sheet{background:var(--paper); border-left:1px solid var(--rule);
  border-right:1px solid var(--rule); min-height:100vh}
.col{max-width:var(--wide); margin:0 auto; padding:46px 28px 0}
/* Prose keeps a reading measure; figures and tables are allowed the full
   column, because a diagram squeezed to 66ch is a diagram nobody reads. */
.col > p, .col > ul, .col > ol, .col > h1, .col > h2, .col > h3, .col > h4,
.col > blockquote, .col > details > p, .col > details > ul, .col > details > ol{
  max-width:var(--measure)}

/* ---- rail ---- */
.brand{display:block; font-size:15px; font-weight:600; color:var(--ink);
  text-decoration:none; font-family:"Source Serif 4",Georgia,serif}
.brand small{display:block; font-weight:400; color:var(--muted); font-size:12px;
  margin-top:3px; font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.search{margin:16px 0 18px}
.search input{width:100%; padding:7px 10px; border:1px solid var(--rule); border-radius:6px;
  background:var(--paper); color:var(--ink); font:inherit; font-size:13.5px}
.search input::placeholder{color:#93a09a}
.tocjump{display:block; margin:0 0 14px; font-size:12px; letter-spacing:.06em;
  text-transform:uppercase; color:var(--muted); text-decoration:none; font-weight:600}
.tocjump:hover{color:var(--green)}

/* where you are, not where you could go */
.where{margin:16px 0 4px; padding:11px 12px; background:var(--paper);
  border:1px solid var(--rule); border-left:3px solid var(--gc); border-radius:7px}
.wpart{display:block; font-size:10.5px; letter-spacing:.07em; text-transform:uppercase;
  color:var(--gc); font-weight:700}
.wch{display:block; font-size:13px; color:var(--ink); margin-top:3px; font-weight:600}
.bar2{height:4px; background:var(--rule); border-radius:2px; margin:9px 0 5px; overflow:hidden}
.bar2 i{display:block; height:100%; background:var(--gc); border-radius:2px}
.wpct{font-size:11px; color:var(--muted)}

.stepsh{margin:20px 0 6px; font-size:10.5px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--muted); font-weight:600}
.rail ol.steps{list-style:none; margin:0; padding:0}
.rail ol.steps li{display:flex; gap:8px; padding:3px 7px; border-radius:4px;
  font-size:12.5px; line-height:1.4; color:var(--muted)}
.rail ol.steps li .sn{font-variant-numeric:tabular-nums; min-width:2.3em; color:#a8b2ab}
.rail ol.steps a{display:flex; gap:8px; color:var(--ink); text-decoration:none; flex:1}
.rail ol.steps li:has(a):hover{background:var(--green-tint)}
.rail ol.steps li.on{background:var(--accent); color:var(--paper); font-weight:600}
.rail ol.steps li.on .sn{color:var(--paper); opacity:.75}
/* ahead of you: visible so you know the shape, not clickable so you do not skip */
.rail ol.steps li.notyet{color:#b3bcb6}
.rail ol.steps li.notyet .sn{color:#c6cdc8}
.rail .ext{margin-top:24px; padding-top:14px; border-top:1px solid var(--rule); font-size:12.5px}
.rail .ext a{display:block; margin:5px 0; color:var(--muted); text-decoration:none}
.rail .ext a:hover{color:var(--green)}

/* ---- page furniture ---- */
.crumb{font-size:13px; color:var(--muted); margin:0 0 14px}
.crumb a{color:var(--muted); text-decoration:none}
.crumb a:hover{color:var(--accent)}
.crumb .dot{opacity:.5; margin:0 6px}
.badge{display:inline-block; font-size:11px; letter-spacing:.06em; text-transform:uppercase;
  font-weight:600; padding:2px 7px; border-radius:4px; background:var(--accent-tint);
  color:var(--accent); vertical-align:2px}
.badge.b-problem{background:var(--warm-tint); color:var(--warm)}
.badge.b-lab,.badge.b-aws{background:#eaeef4; color:#3a5a7a}
.badge.b-case{background:var(--warm-tint); color:#9a4a2a}
.badge.b-practice{background:#f1ecf4; color:#63467a}
.badge.b-chapter{background:var(--accent); color:var(--paper)}
.kindnote{font-size:13.5px; color:var(--muted); margin:0 0 22px}

/* ---- content ---- */
.col h1{font-size:33px; line-height:1.18; margin:0 0 10px; letter-spacing:-.012em}
.col h2{font-size:22px; line-height:1.3; margin:40px 0 12px; letter-spacing:-.008em;
  padding-bottom:5px; border-bottom:1px solid var(--rule); max-width:var(--wide)}
.col h3{font-size:18.5px; margin:30px 0 9px}
.col h4{font-size:17px; margin:24px 0 8px}
.col p,.col li{overflow-wrap:break-word}
.col blockquote{margin:16px 0 26px; padding:12px 18px; border-left:3px solid var(--accent);
  background:var(--accent-tint); border-radius:0 7px 7px 0; color:var(--ink);
  font-size:17px; max-width:var(--measure)}
.col blockquote p{margin:.3em 0}
.col hr{border:0; border-top:1px solid var(--rule); margin:38px 0}
.col ul,.col ol{padding-left:22px}
.col li{margin:5px 0}
.col code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.85em;
  background:var(--green-tint); padding:1px 4px; border-radius:3px}
.col pre{background:#20302a; color:#e6ece8; padding:15px 17px; border-radius:8px;
  overflow-x:auto; font-size:14px; line-height:1.55; margin:20px 0}
.col pre code{background:none; padding:0; color:inherit; font-size:14px}

/* figures: natural size, scroll rather than shrink */
/* Scroll shadows: a wide diagram keeps its natural text size and scrolls, so
   the edge needs to say so. Pure CSS — the two fixed layers are the "ends",
   the two scrolling layers cover them when there is nothing more that way. */
.mer{margin:26px 0; overflow-x:auto; -webkit-overflow-scrolling:touch;
  background:var(--paper); border:1px solid var(--rule); border-radius:9px;
  padding:16px 14px; text-align:center;
  background-image:
    linear-gradient(to right, var(--paper) 30%, rgba(250,249,247,0)),
    linear-gradient(to left,  var(--paper) 30%, rgba(250,249,247,0)),
    linear-gradient(to right, rgba(27,36,32,.20), rgba(27,36,32,0) 20px),
    linear-gradient(to left,  rgba(27,36,32,.20), rgba(27,36,32,0) 20px);
  background-position:0 0, 100% 0, 0 0, 100% 0;
  background-repeat:no-repeat;
  background-size:36px 100%, 36px 100%, 18px 100%, 18px 100%;
  background-attachment:local, local, scroll, scroll}
.mer img{display:inline-block; max-width:none; height:auto}
.figwrap{margin:26px 0; overflow-x:auto; -webkit-overflow-scrolling:touch;
  background:var(--paper); border-radius:9px}
.figwrap img{display:block; width:100%; height:auto; border-radius:9px}

.tablewrap{overflow-x:auto; margin:22px 0; -webkit-overflow-scrolling:touch}
.col table{width:100%; border-collapse:collapse; font-size:15px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.col th{text-align:left; font-weight:600; border-bottom:1.5px solid var(--rule);
  padding:7px 9px; background:var(--green-tint)}
.col td{border-bottom:1px solid var(--rule); padding:7px 9px; vertical-align:top}
.col tr:last-child td{border-bottom:0}

/* ---- the teaching objects ---- */
.mk{position:relative; margin:22px 0; padding:13px 16px 13px 17px;
  border-left:3px solid var(--rule); border-radius:0 7px 7px 0;
  background:#f6f5f2; font-size:16.5px; max-width:var(--measure)}
.mk::before{content:attr(data-mk); display:block; font-size:10.5px; font-weight:600;
  letter-spacing:.09em; text-transform:uppercase; color:var(--muted); margin-bottom:5px}
.mk strong{font-weight:600}
.mk-changed{border-left-color:var(--warm); background:var(--warm-tint)}
.mk-changed::before{color:var(--warm)}
.mk-followup{border-left-color:#3a5a7a; background:#eef1f6}
.mk-followup::before{color:#3a5a7a}
.mk-depth{border-left-color:#63467a; background:#f2eef5}
.mk-depth::before{color:#63467a}
.mk-invariant{border-left-color:var(--green); background:var(--green-tint)}
.mk-invariant::before{color:var(--green)}
.mk-redraw{border-left-color:#8a857d}
.mk-aside{border-left-color:var(--rule); background:transparent; color:var(--muted);
  font-size:15.5px}

/* ---- reveal panels ---- */
.col details{margin:24px 0; border:1px solid var(--rule); border-radius:9px;
  background:#f6f5f2; max-width:var(--wide)}
.col details[open]{background:var(--paper)}
.col summary{cursor:pointer; padding:12px 16px; font-weight:600; font-size:16px;
  list-style:none; display:flex; gap:9px; align-items:baseline;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.col summary::-webkit-details-marker{display:none}
.col summary::before{content:"›"; display:inline-block; color:var(--accent);
  font-size:20px; line-height:1; transform:rotate(0deg); transition:transform .15s}
.col details[open] summary::before{transform:rotate(90deg)}
.col summary:hover{color:var(--accent)}
.col details > *:not(summary){margin-left:16px; margin-right:16px}
.col details > *:last-child{margin-bottom:16px}

/* ---- nav pairs and prev/next ---- */
.pair{display:flex; flex-wrap:wrap; gap:8px; margin:0 0 26px; font-size:13.5px}
.pair a{padding:5px 12px; border:1px solid var(--rule); border-radius:999px;
  text-decoration:none; color:var(--ink); background:var(--paper)}
.pair a:hover{border-color:var(--accent)}
.pair a[aria-current]{background:var(--accent); color:var(--paper); border-color:var(--accent)}
.nextprev{display:flex; justify-content:space-between; align-items:center; gap:16px;
  margin:56px 0 0; padding-top:22px; border-top:1px solid var(--rule); font-size:14px;
  max-width:var(--measure)}
.nextprev a{text-decoration:none; color:var(--ink)}
.nextprev span{display:block; font-size:12px; margin-bottom:2px; letter-spacing:.04em;
  text-transform:uppercase}
.nextprev .back{color:var(--muted); font-size:13.5px; max-width:42%}
.nextprev .back span{color:#a8b2ab}
.nextprev .back:hover{color:var(--ink)}
/* one obvious way forward */
.nextprev .fwd{margin-left:auto; text-align:right; max-width:58%;
  background:var(--accent); color:var(--paper); padding:12px 20px; border-radius:10px}
.nextprev .fwd span{color:var(--paper); opacity:.78}
.nextprev .fwd:hover{background:var(--ink); color:var(--paper)}

/* ---- home ---- */
.hero{padding:48px 28px 0; max-width:var(--wide); margin:0 auto}
.hero h1{font-size:42px; line-height:1.1; margin:0 0 14px; letter-spacing:-.02em}
.hero .lede{font-size:20px; line-height:1.55; color:var(--muted); max-width:36em; margin:0 0 26px}
.heroimg{margin:0 0 30px; border:1px solid var(--rule)}
.hero .how{background:var(--paper); border:1px solid var(--rule); border-radius:10px;
  padding:18px 20px; margin:0 0 34px; font-size:16px; max-width:40em}
.hero .how b{display:block; margin-bottom:6px; font-size:14px; letter-spacing:.04em;
  text-transform:uppercase; color:var(--muted);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.start{display:inline-block; margin:0 0 6px; padding:10px 18px; border-radius:999px;
  background:var(--green); color:var(--paper); text-decoration:none; font-size:15px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.start:hover{background:var(--ink); color:var(--paper)}
.toc{max-width:var(--wide); margin:8px auto 40px; padding:0 28px}
.toch{font-size:14px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted);
  margin:34px 0 4px; padding-bottom:8px; border-bottom:1px solid var(--rule);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.partblock{margin:30px 0 0}
.pnum{display:block; font-size:11px; letter-spacing:.1em; text-transform:uppercase;
  color:var(--gc); font-weight:700; margin-bottom:2px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.partspan{margin:0 0 14px; font-size:13px; color:var(--muted);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.chn{display:flex; flex-direction:column; align-items:center; min-width:3.4em;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:9.5px; letter-spacing:.09em; text-transform:uppercase; color:var(--muted)}
.chn b{font-size:22px; line-height:1.05; font-weight:600; color:var(--gc); letter-spacing:0}

.ahead{margin:48px 0 0; padding:22px 24px; border-radius:10px;
  background:var(--accent-tint); border:1px solid var(--rule); max-width:var(--measure)}
.ahead h2{margin:0 0 6px; border:0; padding:0; font-size:19px}
.ahead p{margin:0 0 16px; color:var(--muted); font-size:16px}
.begin{display:inline-block; padding:11px 20px; border-radius:999px;
  background:var(--accent); color:var(--paper); text-decoration:none; font-size:15.5px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.begin:hover{background:var(--ink); color:var(--paper)}
.sech{margin:22px 0 8px; font-size:11px; letter-spacing:.09em; text-transform:uppercase;
  color:var(--muted); font-weight:600;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.sublist{display:grid; gap:6px}
.subrow{display:flex; gap:13px; align-items:baseline; padding:10px 14px;
  background:var(--paper); border:1px solid var(--rule); border-radius:8px;
  text-decoration:none; color:var(--ink); font-size:16px}
.subrow:hover{border-color:var(--accent); background:#fff}
.subrow .sn{font-variant-numeric:tabular-nums; color:var(--accent); font-weight:600;
  min-width:2.6em; font-size:14px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.badge.b-sub{background:var(--accent); color:var(--paper); margin-right:5px}
.parth{margin:0 0 4px; padding-bottom:8px; border-bottom:2px solid var(--gc);
  font-size:22px; letter-spacing:-.008em}
.parth a{color:var(--ink); text-decoration:none}
.parth a:hover{color:var(--gc)}
.partb{margin:0 0 14px; color:var(--muted); font-size:15px; max-width:44em}
.chlist{display:grid; gap:8px}
.chwrap{background:var(--paper); border:1px solid var(--rule);
  border-left:3px solid var(--gc); border-radius:8px; overflow:hidden}
.chwrap .ch{border:0; border-radius:0; background:transparent}
.steps-d{margin:0; border:0; border-top:1px solid var(--rule); border-radius:0;
  background:transparent; max-width:none}
.steps-d summary{padding:8px 16px 9px; font-size:12.5px; font-weight:400; color:var(--muted)}
.steps-d summary::before{font-size:16px}
.steps-d[open]{background:#fbfbf9}
.tsteps{list-style:none; margin:0 0 12px; padding:0 16px 0 44px}
.tsteps li{margin:2px 0; font-size:14px}
.tsteps .secl{margin:10px 0 3px; font-size:10.5px; letter-spacing:.08em;
  text-transform:uppercase; color:#a8b2ab; font-weight:600;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.tsteps a{display:flex; gap:10px; color:var(--ink); text-decoration:none; padding:2px 0}
.tsteps a:hover{color:var(--gc)}
.tsteps .sn{font-variant-numeric:tabular-nums; color:var(--gc); min-width:2.8em;
  font-size:12.5px; font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.ch{display:flex; gap:14px; align-items:baseline; background:var(--paper);
  border:1px solid var(--rule); border-left:3px solid var(--gc); border-radius:8px;
  padding:13px 16px; text-decoration:none; color:var(--ink)}
.ch:hover{border-color:var(--gc); background:#fff}
.chn{font-variant-numeric:tabular-nums; font-size:15px; font-weight:600; color:var(--gc);
  min-width:1.6em; font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.cht{display:block; min-width:0}
.cht b{display:block; font-size:17px; font-weight:600; margin-bottom:2px}
.cht em{display:block; font-style:normal; color:var(--muted); font-size:14.5px; line-height:1.45}
.cht small{display:block; margin-top:6px; font-size:12px; color:#8a9a90;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.gcard{background:var(--paper); border:1px solid var(--rule); border-radius:10px;
  padding:16px 18px 18px; text-decoration:none; color:var(--ink); display:block;
  border-top:3px solid var(--gc)}
.gcard:hover{border-color:var(--gc)}
.gcard .gn{font-size:11px; font-weight:600; letter-spacing:.08em; color:var(--gc);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.gcard b{display:block; font-size:17.5px; margin:3px 0 5px}
.gcard span{font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:13.5px; color:var(--muted); line-height:1.45; display:block}
.gcard em{font-style:normal; color:var(--gc); font-size:12.5px; display:block; margin-top:10px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.strip{max-width:var(--wide); margin:0 auto; padding:0 28px 10px;
  display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px}
.strip a{display:block; background:var(--paper); border:1px solid var(--rule);
  border-radius:9px; padding:13px 15px; text-decoration:none; color:var(--ink); font-size:14.5px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.strip a:hover{border-color:var(--green)}
.strip a small{display:block; color:var(--muted); font-size:12.5px; margin-top:3px}

/* ---- search results ---- */
#results{margin:6px 0 0; display:none}
#results a{display:block; padding:7px 8px 8px; border-radius:5px; text-decoration:none; color:var(--ink)}
#results a:hover,#results a.on{background:var(--green-tint)}
#results .t{display:block; font-size:13px}
#results .k{font-size:10px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted)}
#results .c{display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
  overflow:hidden; font-size:11.5px; line-height:1.45; color:var(--muted); margin-top:2px}
#results .c b{font-weight:600; color:var(--green); background:var(--green-tint)}
#results .none{padding:6px 8px; font-size:12.5px; color:var(--muted)}

/* ---- mobile ---- */
.bar{display:none; position:sticky; top:0; z-index:20; background:var(--ground);
  border-bottom:1px solid var(--rule); padding:9px 14px; align-items:center; gap:12px}
.bar button{font:inherit; font-size:14px; background:var(--paper); color:var(--ink);
  border:1px solid var(--rule); border-radius:7px; padding:6px 11px; cursor:pointer}
.bar .here{font-size:14px; color:var(--muted); overflow:hidden; white-space:nowrap;
  text-overflow:ellipsis}

@media (max-width:900px){
  body{font-size:17px}
  .frame{grid-template-columns:minmax(0,1fr)}
  .bar{display:flex}
  .rail{position:fixed; inset:47px 0 0; height:auto; width:100%; background:var(--ground);
    border-right:0; display:none; z-index:19; padding:18px 20px 70px}
  .rail.open{display:block}
  .sheet{border-left:0; border-right:0}
  .col{padding:28px 18px 0}
  .col h1{font-size:27px}
  .col h2{font-size:20px}
  .hero{padding:26px 20px 0}
  .hero h1{font-size:31px}
  .hero .lede{font-size:18px}
  .toc,.strip{padding-left:20px; padding-right:20px}
  .parth{font-size:17px}
  .ch{padding:12px 13px; gap:10px}
  .cht b{font-size:16px}
  .cht em{font-size:13.5px}
  .col table{font-size:14px}
  .col th,.col td{padding:6px 7px}
  .mk{font-size:16px; padding:12px 14px}
  .col details > *:not(summary){margin-left:14px; margin-right:14px}
}
@media (prefers-reduced-motion:reduce){*{animation:none !important; transition:none !important}}
@media print{.rail,.bar,.nextprev,.pair{display:none}.frame{display:block}
  .col details{border:0}.col details > *{display:block !important}}
"""

# Raw, because this is JavaScript. Without the r, Python eats the backslashes
# and ships '\b' as a backspace character where the regex needs a word
# boundary, and every search silently returns nothing.
JS = r"""
(function(){
  var q=document.getElementById('q'), r=document.getElementById('results'), idx=null, sel=-1;
  function load(cb){ if(idx){cb();return;}
    fetch(BASE+'search.json').then(function(x){return x.json()}).then(function(d){idx=d;cb()}); }
  function esc(s){return s.replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]})}
  function matcher(t){
    var e=t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    var b=/^\w/.test(t)?'\\b':'', a=/\w$/.test(t)?'\\b':'';
    return new RegExp(b+e+a,'gi');
  }
  function count(hay,re){ re.lastIndex=0; var n=0; while(re.exec(hay)!==null){n++; if(n>9)break;} return n; }
  function snip(body,t,re){
    var i=-1;
    if(re){ re.lastIndex=0; var m=re.exec(body); if(m) i=m.index; }
    if(i<0) i=body.toLowerCase().indexOf(t);
    if(i<0) return '';
    var a=Math.max(0,i-52), b=Math.min(body.length,i+t.length+92);
    if(a>0){ var sp=body.indexOf(' ',a); if(sp>-1&&sp<i) a=sp+1; }
    return (a>0?'… ':'')+esc(body.slice(a,i))+'<b>'+esc(body.slice(i,i+t.length))+'</b>'+
           esc(body.slice(i+t.length,b))+(b<body.length?' …':'');
  }
  function run(){
    var t=q.value.trim().toLowerCase();
    if(t.length<2){r.style.display='none'; r.innerHTML=''; return;}
    load(function(){
      var hits=[], re=matcher(t), loose=t.length>=5;
      for(var i=0;i<idx.length;i++){
        var p=idx[i], s=0, body=p.b||'';
        if(count(p.t,re)) s+=40; else if(loose&&p.t.toLowerCase().indexOf(t)>-1) s+=20;
        if(count(p.h,re)) s+=16; else if(loose&&p.h.toLowerCase().indexOf(t)>-1) s+=8;
        if(count(p.s,re)) s+=8;
        var n=count(body,re);
        if(!n&&loose) n=Math.min(body.toLowerCase().split(t).length-1,3);
        if(n) s+=Math.min(n,6);
        if(s) hits.push([s,p,n?snip(body,t,re):'']);
      }
      hits.sort(function(a,b){return b[0]-a[0]});
      sel=-1;
      if(!hits.length){ r.innerHTML='<div class="none">Nothing matches that.</div>'; r.style.display='block'; return; }
      r.innerHTML=hits.slice(0,10).map(function(h){
        var k=h[1].k&&h[1].k!=='concept' ? '<span class="k">'+esc(h[1].k)+'</span> ' : '';
        return '<a href="'+h[1].u+'">'+k+'<span class="t">'+esc(h[1].t)+'</span>'+
               '<span class="c">'+(h[2]||esc(h[1].s.slice(0,90)))+'</span></a>';
      }).join('');
      r.style.display='block';
    });
  }
  if(q){
    q.addEventListener('input',run);
    q.addEventListener('keydown',function(e){
      var as=r.querySelectorAll('a');
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){
        if(!as.length)return; e.preventDefault();
        if(sel>-1) as[sel].classList.remove('on');
        sel = e.key==='ArrowDown' ? (sel+1)%as.length : (sel<=0?as.length-1:sel-1);
        as[sel].classList.add('on'); as[sel].scrollIntoView({block:'nearest'});
      } else if(e.key==='Enter'&&sel>-1){ e.preventDefault(); as[sel].click(); }
      else if(e.key==='Escape'){ q.value=''; run(); q.blur(); }
    });
    document.addEventListener('keydown',function(e){
      if(e.key==='/'&&document.activeElement!==q&&!/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)){
        e.preventDefault();q.focus();}
    });
  }
  var btn=document.getElementById('menu'), rail=document.getElementById('rail');
  if(btn) btn.addEventListener('click',function(){
    var open=rail.classList.toggle('open');
    btn.setAttribute('aria-expanded',open?'true':'false');
    btn.textContent=open?'Close':'Contents';
    document.body.style.overflow=open?'hidden':'';
  });
  /* Open every reveal panel before printing, so a printed page is complete. */
  window.addEventListener('beforeprint',function(){
    document.querySelectorAll('details').forEach(function(d){d.open=true});
  });
})();
"""


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def rail_html(pages, current, base) -> str:
    """Where you are, how far in, and the one door out.

    This used to be a jump list of every chapter, which meant the site offered
    a menu at every moment and never taught an order. It now shows position and
    the steps of the chapter you are in. Steps you have passed are links,
    because going back to check something is reading. Steps ahead are not,
    because choosing among them is the work the guide is supposed to do for
    you. The table of contents is the one place with free movement.
    """
    seq = [q for q in pages if q["kind"] in ("group", "subject") or q.get("sub")]
    pos = next((i for i, q in enumerate(seq) if q["url"] == current), None)

    out = [
        f'<a class="brand" href="{base}">{esc(SITE_SHORT)}'
        f'<small>a guide that keeps the order</small></a>',
        '<div class="search"><label class="sr" for="q"></label>'
        '<input id="q" type="search" placeholder="Search everything  /" '
        'autocomplete="off" spellcheck="false"><div id="results"></div></div>',
        f'<a class="tocjump" href="{base}">Table of contents</a>',
    ]

    if pos is None:
        out.append('<div class="ext">')
        for label, href in [("Every visual", "gallery/"),
                            ("All coding problems", "indexes/coding.html"),
                            ("Mock interviews", "practice/"),
                            ("How to study", "docs/HOW-TO-USE.html")]:
            out.append(f'<a href="{base}{href}">{label}</a>')
        out.append('<a href="https://github.com/Soulful-Iris/junior-to-staff">Source on GitHub</a></div>')
        return "\n".join(out)

    here = seq[pos]
    gname, gc, _ = GROUPS[here["group"]] if here.get("group") else ("", "#2f6f4e", "")
    total_ch = sum(1 for q in pages if q["kind"] == "subject")
    pct = round((pos + 1) / len(seq) * 100)

    chapter_no = here.get("chapter")
    lines = [f'<div class="where" style="--gc:{gc}">',
             f'<span class="wpart">Part {here["gnum"]} · {esc(gname)}</span>']
    if chapter_no:
        lines.append(f'<span class="wch">Chapter {chapter_no} of {total_ch}</span>')
    lines.append(f'<div class="bar2"><i style="width:{pct}%"></i></div>'
                 f'<span class="wpct">{pct}% through the book</span></div>')
    out.append("".join(lines))

    if chapter_no:
        steps = [q for q in pages if q.get("chapter") == chapter_no and q.get("sub")]
        chead = next(q for q in pages if q["kind"] == "subject" and q["chapter"] == chapter_no)
        done_to = pos
        out.append(f'<div class="stepsh">In chapter {chapter_no}</div><ol class="steps">')
        ci = seq.index(chead)
        cur = ' class="on"' if chead["url"] == current else ""
        out.append(f'<li{cur}><a href="{base.rstrip("/")}{chead["url"]}">'
                   f'<span class="sn">·</span>{esc(chead["title"])}</a></li>')
        for st in steps:
            si = seq.index(st)
            num = f'{chapter_no}.{st["sub"]}'
            if st["url"] == current:
                out.append(f'<li class="on"><span class="sn">{num}</span>{esc(st["title"])}</li>')
            elif si < done_to:
                out.append(f'<li><a href="{base.rstrip("/")}{st["url"]}">'
                           f'<span class="sn">{num}</span>{esc(st["title"])}</a></li>')
            else:
                out.append(f'<li class="notyet"><span class="sn">{num}</span>{esc(st["title"])}</li>')
        out.append("</ol>")

    out.append('<div class="ext">')
    for label, href in [("Every visual", "gallery/"),
                        ("All coding problems", "indexes/coding.html"),
                        ("Mock interviews", "practice/"),
                        ("How to study", "docs/HOW-TO-USE.html")]:
        out.append(f'<a href="{base}{href}">{label}</a>')
    out.append('<a href="https://github.com/Soulful-Iris/junior-to-staff">Source on GitHub</a></div>')
    return "\n".join(out)


def crumb_for(page, pages, base) -> str:
    bits = [f'<a href="{base}">Home</a>']
    if page.get("group"):
        gname, gc, _ = GROUPS[page["group"]]
        gp = next((p for p in pages if p["kind"] == "group" and p["group"] == page["group"]), None)
        if gp and page["kind"] != "group":
            bits.append(f'<a href="{base.rstrip("/")}{gp["url"]}">{esc(gname)}</a>')
    if page.get("subject") and page["kind"] not in ("subject",):
        sp = next((p for p in pages if p["kind"] == "subject"
                   and p["subject"] == page["subject"] and p["group"] == page["group"]), None)
        if sp:
            bits.append(f'<a href="{base.rstrip("/")}{sp["url"]}">{esc(sp["title"])}</a>')
    if page.get("area"):
        bits.append(esc(page["area"]))
    return '<div class="crumb">' + '<span class="dot">·</span>'.join(bits) + "</div>"


def shell(page, body, pages, prev, nxt, base, depth, chips="") -> str:
    gc = GROUPS[page["group"]][1] if page.get("group") else "#2f6f4e"
    tint = {"#1f5b76": "#e9eff3", "#2f6f4e": "#eaf0ec",
            "#a8682f": "#f9efe7", "#6f4a7d": "#f2eef5"}.get(gc, "#eaf0ec")
    up = "../" * depth
    kind, note = KINDS.get(page["kind"], ("", ""))
    badge = (f'<span class="badge b-{kind}">{kind}</span>'
             if kind and kind not in ("concept", "") else "")

    total_ch = sum(1 for q in pages if q["kind"] == "subject")
    if page["kind"] == "group":
        badge = f'<span class="badge b-chapter">Part {page["gnum"]} of {len(GROUPS)}</span>'
        note = ""
    elif page["kind"] == "subject":
        badge = f'<span class="badge b-chapter">Chapter {page["chapter"]} of {total_ch}</span>'
        note = ""
    elif page.get("sub"):
        badge = (f'<span class="badge b-sub">{page["chapter"]}.{page["sub"]}</span>'
                 f'<span class="badge b-{kind}">{kind}</span>')

    kindnote = f'<p class="kindnote">{esc(note)}</p>' if note else ""

    # A chapter lists its own sub-chapters, grouped, so the chapter page is the
    # context and the sub-chapters are the work.
    # A chapter says what is ahead. It does not offer a menu: the order is the
    # guide's job, and a list of links is that job handed back to the reader.
    inchapter = ""
    if page["kind"] == "subject":
        steps = [q for q in pages if q.get("chapter") == page["chapter"] and q.get("sub")]
        if steps:
            counts: dict[str, int] = {}
            for q in steps:
                counts[q["section"]] = counts.get(q["section"], 0) + 1
            bits = " · ".join(f"{v} {k.lower()}" for k, v in counts.items())
            first = steps[0]
            inchapter = (
                f'<section class="ahead">'
                f'<h2>What is ahead</h2>'
                f'<p>{len(steps)} steps in this chapter — {esc(bits)}. '
                f'They come in order; you do not have to choose.</p>'
                f'<a class="begin" href="{base.rstrip("/")}{first["url"]}">'
                f'Begin {page["chapter"]}.1 &middot; {esc(first["title"])}</a>'
                f'</section>')

    def label(q, word):
        if q.get("kind") == "group":
            return f"{word} · part {q['gnum']}"
        if q.get("kind") == "subject":
            return f"{word} · chapter {q['chapter']}"
        if q.get("sub"):
            return f"{word} · {q['chapter']}.{q['sub']}"
        return word

    nav = []
    if prev:
        nav.append(f'<a class="back" href="{base.rstrip("/")}{prev["url"]}">'
                   f'<span>{label(prev, "Back")}</span>{esc(prev["title"])}</a>')
    else:
        nav.append('<span></span>')
    if nxt and page["kind"] != "subject":
        nav.append(f'<a class="fwd" href="{base.rstrip("/")}{nxt["url"]}">'
                   f'<span>{label(nxt, "Next")}</span>{esc(nxt["title"])}</a>')
    elif nxt:
        nav.append('<span></span>')
    else:
        nav.append(f'<a class="fwd" href="{base}">'
                   f'<span>The end</span>Back to the table of contents</a>')

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(page['title'])} · {esc(SITE_SHORT)}</title>
<meta name="description" content="{esc(page['summary'][:180])}">
<meta name="color-scheme" content="light">
<link rel="stylesheet" href="{up}style.css">
<style>:root{{--accent:{gc}; --accent-tint:{tint}}}</style>
</head><body>
<div class="bar"><button id="menu" aria-expanded="false" aria-controls="rail">Contents</button>
<div class="here">{esc(page['title'])}</div></div>
<div class="frame">
<nav class="rail" id="rail" aria-label="Contents">{rail_html(pages, page['url'], base)}</nav>
<div class="main"><div class="sheet"><div class="col">
{crumb_for(page, pages, base)}
{badge}
{kindnote}
{chips}
{body}
{inchapter}
<nav class="nextprev">{''.join(nav)}</nav>
</div></div></div></div>
<script>var BASE="{base}";</script><script src="{up}app.js"></script>
</body></html>
"""


def home_shell(page, body, pages, base) -> str:
    chapters = [p for p in pages if p["kind"] == "subject"]

    def inside(ch):
        leaves = [q for q in pages if q.get("chapter") == ch["chapter"] and q.get("sub")]
        counts: dict[str, int] = {}
        for q in leaves:
            counts[q["section"]] = counts.get(q["section"], 0) + 1
        def name(k, v):
            label = k.lower()
            return f"{v} {label if v != 1 else label.rstrip('s')}"
        return " · ".join(name(k, v) for k, v in counts.items())

    toc = []
    for gi, (gdir, (gname, gc, gblurb)) in enumerate(GROUPS.items(), 1):
        gp = next((q for q in pages if q["kind"] == "group" and q["group"] == gdir), None)
        if not gp:
            continue
        chs = [c for c in chapters if c["group"] == gdir]
        span = (f"Chapters {chs[0]['chapter']}\u2013{chs[-1]['chapter']}"
                if len(chs) > 1 else f"Chapter {chs[0]['chapter']}") if chs else ""
        toc.append(
            f'<section class="partblock" style="--gc:{gc}">'
            f'<h2 class="parth"><span class="pnum">Part {gi}</span>'
            f'<a href="{base.rstrip("/")}{gp["url"]}">{esc(gname)}</a></h2>'
            f'<p class="partb">{esc(gblurb)}</p>'
            f'<p class="partspan">{span} &middot; '
            f'<a href="{base.rstrip("/")}{gp["url"]}">read the part introduction</a></p>'
            f'<div class="chlist">')
        for ch in chs:
            steps = [q for q in pages if q.get("chapter") == ch["chapter"] and q.get("sub")]
            rows, last = [], None
            for st in steps:
                if st["section"] != last:
                    last = st["section"]
                    rows.append(f'<li class="secl">{esc(last)}</li>')
                rows.append(
                    f'<li><a href="{base.rstrip("/")}{st["url"]}">'
                    f'<span class="sn">{ch["chapter"]}.{st["sub"]}</span>'
                    f'{esc(st["title"])}</a></li>')
            toc.append(
                f'<div class="chwrap">'
                f'<a class="ch" href="{base.rstrip("/")}{ch["url"]}">'
                f'<span class="chn">Chapter<b>{ch["chapter"]}</b></span>'
                f'<span class="cht"><b>{esc(ch["title"])}</b>'
                f'<em>{esc(ch["blurb"])}</em>'
                f'<small>{inside(ch)}</small></span></a>'
                + (f'<details class="steps-d"><summary>{len(steps)} steps</summary>'
                   f'<ol class="tsteps">{"".join(rows)}</ol></details>' if steps else "")
                + '</div>')
        toc.append("</div></section>")

    first = next((q for q in pages if q["kind"] == "group"), None)
    startlink = (f'<a class="start" href="{base.rstrip("/")}{first["url"]}">'
                 f'Start reading</a>') if first else ""

    strip = []
    for label, sub, href in [
        ("Every visual", "478 diagrams, each linked to its lesson", "gallery/"),
        ("Coding problems", "42 with solutions and tests", "indexes/coding.html"),
        ("System designs", "requirements, diagrams, follow-ups", "indexes/system-designs.html"),
        ("Mock interviews", "candidate and assessor packs", "practice/"),
        ("Production cases", "five real incidents", "indexes/production-cases.html"),
        ("How to study", "the method, in one page", "docs/HOW-TO-USE.html"),
    ]:
        strip.append(f'<a href="{base}{href}">{label}<small>{sub}</small></a>')

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(SITE_TITLE)}</title>
<meta name="description" content="{esc(SITE_LEDE)}">
<meta name="color-scheme" content="light">
<link rel="stylesheet" href="style.css">
</head><body>
<div class="bar"><button id="menu" aria-expanded="false" aria-controls="rail">Contents</button>
<div class="here">{esc(SITE_SHORT)}</div></div>
<div class="frame">
<nav class="rail" id="rail" aria-label="Curriculum">{rail_html(pages, '/', base)}</nav>
<div class="main"><div class="sheet">
<header class="hero">
<h1>{esc(SITE_TITLE)}</h1>
<p class="lede">{esc(SITE_LEDE)}</p>
<div class="how"><b>How each concept is taught</b>
Situation, then the contract it has to satisfy, then a diagram of the mechanism,
then your implementation and its checks. Then the requirement changes, and the
follow-up questions go deeper. The depth lives inside the question rather than
in a separate chapter, which is why there is no ladder to climb here — just one
problem you keep being asked harder things about.</div>
<div class="mer heroimg"><img src="{base}assets/diagrams/same-problem-three-depths.svg"
 alt="One problem, a bookmark service, answered at three depths: foundation, then
 operating constraints, then broader ownership, each adding to the same answer"></div>
{startlink}
</header>
<section class="strip">{''.join(strip)}</section>
<section class="toc"><h2 class="toch">Contents</h2>{''.join(toc)}</section>
<div class="col">{body}</div>
</div></div></div>
<script>var BASE="{base}";</script><script src="app.js"></script>
</body></html>
"""



# ------------------------------------------------------------------- gallery

def gallery_page(pages, have, base) -> str:
    """Every visual in the curriculum, grouped, each linking to its lesson.

    The repo's own visuals index is a table of "View" links and shows no
    pictures at all, which is an odd thing for a page about pictures. This one
    is generated from what the pages actually reference, so it cannot list a
    diagram that is not used or miss one that is — and every thumbnail goes to
    the lesson rather than to the bare SVG, because a diagram out of its
    argument is decoration.
    """
    IMG = re.compile(r"!\[[^\]]*\]\(([^)]+\.svg)\)")
    buckets: dict[str, list] = {}
    seen_pairs = set()

    for p in pages:
        gkey = p.get("group") or "_other"
        label = GROUPS[gkey][0] if gkey in GROUPS else "Reference and practice"
        colour = GROUPS[gkey][1] if gkey in GROUPS else "#6d6459"
        depth = len(Path(dest_for(p["src"])).parts) - 1

        assets = []
        for m in IMG.finditer(p["text"]):
            src = m.group(1)
            resolved = os.path.normpath(os.path.join(os.path.dirname(p["src"]), src))
            assets.append(resolved.replace(os.sep, "/"))
        for m in MERMAID_RE.finditer(p["text"]):
            h = hashlib.sha256(m.group(1).strip().encode()).hexdigest()[:16]
            if h in have:
                assets.append(f"assets/mermaid/{h}.svg")

        for a in assets:
            key = (a, p["url"])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            buckets.setdefault(label, (colour, []))[1].append((a, p))

    order = [GROUPS[g][0] for g in GROUPS] + ["Reference and practice"]
    sections = []
    total = 0
    for label in order:
        if label not in buckets:
            continue
        colour, items = buckets[label]
        total += len(items)
        cards = "".join(
            f'<a class="gcell" href="{base.rstrip("/")}{pg["url"]}" title="{esc(pg["title"])}">'
            f'<img src="{base}{a}" loading="lazy" alt="">'
            f'<span>{esc(pg["title"])}</span></a>'
            for a, pg in items)
        sections.append(
            f'<h2 style="--accent:{colour}">{esc(label)} '
            f'<small>{len(items)}</small></h2><div class="grid">{cards}</div>')

    body = (f'<h1>Every visual</h1><p class="lede">{total} diagrams across the '
            f'curriculum, in reading order. Each one links to the lesson it '
            f'belongs to rather than to the file, because a diagram out of its '
            f'argument is decoration.</p>' + "".join(sections))

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Every visual · {esc(SITE_SHORT)}</title>
<meta name="description" content="{total} diagrams across the curriculum, each linked to its lesson.">
<meta name="color-scheme" content="light">
<link rel="stylesheet" href="{base}style.css">
<style>
.col{{max-width:1180px}}
.lede{{color:var(--muted); font-size:17px; max-width:var(--measure)}}
.col h2{{border-bottom:2px solid var(--accent); color:var(--ink)}}
.col h2 small{{font:12px ui-monospace,monospace; color:var(--muted); font-weight:400}}
.grid{{display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:14px; margin:18px 0 42px}}
.gcell{{display:block; background:var(--paper); border:1px solid var(--rule); border-radius:9px;
  padding:11px; text-decoration:none; color:var(--ink); overflow:hidden}}
.gcell:hover{{border-color:var(--accent)}}
.gcell img{{width:100%; height:120px; object-fit:contain; object-position:center; display:block}}
.gcell span{{display:block; font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:12px; color:var(--muted); margin-top:9px; line-height:1.35;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden}}
@media (max-width:900px){{.grid{{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}
  .gcell img{{height:90px}}}}
</style>
</head><body>
<div class="bar"><button id="menu" aria-expanded="false" aria-controls="rail">Contents</button>
<div class="here">Every visual</div></div>
<div class="frame">
<nav class="rail" id="rail" aria-label="Curriculum">{rail_html(pages, '/gallery/', base)}</nav>
<div class="main"><div class="sheet"><div class="col">
<div class="crumb"><a href="{base}">Home</a></div>
{body}
</div></div></div></div>
<script>var BASE="{base}";</script><script src="{base}app.js"></script>
</body></html>
"""


def main() -> int:
    base = os.environ.get("SITE_BASE", "/")
    CHAPTER_BLURBS.update(chapter_blurbs())
    pages = collect()
    print(f"collected {len(pages)} pages")

    blocks = mermaid_blocks(pages)
    print(f"mermaid: {len(blocks)} unique diagrams")
    have = render_mermaid(blocks)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / "assets" / "mermaid").mkdir(parents=True, exist_ok=True)
    for h in have:
        shutil.copy(MERMAID_CACHE / f"{h}.svg", OUT / "assets" / "mermaid" / f"{h}.svg")
    shutil.copytree(Path(__file__).resolve().parent / "fonts", OUT / "fonts")
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "app.js").write_text(JS, encoding="utf-8")

    # Everything the lessons link to that is not markdown: solutions, tests,
    # fixtures, diffs, logs. An unresolvable link to a fixture is the same
    # broken experience as an unresolvable link to a page.
    copied = 0
    for f in ROOT.rglob("*"):
        if not f.is_file() or f.suffix == ".md":
            continue
        rel = f.relative_to(ROOT)
        if rel.parts[0] in (".git", "site", "node_modules", "assets"):
            continue
        (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, OUT / rel)
        copied += 1

    # Some pages link to an asset DIRECTORY. Give those a real index instead of
    # a 404, since the whole point of the gallery is browsing it.
    for d in (OUT / "assets").rglob("*"):
        if not d.is_dir() or (d / "index.html").exists():
            continue
        items = sorted(x for x in d.iterdir() if x.is_file() and x.suffix in (".svg", ".png"))
        if not items:
            continue
        rows = "".join(
            f'<figure><a href="{x.name}"><img src="{x.name}" loading="lazy" alt=""></a>'
            f'<figcaption>{x.stem}</figcaption></figure>' for x in items)
        (d / "index.html").write_text(
            f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{d.name} · {SITE_SHORT}</title>'
            f'<link rel="stylesheet" href="{"../" * len(d.relative_to(OUT).parts)}style.css">'
            f'<style>body{{padding:28px}}main{{display:grid;'
            f'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;max-width:1100px}}'
            f'figure{{margin:0;background:var(--paper);border:1px solid var(--rule);'
            f'border-radius:9px;padding:12px;overflow:hidden}}'
            f'figure img{{width:100%;height:auto}}'
            f'figcaption{{font:12px ui-monospace,monospace;color:var(--muted);margin-top:8px}}'
            f'</style></head><body><h1>{d.name}</h1><main>{rows}</main></body></html>',
            encoding="utf-8")

    index = []
    for i, p in enumerate(pages):
        if p["kind"] == "subject":
            p["text"] = strip_chapter_menus(p["text"])
        rel = dest_for(p["src"])
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        depth = len(Path(rel).parts) - 1
        body, toc = render_body(p["text"], have, depth)
        body, chips = lift_crumb(body, p)

        prev = pages[i - 1] if i > 0 else None
        nxt = pages[i + 1] if i < len(pages) - 1 else None

        if p["kind"] == "home":
            body = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", body, count=1, flags=re.S)
            html = home_shell(p, body, pages, base)
        else:
            html = shell(p, body, pages, prev, nxt, base, depth, chips)
        dest.write_text(html, encoding="utf-8")

        index.append({"t": p["title"], "u": base.rstrip("/") + p["url"],
                      "k": KINDS.get(p["kind"], ("", ""))[0],
                      "s": p["summary"][:200],
                      "h": " ".join(toc),
                      "b": prose_of(p["text"])})

    (OUT / "gallery").mkdir(parents=True, exist_ok=True)
    (OUT / "gallery" / "index.html").write_text(gallery_page(pages, have, base), encoding="utf-8")

    (OUT / "search.json").write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    print(f"built {len(pages)} pages, {len(have)} diagrams, {copied} code files -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
