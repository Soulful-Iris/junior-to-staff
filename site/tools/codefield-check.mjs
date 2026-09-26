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

  // ---- v2: your own inputs, time and memory, tips, a clean Python every run
  const TIPS = JSON.parse(readFileSync(join(PROBLEM, "tips.json"), "utf8"));
  const tipText = (t) => (typeof t === "string" ? t : t.text).replace(/`/g, "");
  const cf = (fn, arg) => page.evaluate(fn, arg);
  const clearInputs = () => cf(() => { const f = document.querySelector(".cf").cfField; while (f.cells.length) f.removeInput(0); });

  await check("the tests are listed before the first run", async () => {
    await clearInputs();
    await page.reload({ waitUntil: "domcontentloaded" });
    await field().waitFor();
    const rows = page.locator(".cf-case:not(.kind-input)");
    assert.equal(await rows.count(), 2);
    assert.equal(await page.locator(".cf-case.planned").count(), 2);
    assert.match(await rows.first().innerText(), /Every small prefix and cycle length/);
  });

  await check("add your own input: it starts from the problem's example and shows value, time and memory", async () => {
    await page.waitForSelector(".cf-status.ready", { timeout: 120000 });
    await setCode(readFileSync(join(PROBLEM, "solution.py"), "utf8"));
    await page.click(".cf-add");
    assert.equal(await page.locator(".cf-case.kind-input").count(), 1);
    assert.match(await page.locator(".cf-detail .cf-cell .cm-content").innerText(), /cycle_entry\(a\)/);
    await run();
    const detail = await page.locator(".cf-detail").innerText();
    assert.match(detail, /Returned\s+Node\(value='b'/);
    assert.match(detail, /inside\s+cycle_entry/);
    assert.match(detail, /\d+(\.\d)? [KM]?B\s+(of new|peak) memory used by the call/, "the memory line is missing");
    assert.match(await page.locator(".cf-case.kind-input .cf-csub").innerText(), /→ Node\(value='b'/);
    await shotOf("6-your-input.png");
  });

  await check("memory is measured in the browser's Python: an input that allocates shows it", async () => {
    // A number is not enough: 0 B is also what a tracemalloc that tracks
    // nothing would say. A bytearray is its length in bytes on any build (the
    // browser's Python is 32-bit, so a list's size there is half of CPython's
    // on a desktop: 250,000 references came back as 977 KB, not 2 MB).
    await page.click(".cf-add");
    await page.evaluate(() => {
      const f = document.querySelector(".cf").cfField, v = f.cells[f.cells.length - 1].view;
      v.dispatch({ changes: { from: 0, to: v.state.doc.length, insert: "bytearray(3_000_000)" } });
    });
    await run();
    await page.locator(".cf-case.kind-input").nth(1).click();
    assert.match(await page.locator(".cf-detail .cf-metrics").innerText(), /(2\.[5-9]|3\.[0-2]) MB\s+peak memory used by the call/);
    await page.evaluate(() => document.querySelector(".cf").cfField.removeInput(1));
  });

  await check("each test shows the time spent inside your code", async () => {
    await page.locator(".cf-case:not(.kind-input)").first().click();
    assert.match(await page.locator(".cf-detail .cf-metrics").innerText(), /inside your code/);
    assert.match(await page.locator(".cf-detail .cf-metrics").innerText(), /the whole test took/);
    for (const t of await page.locator(".cf-case:not(.kind-input) .cf-ct").allInnerTexts()) assert.match(t, /ms|s$/);
    await shotOf("7-test-time.png");
  });

  await check("your inputs survive a reload", async () => {
    await page.evaluate(() => document.querySelector(".cf").cfField.save());
    await page.reload({ waitUntil: "domcontentloaded" });
    await field().waitFor();
    assert.equal(await page.locator(".cf-case.kind-input").count(), 1);
    assert.match(await page.locator(".cf-case.kind-input .cf-cl").innerText(), /cycle_entry\(a\)/);
  });

  await check("an input that never ends stops the run, and says the tests did not run", async () => {
    await page.waitForSelector(".cf-status.ready", { timeout: 120000 });
    await setCode(STARTER_BUG(false));
    await run();
    assert.match(await page.locator(".cf-strip").innerText(), /Stopped in your input\s+1/);
    const banner = await page.locator(".cf-detail .cf-banner").innerText();
    assert.match(banner, /Your input ran for 3 seconds/);
    assert.match(banner, /The tests did not run/);
    assert.equal(await page.locator(".cf-line-stop").count(), 2);
  });

  await check("a tip about a stop comes from the problem's own stopped tips", async () => {
    await page.click('.cf [data-act="tip"]');
    const tip = await page.locator(".cf-tip").innerText();
    assert.match(tip, /Tip 1 of \d+/);
    assert.ok(tip.replace(/\s+/g, " ").includes(tipText(TIPS.stopped[0]).slice(0, 60)), tip);
    await shotOf("8-tip-stopped.png");
  });

  await check("five inputs is the most, and one can be removed", async () => {
    for (let n = await page.locator(".cf-case.kind-input").count(); n < 5; n++) await page.click(".cf-add");
    assert.equal(await page.locator(".cf-case.kind-input").count(), 5);
    assert.equal(await page.locator(".cf-add").isDisabled(), true);
    assert.match(await page.locator(".cf-add").innerText(), /Five inputs is the most/);
    await page.locator(".cf-case.kind-input").nth(4).hover();
    await page.locator(".cf-case.kind-input").nth(4).locator(".cf-x").click();
    assert.equal(await page.locator(".cf-case.kind-input").count(), 4);
    assert.equal(await page.locator(".cf-add").isDisabled(), false);
    await clearInputs();
  });

  await check("on the starter, a tip is the first step of the approach, and Another tip goes on", async () => {
    await page.evaluate(() => { const f = document.querySelector(".cf").cfField; f.reset(); f.result = null; f.sel = null; f.hideTip(); f.render(); });
    await page.click('.cf [data-act="tip"]');
    assert.ok((await page.locator(".cf-tip p").innerText()).includes(tipText(TIPS.start[0]).slice(0, 50)));
    await shotOf("9-tip-start.png");
    await page.click('.cf-tip [data-tip="next"]');
    assert.match(await page.locator(".cf-tip").innerText(), /Tip 2 of/);
    assert.ok((await page.locator(".cf-tip p").innerText()).includes(tipText(TIPS.start[1]).slice(0, 50)));
    await page.click(".cf-tip-close");
    assert.equal(await page.locator(".cf-tip").isHidden(), true);
  });

  await check("every run starts from a clean Python", async () => {
    const code = "import builtins\ncount = 0\ncount += 1\nbuiltins.LEAK = getattr(builtins, 'LEAK', 0) + 1\n";
    const tests = "import unittest, builtins\nfrom solution import count\nclass T(unittest.TestCase):\n" +
                  "    def test_fresh(self):\n        self.assertEqual((count, builtins.LEAK), (1, 1))\n";
    for (let k = 0; k < 2; k++) {
      const r = await page.evaluate((p) => document.querySelector(".cf").cfField.runtime.run(p), JSON.stringify({ code, tests }));
      assert.deepEqual(r.tests.map((t) => t.status), ["pass"], JSON.stringify(r.tests[0]));
    }
  });

  await check("a failed check on plain values can be run as your own input", async () => {
    const two = PAGE.replace("15-linked-list-cycle-entry", "01-two-sum");
    await page.goto(two, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".cf-status.ready", { timeout: 120000 });
    await page.evaluate(() => { const f = document.querySelector(".cf").cfField; while (f.cells.length) f.removeInput(0); });
    await setCode("def two_sum(nums, target):\n    return (0, 0)\n");
    await run();
    await page.locator(".cf-case.st-fail").first().click();
    const link = page.locator(".cf-detail [data-try]");
    assert.equal(await link.count(), 1);
    await link.click();
    await page.waitForFunction(() => { const b = document.querySelector('.cf [data-act="run"]'); return b && !b.disabled; }, null, { timeout: 30000 });
    await page.waitForTimeout(200);
    assert.equal(await page.locator(".cf-case.kind-input").count(), 1);
    assert.match(await page.locator(".cf-detail").innerText(), /Returned\s+\(0, 0\)/);
    await shotOf("10-try-as-input.png");
    await page.evaluate(() => { const f = document.querySelector(".cf").cfField; while (f.cells.length) f.removeInput(0); f.reset(); });
  });

  await check("once everything passes, a tip whose code is an input runs as one", async () => {
    // Problem 14's passing tip carries a long list to reverse: an input, not a skeleton.
    const dir = PROBLEM.replace("15-linked-list-cycle-entry", "14-reverse-linked-list");
    const passing = JSON.parse(readFileSync(join(dir, "tips.json"), "utf8")).passing;
    assert.ok(passing.code && !/^def /m.test(passing.code), "14's passing tip is no longer an input; pick another problem");
    await page.goto(PAGE.replace("15-linked-list-cycle-entry", "14-reverse-linked-list"), { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".cf-status.ready", { timeout: 120000 });
    await page.evaluate(() => { const f = document.querySelector(".cf").cfField; while (f.cells.length) f.removeInput(0); });
    await setCode(readFileSync(join(dir, "solution.py"), "utf8"));
    await run();
    await page.click('.cf [data-act="tip"]');
    assert.match(await page.locator(".cf-tip").innerText(), /about what to try next/);
    await page.click('.cf-tip [data-tip="try"]');
    await page.waitForFunction(() => { const b = document.querySelector('.cf [data-act="run"]'); return b && !b.disabled; }, null, { timeout: 30000 });
    await page.waitForTimeout(200);
    assert.equal(await page.locator(".cf-case.kind-input").count(), 1);
    assert.match(await page.locator(".cf-detail").innerText(), /Returned\s+Node\(/);
    await page.evaluate(() => { const f = document.querySelector(".cf").cfField; while (f.cells.length) f.removeInput(0); f.reset(); });
  });

  await check("no page errors", async () => { assert.deepEqual(errors, []); });

  await check("all 38 reference solutions pass in the browser's Python, with their example inputs", async () => {
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
      // With the problem's own example as an input: the one the page offers
      // first must run in the browser's Python, not only under CPython, and at
      // the page's own 3 seconds it must leave the tests time to run.
      const example = JSON.parse(readFileSync(join(dir, "tips.json"), "utf8")).example;
      const payload = JSON.stringify({ code: readFileSync(join(dir, "solution.py"), "utf8"), tests: readFileSync(join(dir, "test_solution.py"), "utf8"), seconds: 3, inputs: [example] });
      const r = await p38.evaluate((p) => document.querySelector(".cf").cfField.runtime.run(p), payload);
      const failing = (r.tests || []).filter((t) => t.status !== "pass");
      const inp = (r.inputs || [])[0] || {};
      if (r.status !== "ok" || !r.tests.length || failing.length || inp.status !== "ok")
        bad.push(`${d}: ${r.status} ${failing.map((t) => t.name + "=" + t.status).join(", ")} example=${inp.status} ${JSON.stringify(inp.failure || "")} ${r.error ? r.error.message : ""}`);
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
