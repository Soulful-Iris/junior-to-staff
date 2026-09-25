#!/usr/bin/env node
/* Pre-render every mermaid block in the curriculum to a static SVG.
 *
 * Why pre-render rather than ship mermaid to the browser: the rest of this
 * site is static files with no framework, it has to read on a phone with a bad
 * connection, and a diagram that needs 3MB of JavaScript to appear is a diagram
 * that sometimes does not appear. Pre-rendering also means the diagrams are in
 * the house palette rather than mermaid's, which matters when 387 of them sit
 * next to 100 hand-drawn SVGs.
 *
 * One browser, one mermaid load, all diagrams. Output is content-addressed, so
 * a rebuild only renders blocks whose source actually changed.
 *
 *   node render-mermaid.mjs <manifest.json> <outdir>
 *
 * manifest.json: [{ "hash": "...", "code": "flowchart TD\n..." }, ...]
 * writes <outdir>/<hash>.svg for each, skipping ones that already exist.
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync, renameSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from 'playwright';

const [manifestPath, outDir] = process.argv.slice(2);
if (!manifestPath || !outDir) {
  console.error('usage: render-mermaid.mjs <manifest.json> <outdir>');
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });

const all = JSON.parse(readFileSync(manifestPath, 'utf8'));
const todo = all.filter((d) => !existsSync(join(outDir, `${d.hash}.svg`)));
console.log(`${all.length} diagrams, ${todo.length} to render, ${all.length - todo.length} cached`);
if (todo.length === 0) process.exit(0);

const mermaidSrc = readFileSync(
  new URL('./node_modules/mermaid/dist/mermaid.min.js', import.meta.url), 'utf8');

// The house palette. Green is the base ink for structure, warm is reserved for
// cost, danger and failure — the same rule the hand-drawn diagrams follow.
const CONFIG = {
  startOnLoad: false,
  securityLevel: 'strict',
  theme: 'base',
  themeVariables: {
    background: '#faf9f7',
    primaryColor: '#eef2ef',
    primaryTextColor: '#1f2b24',
    primaryBorderColor: '#2f6f4e',
    lineColor: '#8a857d',
    secondaryColor: '#faf0e9',
    secondaryBorderColor: '#c2703d',
    tertiaryColor: '#f4f2ee',
    tertiaryBorderColor: '#ded9d1',
    edgeLabelBackground: '#faf9f7',
    clusterBkg: '#f4f2ee',
    clusterBorder: '#ded9d1',
    titleColor: '#1f2b24',
    noteBkgColor: '#faf0e9',
    noteBorderColor: '#c2703d',
    noteTextColor: '#1f2b24',
    actorBkg: '#eef2ef',
    actorBorder: '#2f6f4e',
    actorTextColor: '#1f2b24',
    signalColor: '#6d6459',
    signalTextColor: '#3f3b36',
    labelBoxBkgColor: '#eef2ef',
    labelBoxBorderColor: '#2f6f4e',
    labelTextColor: '#1f2b24',
    fontFamily: 'ui-sans-serif, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif',
    fontSize: '14px',
  },
  flowchart: { curve: 'basis', nodeSpacing: 52, rankSpacing: 58, padding: 14, useMaxWidth: false, htmlLabels: true },
  sequence: { useMaxWidth: false, actorMargin: 60, boxMargin: 12, noteMargin: 12 },
  state: { nodeSpacing: 58, rankSpacing: 68, useMaxWidth: false, padding: 14 },
  er: { useMaxWidth: false },
};

const chrome = process.env.CHROME_PATH;
if (!chrome) { console.error('CHROME_PATH not set'); process.exit(2); }

const browser = await chromium.launch({
  executablePath: chrome,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--font-render-hinting=none'],
});
const page = await browser.newPage();
await page.setViewportSize({ width: 1400, height: 1200 });
await page.setContent('<!doctype html><html><body><div id="host"></div></body></html>');
await page.addScriptTag({ content: mermaidSrc });
await page.evaluate((cfg) => { window.mermaid.initialize(cfg); }, CONFIG);

let ok = 0;
const failures = [];
for (const d of todo) {
  try {
    const svg = await page.evaluate(async ({code, id}) => {
      const { svg } = await window.mermaid.render(id, code);
      return svg;
    }, {code: d.code, id: `m${d.hash.slice(0, 10)}`});
    // Mermaid puts node labels in a <foreignObject> as HTML, so a label
    // written with a line break comes out as a bare <br>. That is correct
    // HTML and invalid XML, and every consumer downstream parses this as
    // XML: diagram_cache.valid_svg() calls ET.fromstring, fails on the
    // mismatched tag, and reports the diagram as MISSING even though the
    // file rendered fine and opens perfectly in a browser.
    //
    // Measured 2026-09-25: eight flowcharts in the curriculum, each 14-24 KB
    // of valid-looking SVG, all rejected for this and all invisible until a
    // separate parse error stopped masking them. Closing the void elements
    // here fixes those eight and every diagram anyone writes afterwards,
    // which is the point of doing it in the renderer rather than in eight
    // markdown files.
    // The (?=[\s/>]) is load bearing: without it the alternation matches the
    // "br" inside <brother> and turns it into <brother/>. Caught by a unit
    // test before this ran on anything real.
    const xmlSafe = svg.replace(
      /<(br|img|hr|input)(?=[\s/>])((?:[^>"']|"[^"]*"|'[^']*')*?)\s*\/?>/gi,
      (_, tag, attrs) => `<${tag}${attrs}/>`);
    const output = join(outDir, `${d.hash}.svg`);
    const temporary = output + `.${process.pid}.tmp`;
    writeFileSync(temporary, xmlSafe, 'utf8');
    renameSync(temporary, output);
    ok++;
    if (ok % 50 === 0) console.log(`  ${ok}/${todo.length}`);
  } catch (e) {
    failures.push({ hash: d.hash, error: String(e).split('\n')[0], head: d.code.split('\n')[0] });
  }
}
await browser.close();

console.log(`rendered ${ok}, failed ${failures.length}`);
if (failures.length) {
  writeFileSync(join(outDir, '_failures.json'), JSON.stringify(failures, null, 2));
  for (const f of failures.slice(0, 10)) console.log(`  FAIL ${f.head} :: ${f.error}`);
}
// A failure here means a diagram silently vanishes from a page, so make it loud.
process.exit(failures.length ? 1 : 0);
