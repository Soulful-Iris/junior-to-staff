// The code field in a real browser, against a built release in site/out:
//   CHROME_PATH=... node site/tools/codefield-check.mjs
// Downloads Pyodide on the first run (about 6 MB), so it needs the network.
// SITE_SCREENSHOTS=<dir> keeps a picture of every state it checks.
//
// Each scenario is a thing a reader actually does, and each assertion reads
// what the reader would see on the page, not the harness's JSON.
import { chromium } from "playwright";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const PORT = +(process.env.CODEFIELD_PORT || 8911);
const PAGE = `http://127.0.0.1:${PORT}/curriculum/01-code/02-data-structures-algorithms/problems/15-linked-list-cycle-entry/`;
const PROBLEM = join(root, "curriculum/01-code/02-data-structures-algorithms/problems/15-linked-list-cycle-entry");
const shots = process.env.SITE_SCREENSHOTS || mkdtempSync(join(tmpdir(), "codefield-"));
mkdirSync(shots, { recursive: true });

const server = spawn(process.env.PYTHON || "python3.12", ["site/serve.py", String(PORT)], { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
let browser;
let this_count = 0;
const results = [];
async function check(name, fn) {
  const t0 = Date.now();
  try { await fn(); results.push(["ok", name, Date.now() - t0]); }
  catch (e) { results.push(["FAIL", name, Date.now() - t0, e.message.slice(0, 700)]); }
}

const STARTER_BUG = (withPrint) => `from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: object
    next: "Node | None" = None

def cycle_entry(head):
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None
    p = head
    while p is not slow:
${withPrint ? '        print("walking from", p.value)\n' : ""}        slow = slow.next
    return p
`;

try {
  // Our own server, or nothing: on 2026-09-26 a probe on a port another
  // service already held got "not found" for every page and looked like a bug.
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.once("exit", (code) => reject(new Error(`serve.py exited (${code}); is port ${PORT} taken?`)));
    setTimeout(resolve, 1500);
  });
  browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ["--no-sandbox", "--disable-dev-shm-usage"] });
  // Screenshots of the field only, never fullPage: on 2026-09-26 a 2x full-page
  // capture of this long lesson failed ("Unable to capture screenshot") and
  // then took the renderer down on a 1.8 GB machine.
  const scale = +(process.env.SITE_SCREENSHOT_SCALE || 1);
  const context = await browser.newContext({ viewport: { width: 1440, height: +(process.env.SITE_SCREENSHOT_HEIGHT || 1000) }, deviceScaleFactor: scale });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error" && !/favicon\.ico/.test(m.location().url || "")) errors.push(m.text()); });

  const field = () => page.locator(".cf");
  const setCode = (code) => page.evaluate((c) => document.querySelector(".cf").cfField.editor.setCode(c, []), code);
  const run = async () => {
    await page.click('.cf [data-act="run"]');
    await page.waitForFunction(() => { const b = document.querySelector('.cf [data-act="run"]'); return b && !b.disabled; }, null, { timeout: 30000 });
    await page.waitForTimeout(150);
  };
  const shotOf = async (name) => { await field().screenshot({ path: join(shots, name) }); };

  await check("mounts on a desktop page and hides the static block", async () => {
    await page.goto(PAGE, { waitUntil: "domcontentloaded" });
    assert.match(await page.title(), /Find where a linked list loops back on itself/);
    await field().waitFor({ timeout: 15000 });
    assert.equal(await page.locator(".codefield-static").isHidden(), true);
    assert.match(await page.locator(".cf-editor .cm-content").innerText(), /def cycle_entry\(head\):/);
  });

  await check("Python loads in the background and says so", async () => {
    await page.waitForSelector(".cf-status.ready", { timeout: 120000 });
    assert.match(await page.locator(".cf-py").innerText(), /Python 3\.\d+/);
  });

  await check("the starter runs and fails honestly", async () => {
    await run();
    assert.match(await page.locator(".cf-strip").innerText(), /0\s+passed/);
    assert.ok(await page.locator(".cf-case.st-fail, .cf-case.st-error").count() >= 1);
    await shotOf("1-starter.png");
  });

  await check("the reference solution passes every test", async () => {
    await setCode(readFileSync(join(PROBLEM, "solution.py"), "utf8"));
    await run();
    const n = await page.locator(".cf-case").count();
    assert.ok(n >= 2);
    assert.equal(await page.locator(".cf-case.st-pass").count(), n);
    await shotOf("2-passing.png");
  });

  await check("freeing a 20,000-node chain as a temporary leaves Python working", async () => {
    // The shape of problem 30: a deep structure that dies mid-expression. In a
    // browser worker, CPython's recursive free overflows the engine's stack
    // around 3,000 deep and breaks that Python for good.
    const code = "class N:\n    def __init__(s, v, n=None):\n        s.value, s.next = v, n\n" +
                 "def build(k):\n    h = None\n    for i in range(k):\n        h = N(i, h)\n    return h\n";
    const tests = "import unittest\nfrom solution import build\nclass T(unittest.TestCase):\n" +
                  "    def test_temporary(self):\n        self.assertEqual(build(20000).value, 19999)\n" +
                  "    def test_after(self):\n        self.assertEqual(build(5).value, 4)\n";
    const r = await page.evaluate((p) => document.querySelector(".cf").cfField.runtime.run(p), JSON.stringify({ code, tests }));
    assert.equal(r.status, "ok", JSON.stringify(r.error));
    assert.deepEqual(r.tests.map((t) => t.status), ["pass", "pass"]);
  });

  await check("a loop that never ends is stopped at 3 s and the loop is marked", async () => {
    await setCode(STARTER_BUG(false));
    const t0 = Date.now();
    await run();
    const ms = Date.now() - t0;
    assert.ok(ms < 9000, `took ${ms} ms`);
    const banner = await page.locator(".cf-banner").innerText();
    assert.match(banner, /Stopped: out of time/);
    assert.match(banner, /lines 18 to 19/);
    assert.equal(await page.locator(".cf-line-stop").count(), 2);
    assert.match(await page.locator(".cf-strip").innerText(), /Time\s+3\.0\s+of 3 s/);
    await shotOf("3-loop.png");
  });

  await check("printing forever is cut at 64 KB and folded", async () => {
    await setCode(STARTER_BUG(true));
    await run();
    assert.match(await page.locator(".cf-banner").innerText(), /Stopped: too much output/);
    assert.match(await page.locator(".cf-ll.fold").first().innerText(), /Same line [\d,]+ more times/);
    assert.match(await page.locator(".cf-strip").innerText(), /Output\s+64 KB\s+of 64 KB/);
    assert.ok(await page.locator(".cf-log .cf-ll").count() < 20, "the page drew the flood instead of folding it");
    await shotOf("4-flood.png");
  });

  await check("a breakpoint set by clicking the gutter records stops you can step through", async () => {
    await setCode(STARTER_BUG(false));
    const gutter = page.locator(".cf-bp-gutter .cm-gutterElement").nth(19);   // line 19, after the spacer
    await gutter.click();
    assert.deepEqual(await page.evaluate(() => document.querySelector(".cf").cfField.editor.getBreakpoints()), [19]);
    await run();
    assert.match(await page.locator(".cf-detail").innerText(), /Stopped at line 19/);
    const first = await page.locator(".cf-vars").innerText();
    assert.match(first, /\bp\b/);
    assert.match(first, /slow/);
    await page.click('[data-stop="1"]');
    assert.match(await page.locator(".cf-detail").innerText(), /stop 2 of/);
    assert.equal(await page.locator(".cf-line-here").count(), 1);
    await shotOf("5-breakpoint.png");
  });

  await check("the given data class cannot be edited", async () => {
    await page.evaluate(() => document.querySelector(".cf").cfField.reset());
    const before = await page.evaluate(() => document.querySelector(".cf").cfField.editor.getCode());
    await page.locator(".cf-editor .cm-line").nth(4).click();
    await page.keyboard.type("oops");
    const after = await page.evaluate(() => document.querySelector(".cf").cfField.editor.getCode());
    assert.equal(after, before);
  });

  await check("select all and paste a whole solution replaces everything, and protection comes back", async () => {
    await page.locator(".cf-editor .cm-content").click();
    await page.keyboard.press("Control+A");
    await page.evaluate((c) => navigator.clipboard ? 0 : 0, "");
    const sol = readFileSync(join(PROBLEM, "solution.py"), "utf8");
    await page.evaluate((c) => {
      const view = document.querySelector(".cf").cfField.editor.view;
      view.dispatch(view.state.replaceSelection(c));          // what a paste does
    }, sol);
    const now = await page.evaluate(() => document.querySelector(".cf").cfField.editor.getCode());
    assert.equal(now, sol);
    assert.equal(await page.evaluate(() => document.querySelector(".cf").cfField.editor.hasGiven()), true);
  });

  await check("your code survives a reload", async () => {
    await setCode(STARTER_BUG(false) + "\n# mine\n");
    await page.evaluate(() => document.querySelector(".cf").cfField.save());
    await page.reload({ waitUntil: "domcontentloaded" });
    await field().waitFor();
    assert.match(await page.locator(".cf-editor .cm-content").innerText(), /# mine/);
    assert.match(await page.locator(".cf-strip").innerText(), /Restored your code/);
  });

  await check("no page errors", async () => { assert.deepEqual(errors, []); });

  await check("all 38 reference solutions pass in the browser's Python", async () => {
    // Its own context: 38 runs grow one Python's heap, and nothing after this
    // should run on it.
    await context.close();
    const ctx38 = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const p38 = await ctx38.newPage();
    await p38.goto(PAGE, { waitUntil: "domcontentloaded" });
    await p38.waitForSelector(".cf-status.ready", { timeout: 120000 });
    const root38 = join(root, "curriculum/01-code/02-data-structures-algorithms/problems");
    const bad = [];
    for (const d of readdirSync(root38).sort()) {
      const dir = join(root38, d);
      if (!existsSync(join(dir, "test_solution.py")) || !/\*\*Write this:\*\*/.test(readFileSync(join(dir, "README.md"), "utf8"))) continue;
      const payload = JSON.stringify({ code: readFileSync(join(dir, "solution.py"), "utf8"), tests: readFileSync(join(dir, "test_solution.py"), "utf8"), seconds: 20 });
      const r = await p38.evaluate((p) => document.querySelector(".cf").cfField.runtime.run(p), payload);
      const failing = (r.tests || []).filter((t) => t.status !== "pass");
      if (r.status !== "ok" || !r.tests.length || failing.length) bad.push(`${d}: ${r.status} ${failing.map((t) => t.name + "=" + t.status).join(", ")} ${r.error ? r.error.message : ""}`);
      this_count++;
    }
    assert.equal(this_count, 38);
    assert.deepEqual(bad, []);
  });

  await check("a phone gets the static block and no field", async () => {
    const phone = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const p2 = await phone.newPage();
    await p2.goto(PAGE, { waitUntil: "load" });
    await p2.waitForTimeout(800);
    assert.equal(await p2.locator(".cf").count(), 0);
    assert.equal(await p2.locator(".codefield-static").isVisible(), true);
    await phone.close();
  });
} finally {
  if (browser) await browser.close();
  server.kill();
  for (const [status, name, ms, why] of results) console.log(`${status.padEnd(4)} ${name}  (${ms} ms)${why ? "\n       " + why : ""}`);
  console.log(`screenshots: ${shots}`);
  process.exitCode = results.some((r) => r[0] !== "ok") ? 1 : 0;
}
