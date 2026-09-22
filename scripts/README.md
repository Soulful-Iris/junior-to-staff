# Maintain the visuals

```bash
python scripts/render_visuals.py
python scripts/check_learning.py
```

Use [the visual gallery](../assets/learning/README.md) to review the complete set.

For a gallery/manifest refresh that preserves every SVG, run
`python scripts/render_visuals.py --metadata-only`. The four coding studies
registered in `HAND_AUTHORED_SPECS` are maintained directly; both renderer modes
preserve their animated and still files. The default mode regenerates only the
older studies in `SPECS`. Keep each hand-authored pair present when updating metadata.

The references are `assets/the-arc.svg`, `assets/diagrams/change-loop.svg`, and `assets/diagrams/request-lifecycle.svg`: a persistent drawing, purposeful motion, restrained colors, and labels that remain readable.

- Move the thing the lesson is about: a node, request, frontier, boundary, or capacity budget.
- Give each mechanism its own timeline. A transfer takes time; a state update happens at its destination. Do not rotate paragraphs or use a shared slideshow clock.
- Use `animateMotion` for path traversal; interpolate numeric geometry for resizing. Ease pointer changes; keep traffic motion linear. Fixed ghost positions may explain a node's origin, but must be identified.
- Keep the entire causal relationship visible. Use a static comparison when simultaneity matters. Movement must add information beyond a color change.
- Keep timing illustrative and label loop resets that could be mistaken for algorithm behavior.
- Preserve SVG title/description, a readable `-still.svg`, reduced-motion and print fallbacks. No JavaScript, external fonts, or player is required in the README.

Logical register changes are instantaneous: `b.next` must change when the moving
reference arrives, rather than crossfade between two targets. A local native
`animate` may therefore use `calcMode="discrete"` only with
`data-state-update="true"` for opacity, visibility, or fill. The checker limits
its owner to four drawing primitives and two short labels, rejects whole-scene
containers/embedded scenes, and requires accompanying continuous `animateMotion`
or `animateTransform`. Discrete geometry and unmarked discrete updates remain
errors. This narrow structural exception does not prove the timing: inspect
Chromium frames before, during, and after arrival. It does not permit slideshow
scene swaps or rotating explanatory paragraphs.

Technique coverage now includes clipped queue reservoirs, clipped request waterfalls, path drawing, rotating circuit contacts, radial refill meters, moving list nodes, and changing traffic widths. These techniques encode capacity, time, ownership, or event order; decoration alone is not a reason to animate.

References: [clipping](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/clipPath), [transform animation](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/animateTransform), [path drawing](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/stroke-dashoffset), [SVG image restrictions](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image), [SVG motion paths](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/animateMotion), [spline interpolation](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/keySplines). Figma's motion workflow also distinguishes a resting screenshot from animation verification; neither XML validation nor static rendering proves playback.

`check_learning.py` checks links, disclosures, native motion timelines, easing, and lab settings. Inspect the published SVGs and Markdown at multiple times; record what was actually checked in [validation](../paths/interviews/VALIDATION.md). Check event order, intermediate geometry, readable labels, reset behavior, and static alternatives. Tests do not validate deployed AWS behavior or architectural claims.


## Render Markdown diagrams

`render_mermaid.cjs` extracts Mermaid blocks, renders them in Chromium, and saves
an image plus source location for every diagram. Inspect the images after a
successful run: parsing alone misses unreadable text and misleading geometry.

Install the tooling outside the learning examples, then use its module path:

```bash
npm install --prefix ../diagram-tools mermaid playwright
node ../diagram-tools/node_modules/playwright/cli.js install chromium
NODE_PATH=../diagram-tools/node_modules node scripts/render_mermaid.cjs ../diagram-review
```

Pass selected Markdown paths after the output directory to review a checkpoint.
`BROWSER_EXECUTABLE_PATH` can select an already installed browser. For an
npm-packaged Chromium environment, `USE_PACKAGED_CHROMIUM=1` uses the optional
`@sparticuz/chromium` dependency. Ensure the browser can find real fonts; blank
text is a failed review even if the SVG parser succeeded. Repository diagrams
use common Markdown/Mermaid syntax; GitHub's renderer may use a different version,
so also inspect the published pages when confirming a checkpoint.
