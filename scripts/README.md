# Maintain the learning material

From the repository root:

```bash
python scripts/render_learning.py
python scripts/render_mechanisms.py
python scripts/check_learning.py
```

`learning_storyboards.json` is the editable narrative source for the 21 chapter walkthroughs and six shared interview concepts. Each entry has four before/after states, actors, a four-message implementation trace, and a prediction question. The generator emits two animated SVGs and one static storyboard per entry. `render_mechanisms.py` adds three geometric animations for a sliding window, cache fan-out, and bounded workers.

SVGs use local CSS animation with a 16-second teaching cycle. Reduced-motion preference selects a static final state; linked storyboards retain all four states. No JavaScript, external fonts, remote image services, or hosted player is required. Preview in your target Markdown renderer after changes because animation support varies.

`check_learning.py` checks local Markdown paths, accessible SVG metadata, chapter integration, and key lab configuration invariants. It does not validate remote URLs or prove cloud deployment behavior. Run the Python and TypeScript tests listed in [the interview entry point](../paths/interviews/README.md) after code changes.

Optional deeper checks: TypeScript `tsc --noEmit --strict` with Node types and `allowImportingTsExtensions`; `cfn-lint` for the SAM template. Record results and limitations in [validation](../paths/interviews/VALIDATION.md).
