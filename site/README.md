# The website

The guide reads fine on GitHub. This turns the same markdown into something
you can search, page through, and read on a phone.

Live at **[guide.soulful-ai.dev](https://guide.soulful-ai.dev)**.

```bash
python3 site/build.py      # markdown -> site/out/  (43 pages)
python3 site/serve.py      # http://127.0.0.1:8901
```

No build step beyond Python and the `markdown` package. No JavaScript
framework, no node_modules, nothing to keep patched.

## Two decisions worth knowing about

**The output mirrors the repo tree.** `tiers/01-junior/06-testing/README.md`
becomes `tiers/01-junior/06-testing/index.html`. That is not tidiness. It means
every relative link already written in the markdown resolves without being
rewritten, so the site and GitHub cannot drift apart — there is no link-rewriting
step to get subtly wrong.

**The search index carries the prose, not just the titles.** A 105,000-word
guide where search only matches headings is a table of contents with extra
steps. `search.json` is 490 KB and is fetched on the first keystroke, not on
page load, so it costs nothing until you use it. Matching prefers whole words:
without that, `rds` scores 32 pages because it is inside *words* and *records*,
and the two pages actually about RDS are buried.

## The site is not committed

`site/out/` is gitignored. It is generated, so a committed copy would be a
second source of truth that goes stale the first time someone edits a section
and forgets to rebuild.

## Running it as a service

`units/j2s-site.service` is a systemd user unit — `Restart=always`, static
files only, bound to localhost. Nothing here can lose data; the worst failure is
a dead bookmark.

```bash
cp units/j2s-site.service ~/.config/systemd/user/
systemctl --user enable --now j2s-site.service
```

## Changing how it looks

The CSS and JS live inside `build.py` as two string constants, `CSS` and `JS`.
One file, one build, no asset pipeline.

`JS` is a **raw** string. It has to be: without the `r`, Python eats the
backslashes and the word-boundary `\b` in the search regex ships as `\b` — the
backspace character — and every search silently returns nothing. It looks
identical in the source and it is completely broken. Test the built file, not
the algorithm.
