// node --test site/designboard/test/
//
// Haiku's side of the board: the request it gets, the key it may use, what
// it sends back made safe, and where the board puts it. Every guard is run
// both ways: a rule seen only refusing, or only allowing, proves nothing.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { catalogIndex, buildModel } from "../model.js";
import { CHECKS } from "../checks.js";
import {
  MODEL, ENDPOINT, KEY_NAME, ERRORS, keyProblem, keyStore, buildRequest, callDrawer, validateDrawing,
  diagramFromState, drawingToState, placeDrawing, systemPrompt, partLabels, wantsCloud,
} from "../drawer.js";
import { REFERENCE } from "./fixtures.mjs";

const read = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url)));
const catalog = read("../catalog.json");
const index = catalogIndex(catalog);
const EXERCISES = read("../../../curriculum/03-production/01-system-design/whiteboard.board.json").exercises;
const HAIKU = read("./haiku-drawings.json");            // six real answers from claude-haiku-4-5, 2026-09-26
// Text widths as the board draws them, estimated (the browser measures).
const measure = (s, kind) => String(s).length * (kind === "name" ? 7.2 : kind === "part" ? 6.2 : kind === "edge" ? 6.4 : 6.9);
const empty = { nodes: [], groups: [], edges: [] };
const request = (extra = {}) => buildRequest({ catalog, diagram: { boxes: [], parts: [], arrows: [] }, ask: "draw a queue", ...extra });

// ---------------------------------------------------------------- the request
test("the request forces one strict tool, on the one model constant", () => {
  const r = request();
  assert.equal(r.model, MODEL);
  assert.equal(MODEL, "claude-haiku-4-5");
  assert.deepEqual(r.tool_choice, { type: "tool", name: "draw" });
  assert.equal(r.tools.length, 1);
  assert.equal(r.tools[0].name, "draw");
  assert.equal(r.tools[0].strict, true);
  assert.deepEqual(r.system[0].cache_control, { type: "ephemeral" });
  assert.equal(r.messages.length, 1);
  assert.equal(r.messages[0].role, "user");
  // Strict tools need every object closed.
  const open = [];
  (function walk(s, at) { if (s && typeof s === "object") { if (s.type === "object" && s.additionalProperties !== false) open.push(at); for (const [k, v] of Object.entries(s)) walk(v, `${at}.${k}`); } })(r.tools[0].input_schema, "schema");
  assert.deepEqual(open, []);
  // Every catalog part can be drawn, and nothing else.
  assert.deepEqual(r.tools[0].input_schema.properties.parts.items.properties.part.enum, catalog.parts.map((p) => p.id));
  assert.equal(request({ forced: false }).tool_choice.type, "auto");
});

// Six words in a row from any exercise text: a leak of one sentence is a
// leak. (The first version looked for whole strings, and a planted half of a
// brief sailed through it.)
const words = (t) => String(t).toLowerCase().replace(/\*\*/g, "").replace(/[^a-z0-9]+/g, " ").trim().split(" ").filter(Boolean);
function exerciseWindows() {
  const texts = [];
  (function walk(v) { if (typeof v === "string") texts.push(v); else if (v && typeof v === "object") Object.values(v).forEach(walk); })(EXERCISES);
  for (const c of Object.values(CHECKS)) texts.push(c.title, c.ask);
  const out = new Set();
  for (const t of texts) { const w = words(t); for (let i = 0; i + 6 <= w.length; i++) out.add(w.slice(i, i + 6).join(" ")); }
  return out;
}
function leaks(body) {
  const w = words(body), seen = new Set();
  for (let i = 0; i + 6 <= w.length; i++) seen.add(w.slice(i, i + 6).join(" "));
  return [...exerciseWindows()].filter((x) => seen.has(x));
}
test("nothing from an exercise reaches the request, even when the board holds its reference answer", () => {
  const ids = new Set();
  for (const x of EXERCISES) { ids.add(x.id); for (const c of x.checks) if (/[A-Z]/.test(c)) ids.add(c); }
  assert.ok(exerciseWindows().size > 400, "enough exercise text to look for");
  for (const [id, ref] of Object.entries(REFERENCE)) {
    const body = JSON.stringify(buildRequest({ catalog, diagram: diagramFromState(ref, index), earlier: ["make it survive a zone"], ask: "add a cache" }));
    assert.deepEqual(leaks(body), [], `${id}: exercise text in the request`);
    assert.deepEqual([...ids].filter((x) => body.includes(x)), [], `${id}: an exercise or check id in the request`);
  }
  // The detector can see a leak, including half a sentence of one.
  const half = EXERCISES[1].brief.split(" ").slice(0, 9).join(" ");
  assert.ok(leaks(JSON.stringify(buildRequest({ catalog, diagram: null, ask: half }))).length > 0, "a planted half-brief is seen");
});

