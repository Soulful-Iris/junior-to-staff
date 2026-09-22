# Maintain the visuals

```bash
python scripts/render_visuals.py
python scripts/check_learning.py
```

The original drawings in `assets/diagrams` are the style reference. `render_visuals.py` draws each added mechanism separately: a moving array window, a frontier graph, a recency list, a retry tree, a task fleet, a request timeline, and other concrete structures.

Each diagram has native SVG animation and a static alternative. The root SVG includes an accessible title and description. Reduced-motion and print styles display the static version. No JavaScript, external fonts, or hosted player is needed. Native SVG animation follows the approach used by the original branch.

To export all four checkpoint SVGs for layout review:

```bash
python scripts/render_visuals.py --frames /tmp/learning-frames
```

`assets/learning/manifest.json` indexes the generated diagrams. Static rendering is not proof of animation playback. Check published Markdown as well as standalone SVGs; record the result in [validation](../paths/interviews/VALIDATION.md).

`check_learning.py` validates local links, disclosures, SVG metadata/timelines, and key lab settings. It does not test remote URLs, deployed AWS behavior, or the truth of an architectural claim.
