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
import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
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
  const page = await context.newPage();
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
      return { x: r.left + (x / 860) * r.width, y: r.top + (y / 540) * r.height };
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

  await check("no page errors", async () => { assert.deepEqual(errors, []); });

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