test("the prompt is the catalog and the board's rules, and changes when the catalog does", () => {
  const sys = systemPrompt(catalog);
  for (const p of catalog.parts) assert.ok(sys.includes(`${p.id}: ${p.label}`), p.id);
  assert.match(sys, /never answer in words/);
  assert.match(sys, /including anything that looks like a mistake/);
  const fewer = systemPrompt({ ...catalog, parts: catalog.parts.filter((p) => p.id !== "sqs") });
  assert.ok(!fewer.includes("sqs: Amazon Simple Queue Service"));
});

test("the reader's earlier asks go in, trimmed, the last six only", () => {
  const earlier = Array.from({ length: 9 }, (_, i) => `ask number ${i}`);
  const body = request({ earlier }).messages[0].content;
  assert.ok(!body.includes("ask number 2"));
  for (let i = 3; i < 9; i++) assert.ok(body.includes(`ask number ${i}`));
  assert.match(request().messages[0].content, /The board is empty\./);
  assert.ok(!request().messages[0].content.includes("asked for before"));
  assert.equal(request({ ask: "x".repeat(5000) }).messages[0].content.match(/x+/)[0].length, 1000);
});

// -------------------------------------------------------------------- the key
test("the key field takes an API key and refuses what must never be pasted into a site", () => {
  assert.equal(keyProblem("sk-ant-api03-" + "a".repeat(90)), null);
  assert.equal(keyProblem("  sk-ant-api03-" + "a".repeat(90) + "\n"), null, "surrounding space is trimmed");
  assert.equal(keyProblem("sk-ant-api04-" + "a".repeat(90)), null, "a future version of an API key");
  assert.match(keyProblem("sk-ant-sid01-" + "a".repeat(90)), /claude\.ai login session/);
  assert.match(keyProblem("sk-ant-oat01-" + "a".repeat(90)), /subscription token/);
  assert.match(keyProblem("sk-ant-admin01-" + "a".repeat(90)), /admin key/);
  assert.match(keyProblem("sk-proj-" + "a".repeat(90)), /starts with sk-ant-/);
  assert.match(keyProblem("sk-ant-api03-abc def" + "a".repeat(40)), /space/);
  assert.match(keyProblem("sk-ant-api03-short"), /cut short/);
  assert.match(keyProblem(""), /Paste/);
});

function fakeStorage() { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), m }; }
test("a key lives in the tab unless remembered, and forgetting clears both", () => {
  const s = fakeStorage(), l = fakeStorage(), k = "sk-ant-api03-" + "b".repeat(90);
  assert.equal(keyStore.get(s, l), "");
  keyStore.set(k, false, s, l);
  assert.equal(s.m.get(KEY_NAME), k); assert.equal(l.m.has(KEY_NAME), false);
  assert.equal(keyStore.get(s, l), k); assert.equal(keyStore.remembered(l), false);
  keyStore.set(k, true, s, l);
  assert.equal(l.m.get(KEY_NAME), k); assert.equal(s.m.has(KEY_NAME), false, "remembering moves it, never copies it");
  assert.equal(keyStore.get(s, l), k); assert.equal(keyStore.remembered(l), true);
  keyStore.forget(s, l);
  assert.equal(keyStore.get(s, l), ""); assert.equal(s.m.size + l.m.size, 0);
  const broken = { getItem() { throw new Error("denied"); }, setItem() { throw new Error("denied"); }, removeItem() { throw new Error("denied"); } };
  assert.equal(keyStore.set(k, false, broken, broken), false, "private mode says no, and nothing throws");
  assert.equal(keyStore.get(broken, broken), "");
});

