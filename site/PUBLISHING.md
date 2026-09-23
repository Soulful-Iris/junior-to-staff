# Static-site publication contract

The build and both content checks run in a unique staging directory. Publication
moves that complete directory into `.releases/`, then replaces the `out` symlink
in one same-filesystem operation. The previous release is not deleted. A failed
post-switch check restores the old pointer; `last-deployed` advances only after
successful publication. A deployment lock covers fetch, build and publication.

```text
out -> .releases/old       stage/new is checked
out -> .releases/new       one pointer replacement
.releases/old remains      delayed requests can fetch old hashed assets
```

This is POSIX process-failure handling, not a tested power-loss guarantee.
`serve.py` reads the live path for requests and falls back to retained releases
only for fingerprinted reader scripts/styles and Mermaid SVGs. It does not serve
retired HTML as a fallback. Unversioned assets still use their documented cache
policy. The full browser, proxy and host deployment remain separate checks.

## Existing installations

An existing real `site/out` directory is **left untouched** and publication is
refused. Do not delete it to make the deploy pass. The operator must schedule a
one-time layout migration: retain it as `.releases/legacy`, create `out` as a
relative symlink to that retained directory, verify its pages, and restart the
static server with the updated serving code. The legacy directory-to-symlink
conversion is not an atomic live switch; perform it under a maintenance window
or route traffic to an unchanged instance. Ordinary releases after that use the
atomic pointer protocol. No migration is run by the test suite.

## Retention and dependencies

No automatic release cleanup runs. Set an explicit old-client support window
before implementing garbage collection; removing an old asset ends that window
for an uncached old tab. Preserve the active release and rollback target, and
monitor disk usage. Retention is deliberate, not a claim of unlimited disk.

**Open dependency gate (SITE-05):** direct Node versions are pinned, but a reviewed
transitive `package-lock.json` is not yet committed. The existing install policy
is retained rather than pretending that a lock was generated or introducing an
unconditionally failing `npm ci`. Do not call this a fully reproducible website
release until the lock is reviewed, committed, and enforced with `npm ci`.
Python pins likewise do not establish hash-locked transitive reproducibility.

## Reproduce the focused tests

```bash
python -m unittest discover -s site/tests -p test_publish.py -v
python -m unittest discover -s site/tests -p test_retained_assets.py -v
# Requires Python Playwright and Chromium (or its installed Playwright browser):
python -m unittest discover -s site/tests -p test_reader_storage.py -v
bash -n site/deploy.sh
```

Publication tests inject failures only in temporary directories. The HTTP test
loads old HTML, switches releases, then fetches its uncached old script and
checks exact bytes. The preference tests run the real reader script in Chromium
with controlled Storage responses; they do not prove cross-reload persistence.
