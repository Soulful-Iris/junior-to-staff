/* Render Markdown diagrams in a real browser for review.
 * Install mermaid and playwright in a separate tooling directory; set NODE_PATH.
 * Usage: node scripts/render_mermaid.cjs /absolute/output [Markdown paths...]
 * Output is review evidence, not committed generated source.
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { execFileSync } = require('node:child_process');
const { chromium } = require('playwright');

async function main() {
  const root = path.resolve(__dirname, '..');
  const output = path.resolve(process.argv[2] || path.join(root, '..', 'mermaid-review'));
  const dist = path.dirname(require.resolve('mermaid'));
  const files = process.argv.slice(3).length ? process.argv.slice(3) :
    execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard'], {cwd: root, encoding: 'utf8'})
      .trim().split('\n').filter(p => p.endsWith('.md'));
  fs.mkdirSync(output, {recursive: true});
  const server = http.createServer((req, res) => {
    if (req.url === '/') {
      res.setHeader('Content-Type', 'text/html');
      res.end('<html><body style="margin:16px;width:760px;background:#faf9f7;font-family:Arial"><div id="drawing"></div></body></html>');
      return;
    }
    const target = path.resolve(dist, '.' + decodeURIComponent(req.url.split('?')[0]));
    if (!target.startsWith(dist + path.sep) || !fs.existsSync(target)) {res.writeHead(404);res.end();return;}
    res.setHeader('Content-Type', 'text/javascript');
    fs.createReadStream(target).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const launch = {headless: true};
  if (process.env.BROWSER_EXECUTABLE_PATH) launch.executablePath = process.env.BROWSER_EXECUTABLE_PATH;
  if (process.env.USE_PACKAGED_CHROMIUM === '1') {
    const module = require('@sparticuz/chromium');
    const packaged = module.default || module;
    launch.executablePath = process.env.BROWSER_EXECUTABLE_PATH || await packaged.executablePath();
    launch.args = packaged.args;
  }
  const browser = await chromium.launch(launch);
  const page = await browser.newPage({viewport: {width: 800, height: 900}, deviceScaleFactor: 1});
  const records = [];
  try {
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    await page.evaluate(async () => {
      window.mermaid = (await import('/mermaid.esm.min.mjs')).default;
      window.mermaid.initialize({startOnLoad: false, securityLevel: 'strict', theme: 'base',
        themeVariables: {fontFamily: 'Arial', fontSize: '16px', primaryColor: '#eef2ef',
          primaryTextColor: '#1f2b24', primaryBorderColor: '#2f6f4e', lineColor: '#6d6459', background: '#faf9f7'},
        flowchart: {htmlLabels: false}});
    });
    for (const file of files) {
      const text = fs.readFileSync(path.resolve(root, file), 'utf8');
      let ordinal = 0;
      for (const match of text.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)) {
        ordinal++;
        const id = 'diagram' + records.length;
        const record = {file, ordinal, line: text.slice(0, match.index).split('\n').length};
        try {
          const svg = await page.evaluate(async ({source, id}) => {
            document.getElementById('drawing').innerHTML = '';
            const result = await window.mermaid.render(id, source, document.getElementById('drawing'));
            document.getElementById('drawing').innerHTML = result.svg;
            const node = document.querySelector('#drawing svg');
            node.style.maxWidth = '760px';
            node.style.height = 'auto';
            return result.svg;
          }, {source: match[1], id});
          record.image = `${id}.png`;
          fs.writeFileSync(path.join(output, `${id}.svg`), svg);
          await page.locator('#drawing').screenshot({path: path.join(output, record.image)});
          record.ok = true;
        } catch (error) {
          record.ok = false;
          record.error = String(error).slice(0, 1200);
        }
        records.push(record);
      }
    }
  } finally {await browser.close(); await new Promise(resolve => server.close(resolve));}
  fs.writeFileSync(path.join(output, 'manifest.json'), JSON.stringify(records, null, 2));
  const failures = records.filter(r => !r.ok);
  console.log(JSON.stringify({files: files.length, diagrams: records.length, output, failures}, null, 2));
  if (failures.length) process.exitCode = 1;
}
main().catch(error => {console.error(error);process.exit(1);});
