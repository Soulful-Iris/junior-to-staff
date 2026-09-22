# Guided reader verification

The redesign targets `site/concept-first` and incorporates the branch's automatic-deployment update. Curriculum Markdown, supplied code, project specifications, research and original visual assets are preserved.

## Learning experience

- Four parts and all 17 chapters are available in the left contents on every page. Expanding a chapter reveals its learning sections and ordered steps. The current lesson exposes its own heading hierarchy.
- Homepage → part introduction → chapter introduction → lessons, exercises, projects and assessment form one sequence. Previous and Next agree at every boundary.
- Coding refreshers immediately precede relevant problems. All 42 coding bundles and all five continuing-project stages are in the guided sequence.
- Full reference implementations and tests appear inside their lesson. Reference disclosures protect independent attempts; subsection navigation can reveal a requested explanation in place.
- Ordinary lesson-to-lesson links are removed from the article surface. Jumping and searching happen in the left contents; external evidence remains in Sources.
- Original animated SVGs and box diagrams retain their teaching context. Motion controls, static alternatives and fit/natural-size controls support different reading needs.

## Executed checks

`site/check_reading.py` verifies every generated content page, not a sample: 239 pages, four parts, 17 chapter branches, 185 contiguous guided steps, every coding problem and project stage, current-heading anchors, and no in-body lesson-navigation links. It compares all 123 embedded files against their source text, verifies all 107 original SVG byte hashes, and checks that all 387 Mermaid diagrams are displayed. Assessor keys are excluded from the automatic sequence.

`site/check.py` verifies local links and images in the generated output. The bookmark exercise's standalone `web/index.html` is a copied lab resource rather than a curriculum page; it is intentionally not an extra lesson in the reader.

The 12 Chromium scenarios cover: homepage hierarchy; primer/problem continuity; inline implementation/test references; opening a hidden subsection in place; Previous/Next and resume state; contents search; saved manual motion preference; desktop contents visibility and overflow; mobile drawer focus/Escape; mobile code/table/diagram containment; system reduced motion; unavailable local storage; and uncaught JavaScript errors. Several related assertions run within the same scenario. Desktop and 390px-wide mobile screenshots were inspected, including the homepage, worked coding explanation, backend lesson, AI lesson and mobile contents drawer.

The staged-output build and checks are exercised independently of the live output path. Shell syntax is checked for the deployment script. The original content tests were not rerun because curriculum implementations were unchanged.

## Limits

The browser checks use Chromium; cross-browser and full screen-reader testing are not claimed. Older animations' derived resting views are static diagrams, not sampled full animation timelines. Live publication is performed by the existing server-side deployment timer; pushing a commit does not by itself prove that the server completed deployment. No AWS resources or PostgreSQL servers are deployed by this redesign.

## Deployed styling regression

Mobile screenshots reported after deployment showed the new reader markup without its matching layout CSS: an exposed skip link, an inline contents tree, and overflowing diagrams. Live HTML/asset requests from the development environment returned 403, so the precise server/cache response could not be confirmed.

The fix binds CSS and JavaScript filenames to SHA-256 content hashes and supplies integrity attributes. Every generated HTML page also embeds its exact release stylesheet, with font URLs rooted correctly for nested lessons. This prevents missing or mismatched external CSS from stripping the layout. The server declares CSS/JavaScript MIME types explicitly and gives immutable caching only to the fingerprinted files. Ordinary HTML continues to require revalidation.

The acceptance checker verifies stylesheet and script hashes, integrity values and the embedded stylesheet on every content page. The browser suite now has **15 passing scenarios**, including explicit MIME/cache checks, blocked external CSS, and an injected stale stylesheet. The negative control removes the embedded stylesheet and reproduces the unpositioned contents tree and visible skip link; the fixed page remains styled. These checks reproduce the failure mode locally, not a verified diagnosis of the inaccessible production cache.

## Sticky navigation follow-up

Previous and Next remain inside the existing sticky header. On mobile, the top bar identifies the current lesson and its chapter/step while scrolling. The final lesson includes a sticky Finish button; both completion buttons stay synchronized and reflect saved completion on reload.

The suite now passes **17 browser scenarios**. Added checks exercise pinned navigation at 320px, 390px, 768px and 1440px, agreement with bottom destinations, progress from sticky Next, and synchronized final-step completion after reload. Mobile screenshots of a scrolled coding lesson and the completed final lesson were inspected. The structural check additionally verifies sticky destinations across the entire sequence; all 60,072 built links resolve. Production deployment and Safari remain outside these local checks.