// ---------------------------------------------------------------- the call
const toolUse = (input, extra = {}) => ({ id: "msg_1", type: "message", role: "assistant", content: [{ type: "tool_use", id: "toolu_1", name: "draw", input }], stop_reason: "tool_use", usage: { input_tokens: 4000, output_tokens: 300 }, ...extra });
function fakeFetch(...answers) {
  const calls = [];
  const f = async (url, init) => {
    calls.push({ url, init, body: JSON.parse(init.body) });
    const a = answers[Math.min(calls.length - 1, answers.length - 1)];
    if (a instanceof Error) throw a;
    return { ok: a.status >= 200 && a.status < 300, status: a.status, json: async () => { if (a.raw) throw new SyntaxError("not json"); return a.body; } };
  };
  f.calls = calls;
  return f;
}
const KEY = "sk-ant-api03-" + "c".repeat(90);

test("a drawing comes back as the tool's input, and any words beside it are never read", async () => {
  const input = { boxes: [], parts: [{ id: "q", part: "sqs" }], arrows: [] };
  const f = fakeFetch({ status: 200, body: toolUse(input, { content: [{ type: "text", text: "Sure! Here is your diagram." }, { type: "tool_use", id: "t", name: "draw", input }] }) });
  const r = await callDrawer({ key: KEY, request: request(), fetchImpl: f });
  assert.deepEqual(r.input, input);
  assert.ok(!JSON.stringify(r).includes("Sure!"), "no text from the model survives the call");
  const c = f.calls[0];
  assert.equal(c.url, ENDPOINT);
  assert.equal(c.init.headers["x-api-key"], KEY);
  assert.equal(c.init.headers["anthropic-dangerous-direct-browser-access"], "true");
  assert.equal(c.init.headers["anthropic-version"], "2023-06-01");
  assert.equal(c.init.credentials, "omit");
  assert.equal(c.init.referrerPolicy, "no-referrer");
  assert.equal(c.init.cache, "no-store");
});

test("every failure becomes one of the board's own sentences, and none carries the key", async () => {
  const cases = [
    [{ status: 401, body: { type: "error", error: { type: "authentication_error", message: "invalid x-api-key" } } }, "key"],
    [{ status: 403, body: { type: "error", error: { type: "permission_error", message: "no" } } }, "forbidden"],
    [{ status: 404, body: { type: "error", error: { type: "not_found_error", message: "model: claude-haiku-4-5" } } }, "model"],
    [{ status: 413, body: {} }, "big"],
    [{ status: 429, body: { type: "error", error: { type: "rate_limit_error", message: "slow down" } } }, "rate"],
    [{ status: 529, body: { type: "error", error: { type: "overloaded_error", message: "Overloaded" } } }, "busy"],
    [{ status: 500, raw: true }, "busy"],
    [{ status: 400, body: { type: "error", error: { type: "invalid_request_error", message: "Your credit balance is too low to access the Anthropic API." } } }, "credit"],
    [{ status: 400, body: { type: "error", error: { type: "invalid_request_error", message: "messages: text content blocks must be non-empty" } } }, "refused"],
    [{ status: 200, body: { content: [{ type: "text", text: "I would rather talk." }], stop_reason: "end_turn" } }, "nothing"],
    [{ status: 200, body: toolUse({}, { stop_reason: "max_tokens" }) }, "big"],
    [new TypeError("Failed to fetch"), "network"],
  ];
  for (const [answer, want] of cases) {
    const r = await callDrawer({ key: KEY, request: request(), fetchImpl: fakeFetch(answer) });
    assert.equal(r.error, want, JSON.stringify(answer).slice(0, 80));
    assert.ok(ERRORS[r.error], `a sentence for ${r.error}`);
    assert.ok(!JSON.stringify(r).includes(KEY.slice(12)), "the key never comes back out");
  }
  // An abort, the way a browser does it: fetch rejects with the reason the
  // signal was aborted with, which is a string here, not an AbortError.
  const aborting = async (url, init) => { throw init.signal.reason; };
  const ctl = new AbortController(); ctl.abort("timeout");
  assert.equal((await callDrawer({ key: KEY, request: request(), fetchImpl: aborting, signal: ctl.signal })).error, "timeout");
  const ctl2 = new AbortController(); ctl2.abort("stopped");
  assert.equal((await callDrawer({ key: KEY, request: request(), fetchImpl: aborting, signal: ctl2.signal })).error, "stopped");
  // And with no reason at all it is a DOMException named AbortError.
  const ctl3 = new AbortController(); ctl3.abort();
  assert.equal((await callDrawer({ key: KEY, request: request(), fetchImpl: aborting, signal: ctl3.signal })).error, "stopped");
});

