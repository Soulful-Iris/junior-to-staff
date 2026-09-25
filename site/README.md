# The Engineering Guide

The site presents the existing curriculum as a guided book. Its homepage gives newcomers a short sample lesson and direct links into the five core parts. The complete searchable curriculum stays one click away in a Browse curriculum drawer. Lesson pages keep the persistent left-hand contents, including 18 chapters, an optional AI systems specialization, an elective company interview studio, and the current lesson's subsections. Every lesson has Previous/Next navigation.

## Build and check

Python 3.12+, Node 22.16.0, and Chromium are required for a fresh build. Install the declared tooling in a virtual environment and the local Node tooling directory:

```bash
python3.12 -m venv /tmp/engineering-guide-venv
/tmp/engineering-guide-venv/bin/python -m pip install --require-hashes -r site/requirements.lock
npm ci --prefix site/tools --ignore-scripts --no-audit --no-fund
# Use an existing Chromium executable, or install one with Playwright:
cd site/tools
npx playwright install chromium
cd ../..

/tmp/engineering-guide-venv/bin/python site/build.py
/tmp/engineering-guide-venv/bin/python site/check.py
/tmp/engineering-guide-venv/bin/python site/serve.py
```

The preview serves at `http://127.0.0.1:8901`. Set `CHROME_PATH` if Chromium lives outside the standard Playwright cache. If required system libraries are unavailable, install them for that browser before rendering. The build refuses to publish missing diagrams. `SITE_OUT` selects a staging directory; the default is `site/out/`. Generated output, browser binaries and tooling dependencies are not committed.

With a browser available, run the interaction checks:

```bash
CHROME_PATH=/path/to/chromium node site/tools/browser-check.mjs
```

The browser script starts and stops its own local server. `SITE_SCREENSHOTS` selects a directory for review images; otherwise it uses a temporary directory.

## Reading sequence and content

- `build.py` maps stable source URLs into five core parts and an optional specialization. `course.py` orders lessons inside that map. The 23 foundations lessons precede coding practice, followed by AI-assisted change work. Scale and capacity sit beside system design; infrastructure, delivery, observability, and reliability form the production sequence. The five reading-list stages appear in their relevant chapters. Candidate exercises follow the relevant material; assessor keys stay outside the automatic sequence.
- `companies/` is an eight-page senior interview studio after the core sequence: a qualitative room guide, six company rehearsals, and a CrowdStrike study companion, each with eight original coding drills, five design prompts, a worked mock, source/uncertainty labels, a distinct motion study, and before/after box diagrams. Drill summaries are prompts, not additions to the 42 fully worked and tested coding bundles.
- `reader.py` composes the content and interface. Code and test files are displayed beside their references. References outside a protected answer are placed in an inline disclosure; existing answer disclosures stay closed until the learner opens them. Ordinary cross-links become contextual text, while their full documents remain in the sequence or reference shelf. External citations appear under Sources at the end of the lesson.
- `build.py` retains Markdown parsing, heading generation and cached Mermaid rendering. Original Markdown, code and visual assets remain untouched.
- `style.css` and `app.js` provide the reading layout, nested contents, mobile drawer, subsection navigation, search, local progress, copy-code controls and diagram sizing/motion controls.

The current build publishes **333 pages**, **250 guided steps** and **311 Mermaid diagrams**, plus a separate visual reference. All **42 fully worked coding problems** and existing project/design briefs remain available at their stable URLs. Referenced code and fixture files are embedded at their point of use. Indexes and repository notes remain available under the reference shelf; they are not extra reading choices between lessons.

Progress is stored on the current device. Visiting a page saves a resume location; following Next marks the current step complete. Completion records practice, not mastery. Reading and navigation continue if local storage is unavailable.

Previous and Next remain pinned above each lesson on desktop and mobile, with the same destinations as the bottom controls. They are intentionally absent from the curriculum overview. The mobile header retains the current lesson title and chapter/step while scrolling. On the final lesson, either Finish control marks completion; both controls reflect the saved state when revisiting.

## Visuals and accessibility

Mermaid is rendered to SVG before publication and cached by source hash. Wide diagrams and tables scroll within the reading column. Readers can fit a diagram to the column or keep its natural size. Authored animation/still pairs are used where supplied. Older animations receive derived resting views that preserve their original boxes and labels; original assets are never overwritten. The motion preference is retained locally and respects the system's reduced-motion setting.

The mobile contents drawer supports Escape, focus containment and return to its opening button. Heading navigation opens an enclosing solution disclosure before moving to the heading. Search stays inside the contents panel. The browser checks exercise these behaviors; they are not a full assistive-technology certification.

## Deployment

`deploy.sh` preserves the existing automatic deployment job. It builds main into a staging directory and publishes after the build succeeds. Content/link checks are manual and do not block publication. Existing output directories are adopted automatically. It installs the pinned Python requirements into a dedicated virtual environment and the declared Node tools when their manifests change. A failed build remains retryable even after the checkout advances to the new commit. Existing notification behavior is preserved.

See [redesign verification](REDESIGN.md) for the completed checks and their limits.

## Release assets

Generated pages use `reader-css.<content-hash>.css` and `reader-js.<content-hash>.js` with integrity attributes. The matching stylesheet is also embedded in each page, so stale or unavailable external CSS cannot strip the reading layout. Font URLs in this embedded copy are rooted at `SITE_BASE`. The build writes `reader-assets.json`; the acceptance check verifies it against every generated content page. The mobile browser suite includes stale-stylesheet and missing-stylesheet regressions.

## Foundations and practice presentation

The foundations chapter has five sections and 23 lessons, including 14 native SVG diagrams generated by `scripts/render-foundations.py`. The next chapter applies these tools to complete coding problems. Existing problem URLs are preserved. Stateful and concurrency exercises stay with their system concepts.

Every coding problem and project brief has a highlighted prompt. Input/expected-result scenarios render as paired cards, stacked on mobile; contract, trace, and comparison tables retain their column relationships. Canonical Markdown keeps ordinary tables for GitHub. Shared-tool explanations remain available in closed optional refreshers rather than interrupting each problem.

The design-practice expansion adds twelve constructed architecture problems placed after their prerequisite lessons and 32 authored SVGs: before/after architectures, failure timelines, and eight deeper visuals with concurrency, workload arithmetic, access decisions, or durability boundaries. The [dated research note](../docs/research/system-design-practice-2026.md) distinguishes anonymous interview reports, published engineering work, and invented exercise assumptions.
