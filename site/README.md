# The site

Builds the curriculum into a static site. Live at
**[guide.soulful-ai.dev](https://guide.soulful-ai.dev)**.

```bash
python3.12 site/build.py    # markdown -> site/out/  (239 pages, 387 diagrams)
python3.12 site/check.py    # resolve every link in the BUILT output
python3.12 site/serve.py    # http://127.0.0.1:8901
```

No framework, no client-side rendering, nothing to keep patched. Python plus
the `markdown` package, and Node only for the one-off mermaid render.

## The four things worth knowing

**Mermaid is pre-rendered.** `tools/render-mermaid.mjs` loads mermaid once in a
headless browser and renders all 387 diagrams in about thirty seconds, themed to
the house palette, cached by content hash so a rebuild costs nothing. Diagrams
are emitted at natural size rather than scaled to fit: scaling a wide flowchart
down to the text column shrinks its labels past legibility, so the wide ones
scroll instead, with a CSS scroll shadow so you can tell.

**`<details>` needs `markdown="1"` injected.** Without it the 197 collapsible
solutions render their insides as raw markdown — tables as pipes, emphasis as
asterisks — and the build log looks completely fine.

**Links are rewritten, and the checker reads the built pages.** The curriculum
links to `.md` files, which is correct on GitHub and dead on a website: there
were 1,421 of them. The mirrored output tree means the rewrite is one mechanical
rule with no lookups, so a link cannot drift from where its file landed.
`check.py` walks `site/out` rather than the markdown, because a source-level
checker passes a build with 1,421 dead links in it. It has a negative control:
break a link and it goes red.

**The curriculum's own vocabulary carries the teaching.** `Changed requirement`,
`Follow-up N`, `Senior expectation`, `Invariant`, `Redraw challenge` are styled
as marked blocks rather than left as bold paragraphs, because they are the part
a reader is here for. 279 of them across the site.

## Colour

Green is the base throughout. Each of the four parts has an accent used only as
an identity mark — the nav chip, the active item, the page's quote rule — never
as a theme, so the site reads as one thing. Colour is always redundant with a
number and a name, never the only channel.

## Changing the name

`SITE_TITLE`, `SITE_SHORT` and `SITE_LEDE` at the top of `build.py`. One place.