test("a model that refuses forced tool use is asked once more with auto, and still only draws", async () => {
  const refuse = { status: 400, body: { type: "error", error: { type: "invalid_request_error", message: "tool_choice: forced tool use is not supported for this model" } } };
  const input = { boxes: [], parts: [{ id: "q", part: "sqs" }], arrows: [] };
  const f = fakeFetch(refuse, { status: 200, body: toolUse(input) });
  const r = await callDrawer({ key: KEY, request: request(), fetchImpl: f });
  assert.equal(f.calls.length, 2);
  assert.deepEqual(f.calls[0].body.tool_choice, { type: "tool", name: "draw" });
  assert.deepEqual(f.calls[1].body.tool_choice, { type: "auto" });
  assert.deepEqual(r.input, input); assert.equal(r.fellBack, true);
  // Once, not forever: a second refusal is reported, not retried.
  const g = fakeFetch(refuse, refuse, refuse);
  assert.equal((await callDrawer({ key: KEY, request: request(), fetchImpl: g })).error, "refused");
  assert.equal(g.calls.length, 2);
  // And an unrelated 400 is not mistaken for it.
  const h = fakeFetch({ status: 400, body: { error: { type: "invalid_request_error", message: "max_tokens: too large" } } });
  assert.equal((await callDrawer({ key: KEY, request: request(), fetchImpl: h })).error, "refused");
  assert.equal(h.calls.length, 1);
});

// ------------------------------------------------------------- validation
test("validation keeps what is drawable and drops the rest, without throwing", () => {
  const v = validateDrawing({
    boxes: [
      { id: "vpc", kind: "vpc" }, { id: "a", kind: "az", inside: "vpc" }, { id: "z", kind: "moon" },
      { id: "loop1", kind: "private", inside: "loop2" }, { id: "loop2", kind: "public", inside: "loop1" },
      { id: "cloud", kind: "cloud" },                                     // empty: dropped
    ],
    parts: [
      { id: "u", part: "users" }, { id: "api", part: "ecs", inside: "a", name: "ECS" }, { id: "db", part: "rds", inside: "vpc", multiAz: true },
      { id: "q", part: "sqs", multiAz: true }, { id: "ghost", part: "floppy-disk" }, { id: "api", part: "lambda" },
      { id: "bad id!", part: "s3", inside: "nowhere" }, "junk", null,
    ],
    arrows: [
      { from: "u", to: "api", label: "  POST   /bookmarks  ", guards: ["timeout", "teleport", "timeout"] }, { from: "api", to: "db" },
      { from: "api", to: "api" }, { from: "api", to: "ghost" }, { from: "u", to: "api" }, { from: "bad id!", to: "q" },
    ],
  }, index);
  assert.deepEqual(v.boxes.map((b) => b.kind), ["vpc", "az", "private", "public"]);
  assert.equal(v.boxes.find((b) => b.kind === "az").name, "us-east-1a", "zones get names");
  const loops = v.boxes.filter((b) => b.kind === "private" || b.kind === "public");
  assert.ok(loops.some((b) => !b.inside), "a loop of boxes is broken");
  assert.deepEqual(v.parts.map((p) => p.part), ["users", "ecs", "rds", "sqs", "s3"]);
  assert.equal(v.parts[1].name, "", "a name that only repeats AWS's is dropped");
  assert.equal(v.parts[2].multiAz, true);
  assert.equal("multiAz" in v.parts[3], false, "multiAz only on parts that have it");
  const s3 = v.parts[4];
  assert.match(s3.id, /^n\d+$/, "an unusable id is replaced"); assert.equal(s3.inside, "");
  assert.deepEqual(v.arrows.map((a) => [a.from, a.to]), [["u", "api"], ["api", "db"], [s3.id, "q"]], "arrows follow a renamed id; self, unknown and repeated arrows go");
  assert.equal(v.arrows[0].label, "POST /bookmarks");
  assert.deepEqual(v.arrows[0].guards, ["timeout"]);
  for (const junk of [null, undefined, "x", 3, [], { boxes: "no" }]) assert.deepEqual(validateDrawing(junk, index), { boxes: [], parts: [], arrows: [] });
});

