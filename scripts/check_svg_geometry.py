#!/usr/bin/env python3.12
"""Measure rendered SVG geometry and report clipping and overlap.

Why this exists rather than looking at each picture: on 2026-09-26 seven
diagrams had defects that are invisible in the source and obvious in the
render -- caption lines running past the canvas and being silently cut, labels
sitting on their own bars, a headline number drawn over a chart column. Reading
the file cannot find those. This asks the browser where the glyphs actually
landed.

CLIPPING  a text bounding box that extends outside the viewBox. The file is
          intact; the picture simply ends mid-sentence.
OVERLAP   two text boxes intersecting by more than a tolerance in both axes.

Text-vs-text only. Text sitting inside a rect is the normal case and is not a
fault, so checking text against shapes would report every label in every box.

WHAT THIS DELIBERATELY DOES NOT JUDGE. It samples one instant, the first frame.
That is sound for a static drawing and unsound for a travelling one: labels
carried by animateMotion legitimately share a starting point and separate over
the loop, so at t=0 they stack, and reporting that produced sixty findings
against six motion studies that were working correctly. Anything under an
animateMotion is excluded, and the number excluded is printed rather than left
silent -- a check that skipped part of its subject has to say so, or a clean
report is a claim about something nobody looked at.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

CHROME = next(Path.home().glob(".cache/ms-playwright/chromium*/chrome-linux/chrome"))
TOL = 2.0          # px of intersection in BOTH axes before it counts
EDGE = 0.5         # px outside the viewBox before it counts

PROBE = """
<script>
window.addEventListener('load', function () {
  var svg = document.querySelector('svg');
  // getBoundingClientRect, NOT getBBox. getBBox reports untransformed geometry,
  // so anything carried by animateMotion reports the position it was authored
  // at rather than where it is drawn. On the generated motion studies that
  // made every moving label look like a collision with its own start point.
  var root = svg.getBoundingClientRect();
  var animated = !!svg.querySelector('.moving');
  var out = [], i = 0, skipped = 0;
  svg.querySelectorAll('text').forEach(function (t) {
    // In a file that carries both tracks the .still copy is display:none and
    // its geometry is not what a reader sees. Check the -still file instead.
    if (animated && t.closest('.still')) return;
    // An element that is invisible at this instant is not on the picture, so
    // it cannot clip and it cannot collide. Alternating states drawn in the
    // same place -- two verdicts swapping on a loop -- are the normal way to
    // build a two-state diagram, and reporting them as an overlap sent me to
    // "fix" a drawing that was working exactly as designed.
    var eff = 1, n = t;
    while (n && n.nodeType === 1) {
      var o = parseFloat(getComputedStyle(n).opacity);
      if (!isNaN(o)) eff *= o;
      if (getComputedStyle(n).display === 'none') { eff = 0; break; }
      n = n.parentNode;
    }
    if (eff < 0.05) return;
    // A travelling label is measured at t=0, which is not where it spends the
    // loop. Exclude it and count it rather than judging it.
    for (var a = t; a && a.nodeType === 1; a = a.parentNode) {
      if (a.querySelector && a.querySelector(':scope > animateMotion')) { skipped++; return; }
    }
    var b = t.getBoundingClientRect();
    if (!b || b.width === 0) return;
    out.push({i: i++, x: b.left - root.left, y: b.top - root.top,
              w: b.width, h: b.height,
              s: (t.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 60)});
  });
  var pre = document.createElement('pre');
  pre.id = 'result';
  pre.textContent = JSON.stringify({vw: root.width, vh: root.height, t: out, skipped: skipped});
  document.body.appendChild(pre);
});
</script>
"""


def boxes(svg_path: Path):
    svg = svg_path.read_text()
    page = Path.home() / "work/.svgprobe.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("<!doctype html><meta charset=utf-8><body>" + svg + PROBE)
    r = subprocess.run(
        [str(CHROME), "--headless", "--disable-gpu", "--no-sandbox",
         "--virtual-time-budget=4000", "--dump-dom", "file://" + str(page)],
        capture_output=True, text=True, timeout=120,
        env={"LD_LIBRARY_PATH": f"{Path.home()}/sysroot/usr/lib64:{Path.home()}/sysroot/lib64",
             "PATH": "/usr/bin:/bin", "HOME": str(Path.home())})
    m = re.search(r'<pre id="result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise RuntimeError(f"no probe result for {svg_path.name}")
    return json.loads(html.unescape(m.group(1)))


def check(svg_path: Path):
    d = boxes(svg_path)
    vw, vh, ts = d["vw"], d["vh"], d["t"]
    faults = []
    for t in ts:
        over_r, over_b = t["x"] + t["w"] - vw, t["y"] + t["h"] - vh
        if over_r > EDGE:
            faults.append(f'CLIP right +{over_r:.0f}px  "{t["s"]}"')
        if over_b > EDGE:
            faults.append(f'CLIP bottom +{over_b:.0f}px  "{t["s"]}"')
        if t["x"] < -EDGE:
            faults.append(f'CLIP left {t["x"]:.0f}px  "{t["s"]}"')
    for a in range(len(ts)):
        for b in range(a + 1, len(ts)):
            p, q = ts[a], ts[b]
            ox = min(p["x"] + p["w"], q["x"] + q["w"]) - max(p["x"], q["x"])
            oy = min(p["y"] + p["h"], q["y"] + q["h"]) - max(p["y"], q["y"])
            if ox > TOL and oy > TOL:
                faults.append(f'OVERLAP {ox:.0f}x{oy:.0f}px  "{p["s"]}" / "{q["s"]}"')
    return faults, d.get("skipped", 0), len(ts)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    targets = [Path(a) for a in sys.argv[1:]] or sorted(
        list((root / "assets/diagrams").glob("*.svg"))
        + list((root / "assets/learning").glob("*.svg")))
    bad = skipped_total = judged_total = 0
    for p in sorted(targets):
        try:
            f, skipped, judged = check(p)
        except Exception as e:
            # A file that could not be measured is not a file that passed.
            print(f"!! {p.name}: {e}")
            bad += 1
            continue
        skipped_total += skipped
        judged_total += judged
        if f:
            bad += 1
            print(f"\n{p.name}")
            for line in f:
                print("   ", line)
    print(f"\n{len(targets)} files checked, {bad} with findings")
    print(f"{judged_total} text elements judged, "
          f"{skipped_total} excluded as travelling (measured at one instant only)")
    sys.exit(1 if bad else 0)