test("an AWS Cloud box Haiku adds is unwrapped, unless the board had one or the reader asked", () => {
  const drawing = { boxes: [{ id: "c", kind: "cloud" }, { id: "v", kind: "vpc", inside: "c" }], parts: [{ id: "f", part: "lambda", inside: "c" }, { id: "e", part: "ecs", inside: "v" }], arrows: [] };
  const off = validateDrawing(drawing, index);
  assert.deepEqual(off.boxes.map((b) => [b.id, b.inside]), [["v", ""]]);
  assert.deepEqual(off.parts.map((p) => [p.id, p.inside]), [["f", ""], ["e", "v"]], "what was in it moves up a level");
  const on = validateDrawing(drawing, index, { keepCloud: true });
  assert.deepEqual(on.boxes.map((b) => b.id), ["c", "v"]);
  assert.equal(validateDrawing({ boxes: [{ id: "c", kind: "cloud" }], parts: [], arrows: [] }, index, { keepCloud: true }).boxes.length, 0, "empty, it goes anyway");
  assert.equal(wantsCloud({ groups: [] }, ["put it all in the aws cloud"]), true);
  assert.equal(wantsCloud({ groups: [] }, ["CloudFront in front of S3, logs to CloudWatch"]), false);
  assert.equal(wantsCloud({ groups: [{ part: "cloud" }] }, []), true);
});

// ----------------------------------------------- the board, and back again
test("the board as the model sees it: containment read from where things are drawn", () => {
  const d = diagramFromState(REFERENCE["read-traffic-grows"], index);
  const by = (id) => d.parts.find((p) => p.id === id);
  assert.equal(by("apia").inside, "priva");
  assert.equal(by("alb").inside, "vpc");
  assert.equal(by("user").inside, undefined);
  assert.equal(by("db").multiAz, true);
  assert.equal(d.boxes.find((b) => b.id === "priva").inside, "aza");
  assert.equal(d.boxes.find((b) => b.id === "aza").inside, "vpc");
  assert.equal(d.boxes.find((b) => b.id === "vpc").inside, undefined);
  const g = diagramFromState(REFERENCE["refresh-takes-seconds"], index);
  assert.deepEqual(g.arrows.find((a) => a.to === "site").guards, ["timeout", "retries"]);
});

// What the checks read from a drawing: which zone, subnet and VPC each part
// is in. The layout must put every part where the drawing said it was.
function placeOf(state, id) { const m = buildModel(state, index), p = m.place(id); return [p.zone ? p.zone.id : null, p.subnet ? p.subnet.id : null, p.vpc ? p.vpc.id : null]; }
function wantedPlace(d, id) {
  const box = (bid) => d.boxes.find((b) => b.id === bid);
  const chain = []; for (let at = (d.parts.find((p) => p.id === id) || {}).inside; at; at = (box(at) || {}).inside) chain.push(box(at));
  const first = (...kinds) => (chain.find((b) => kinds.includes(b.kind)) || {}).id;
  return [first("az") ?? null, first("public", "private") ?? null, first("vpc") ?? null];
}
const drawings = {
  ...Object.fromEntries(Object.entries(REFERENCE).map(([k, s]) => [k, validateDrawing(diagramFromState(s, index), index)])),
  ...Object.fromEntries(Object.entries(HAIKU).map(([k, h]) => [k, validateDrawing(h.input, index)])),
};

for (const [name, d] of Object.entries(drawings)) {
  test(`${name}: laid out inside the canvas, every part in the box it was drawn in, nothing on top of anything`, () => {
    const s = drawingToState(d, { index, current: null, measure });
    assert.equal(s.fits, true, "fits the canvas, zoomed out if need be, without squeezing");
    const CW = s.canvas ? s.canvas.w : 860, CH = s.canvas ? s.canvas.h : 540;
    if (s.canvas) assert.ok(CW > 860 && CW <= 860 * 1.6 && Math.abs(CH / CW - 540 / 860) < 0.01, `a zoomed canvas keeps the board's shape: ${CW}x${CH}`);
    for (const n of s.nodes) {
      assert.ok(n.x >= 22 && n.x <= CW - 22 && n.y >= 22 && n.y <= CH - 40, `${n.id} at ${n.x},${n.y} is on the ${CW}x${CH} canvas`);
      assert.deepEqual(placeOf(s, n.id), wantedPlace(d, n.id), `${n.id} is where the drawing put it`);
    }
    for (const g of s.groups) assert.ok(g.x >= 0 && g.y >= 0 && g.x + g.w <= CW && g.y + g.h <= CH, `${g.id} is on the canvas`);
    // Boxes nest as drawn, and siblings do not overlap.
    const G = new Map(s.groups.map((g) => [g.id, g]));
    for (const b of d.boxes) if (b.inside && G.has(b.inside)) {
      const g = G.get(b.id), p = G.get(b.inside);
      assert.ok(g.x >= p.x && g.y >= p.y && g.x + g.w <= p.x + p.w && g.y + g.h <= p.y + p.h, `${b.id} sits inside ${b.inside}`);
    }
    for (const a of s.groups) for (const b of s.groups) {
      if (a.id >= b.id) continue;
      const nested = (x, y) => x.x >= y.x && x.y >= y.y && x.x + x.w <= y.x + y.w && x.y + x.h <= y.y + y.h;
      const apart = a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y;
      assert.ok(apart || nested(a, b) || nested(b, a), `${a.id} and ${b.id} overlap without one holding the other`);
    }
    // Parts (icon and labels) do not overlap, and no arrow runs through a part.
    const block = (n) => { const { top, sub } = partLabels(index.parts.get(n.part), n.name), w = Math.max(44, measure(top, "name"), sub ? measure(sub, "part") : 0) / 2; return [n.x - w, n.y - 22, n.x + w, n.y + (sub ? 56 : 42)]; };
    for (const a of s.nodes) for (const b of s.nodes) {
      if (a.id >= b.id) continue;
      const [a0, a1, a2, a3] = block(a), [b0, b1, b2, b3] = block(b);
      assert.ok(a2 <= b0 || b2 <= a0 || a3 <= b1 || b3 <= a1, `${a.id} and ${b.id} overlap`);
    }
    const N = new Map(s.nodes.map((n) => [n.id, n]));
    for (const e of s.edges) for (const n of s.nodes) {
      if (n.id === e.from || n.id === e.to) continue;
      const a = N.get(e.from), b = N.get(e.to), [x0, y0, x1, y1] = [n.x - 22, n.y - 22, n.x + 22, n.y + 22];
      assert.ok(!segmentHits(a, b, x0, y0, x1, y1), `${e.from} -> ${e.to} runs through ${n.id}'s icon`);
    }
  });
}
function segmentHits(a, b, x0, y0, x1, y1) {
  let t0 = 0, t1 = 1; const dx = b.x - a.x, dy = b.y - a.y;
  for (const [p, q] of [[-dx, a.x - x0], [dx, x1 - a.x], [-dy, a.y - y0], [dy, y1 - a.y]]) {
    if (p === 0) { if (q < 0) return false; continue; }
    const r = q / p;
    if (p < 0) { if (r > t1) return false; if (r > t0) t0 = r; } else { if (r < t0) return false; if (r < t1) t1 = r; }
  }
  return t0 <= t1;
}

test("a pipeline that loops back to its bucket still reads left to right, and only the loop's own arrow goes back", () => {
  // Haiku's video pipeline: Users -> S3 -> Lambda -> SQS -> ECS -> S3 again.
  const s = drawingToState(drawings["q2-dlq"], { index, current: null, measure });
  const x = Object.fromEntries(s.nodes.map((n) => [n.id, n.x]));
  assert.ok(x.users < x.s3 && x.s3 < x.lambda && x.lambda < x.sqs && x.sqs < x.ecs, JSON.stringify(x));
  const backwards = s.edges.filter((e) => x[e.to] < x[e.from]).map((e) => `${e.from}>${e.to}`);
  assert.deepEqual(backwards, ["ecs>s3"]);
});

test("a VPC's front door sits above its zones, whatever its step", () => {
  const s = drawingToState(drawings["p6-network"], { index, current: null, measure });
  const zones = s.groups.filter((g) => g.part === "az"), top = Math.min(...zones.map((z) => z.y));
  for (const id of ["alb1", "igw1"]) assert.ok(s.nodes.find((n) => n.id === id).y < top, `${id} is above the zones`);
  const users = s.nodes.find((n) => n.id === "users1"), vpc = s.groups.find((g) => g.part === "vpc");
  assert.ok(users.x < vpc.x, "Users is left of the VPC, not under it");
});

test("the layout is the same every time, and a part swapped for another kind moves nothing", () => {
  const d = drawings["p1-alb-ecs-rds"];
  const one = drawingToState(d, { index, current: null, measure }), two = drawingToState(d, { index, current: null, measure });
  assert.deepEqual(one, two);
  // "oh no, i meant a cache, not a database": Haiku's real answer.
  const swapped = drawings["p2-meant-cache"];
  assert.equal(swapped.parts.find((p) => p.id === "rds1").part, "elasticache", "Haiku kept the id and changed the part");
  const after = drawingToState(swapped, { index, current: one, measure });
  const pos = (s) => Object.fromEntries([...s.nodes.map((n) => [n.id, [n.x, n.y]]), ...s.groups.map((g) => [g.id, [g.x, g.y, g.w, g.h]])]);
  const [p1, p2] = [pos(one), pos(after)];
  // Only the swapped part's labels changed width; the boxes and every other part stay.
  for (const k of Object.keys(p1)) if (k !== "rds1") assert.deepEqual(p2[k], p1[k], `${k} moved`);
  assert.deepEqual(after.edges.map((e) => e.id), one.edges.map((e) => e.id), "arrows keep their ids");
});

test("an arrangement the reader made by hand survives an edit that only changes kinds, names or arrows", () => {
  const laid = drawingToState(drawings["p1-alb-ecs-rds"], { index, current: null, measure });
  const moved = JSON.parse(JSON.stringify(laid));
  const u = moved.nodes.find((n) => n.id === "users1"); u.y += 60;       // the reader dragged Users down
  const after = drawingToState(drawings["p2-meant-cache"], { index, current: moved, measure });
  assert.deepEqual(after.nodes.find((n) => n.id === "users1"), u, "Users stays where the reader put it");
  assert.equal(after.nodes.find((n) => n.id === "rds1").part, "elasticache");
  // ...but a change of shape (a new part) lays the whole drawing out again.
  const bigger = { ...drawings["p2-meant-cache"], parts: [...drawings["p2-meant-cache"].parts, { id: "q9", part: "sqs", name: "", inside: "" }] };
  const again = drawingToState(bigger, { index, current: moved, measure });
  assert.notDeepEqual(again.nodes.find((n) => n.id === "users1"), u, "a new part means a fresh layout");
  // And a board nobody moved is simply laid out again.
  const fresh = drawingToState(drawings["p2-meant-cache"], { index, current: laid, measure });
  assert.deepEqual(fresh.nodes.find((n) => n.id === "users1"), laid.nodes.find((n) => n.id === "users1"));
});

test("an empty answer clears the board, and an empty board is laid out as nothing", () => {
  const s = drawingToState({ boxes: [], parts: [], arrows: [] }, { index, current: REFERENCE["bookmark-survives-restart"], measure });
  assert.deepEqual([s.nodes, s.groups, s.edges], [[], [], []]);
  assert.equal(drawingToState({ boxes: [], parts: [], arrows: [] }, { index, current: empty, measure }).fits, true);
});

test("placeDrawing measures names, boxes and chips with the board's own measure", () => {
  const seen = new Set();
  placeDrawing(drawings["dependency-slow"], index, (t, k) => { seen.add(k); return measure(t, k); });
  assert.deepEqual([...seen].sort(), ["box", "edge", "name", "part"]);
});
