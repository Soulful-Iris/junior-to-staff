// The design board: draw an architecture with AWS's own parts, check it, then
// break it. Desktop only; everywhere else the page keeps its static sketches.
//
// The editor's state IS the graph the checks read (model.js), so nothing can
// drift between what is drawn and what is judged. Hand-written SVG, because
// the need is small and fixed and every gesture needs its own check anyway
// (site/tools/designboard-check.mjs), which is what a library would not give.
import CATALOG from "./catalog.json";
import ICONS from "designboard:icons";
import BOARD_CSS from "./board.css";
import { catalogIndex, buildModel, GUARDS, KINDS } from "./model.js";
import { runChecks, CHECKS } from "./checks.js";
import { simulate, CAPABILITIES, FAILS, zonal, multiAzOn } from "./sim.js";
import { icon } from "./ui-icons.js";

const INDEX = catalogIndex(CATALOG);
const W = 860, H = 540, ICON = 44, HALF = ICON / 2;
const DESKTOP = "(min-width: 1024px) and (hover: hover) and (pointer: fine)";
const MOD = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Ctrl";
const TIMER_SECONDS = 120;
const HISTORY = 60;
const GROUP_SIZE = { region: [800, 500], vpc: [620, 420], az: [280, 360], "public-subnet": [240, 130], "private-subnet": [240, 170], asg: [240, 150], cloud: [820, 520] };
const GUARD_LABEL = { timeout: "Timeout", retries: "Retries", breaker: "Circuit breaker", fallback: "Fallback" };
const GUARD_SHORT = { timeout: "timeout", retries: "retries", breaker: "breaker", fallback: "fallback" };
const STATUS = { pass: ["circle-check", "Holds"], fail: ["circle-x", "Does not hold"], wait: ["circle-dashed", "Waiting"], todo: ["circle-dashed", "Not checked"] };
const CAP = { ok: ["circle-check", "works"], slow: ["hourglass", "slow"], degraded: ["circle-alert", "degraded"], paused: ["pause", "paused"], down: ["circle-x", "down"], na: ["circle-dashed", "not on the board yet"] };

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const el = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const snap = (v) => Math.round(v / 4) * 4;
const clone = (x) => JSON.parse(JSON.stringify(x));
const md = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");

// Icons are images from data URLs: each one keeps its own ids to itself, and
// is exactly AWS's file.
const URLS = new Map();
const iconUrl = (file) => {
  if (!URLS.has(file)) URLS.set(file, ICONS[file] ? "data:image/svg+xml;charset=utf-8," + encodeURIComponent(ICONS[file]) : "");
  return URLS.get(file);
};

let measureCtx = null;
function textWidth(s, font) {
  measureCtx ||= document.createElement("canvas").getContext("2d");
  measureCtx.font = font;
  return measureCtx.measureText(s).width;
}
const NAME_FONT = "600 12px Inter, ui-sans-serif, -apple-system, 'Segoe UI', sans-serif";
const PART_FONT = "400 11px Inter, ui-sans-serif, -apple-system, 'Segoe UI', sans-serif";
const EDGE_FONT = "500 10.5px ui-monospace, Menlo, Consolas, monospace";

// Where an arrow leaves a part heading for (bx, by). A part is its icon and,
// under it, its labels: an arrow that leaves downwards starts below the
// labels, so it never runs through the part's own name.
function exitPoint(ax, ay, bx, by, below = 0, halfLabel = HALF) {
  const dx = bx - ax, dy = by - ay;
  if (!dx && !dy) return [ax, ay];
  const pad = HALF + 5;
  const along = (hw, top, bottom) => Math.min(dx ? hw / Math.abs(dx) : Infinity, dy > 0 ? bottom / dy : dy < 0 ? top / -dy : Infinity);
  let t = along(pad, pad, pad);
  const y = ay + dy * t, x = ax + dx * t;
  if (below && dy > 0 && y >= ay + pad - 0.5 && Math.abs(x - ax) <= halfLabel + 4) t = along(halfLabel + 4, pad, HALF + below + 4);
  return [ax + dx * t, ay + dy * t];
}

// ------------------------------------------------------------------- board
class Board {
  constructor(mount, data) {
    this.mount = mount; this.data = data; this.x = data.exercise;
    this.key = `j2s-designboard:v1:${data.page}:${this.x.id}`;
    this.state = this.load() || { nodes: [], groups: [], edges: [] };
    this.undoStack = []; this.redoStack = [];
    this.sel = null;                 // { type: "node"|"edge"|"group", id }
    this.mode = "draw";              // or "break"
    this.failed = { nodes: new Set(), groups: new Set() };
    this.results = null; this.live = false; this.selCheck = null; this.checkedAt = 0;
    this.tip = null; this.hoverRef = null;
    this.timer = { state: "off", left: TIMER_SECONDS, started: 0, handle: null };
    this.build();
    this.render();
  }

  // ------------------------------------------------------------- storage
  load() { try { const s = JSON.parse(localStorage.getItem(this.key) || "null"); return s && s.state ? s.state : null; } catch { return null; } }
  save() {
    try {
      const empty = !this.state.nodes.length && !this.state.groups.length;
      if (empty) localStorage.removeItem(this.key);
      else localStorage.setItem(this.key, JSON.stringify({ state: this.state, at: Date.now() }));
    } catch { /* private mode: the board still works, it just forgets */ }
    // The next sketch offers to start from this one; tell it this one changed.
    for (const other of BOARDS) if (other !== this && other.data.previous && other.data.previous.id === this.x.id) other.renderLayer();
  }
  previous() {
    const prev = this.data.previous;
    if (!prev) return null;
    try { const s = JSON.parse(localStorage.getItem(`j2s-designboard:v1:${this.data.page}:${prev.id}`) || "null"); return s && s.state && (s.state.nodes.length || s.state.groups.length) ? s.state : null; } catch { return null; }
  }

  // Every change goes through here: one undo step, a save, a redraw, and the
  // checks again if they are live.
  change(fn, { keepSel = true } = {}) {
    this.undoStack.push(clone(this.state));
    if (this.undoStack.length > HISTORY) this.undoStack.shift();
    this.redoStack = [];
    fn(this.state);
    if (!keepSel) this.sel = null;
    this.afterChange();
  }
  afterChange() {
    if (this.sel && !this.find(this.sel)) this.sel = null;
    this.stripNote = null;
    this.save();
    if (this.live) this.check({ quiet: true });
    this.render();
  }
  undo() { if (!this.undoStack.length) return; this.redoStack.push(clone(this.state)); this.state = this.undoStack.pop(); this.afterChange(); }
  redo() { if (!this.redoStack.length) return; this.undoStack.push(clone(this.state)); this.state = this.redoStack.pop(); this.afterChange(); }

  nextId(prefix) {
    const used = new Set([...this.state.nodes, ...this.state.groups, ...this.state.edges].map((x) => x.id));
    for (let i = 1; ; i++) if (!used.has(prefix + i)) return prefix + i;
  }
  find(sel) {
    if (!sel) return null;
    const list = sel.type === "node" ? this.state.nodes : sel.type === "edge" ? this.state.edges : this.state.groups;
    return list.find((x) => x.id === sel.id) || null;
  }
  model() { return buildModel(this.state, INDEX); }

  // ---------------------------------------------------------------- build
  build() {
    const x = this.x;
    this.root = el(`<section class="db" aria-label="Design board: ${esc(x.title)}">
      <div class="db-cap">
        <div class="db-cap-l"><span class="db-kicker">${icon("spline", 14, "", 2)}Design board</span><span class="db-title">${esc(x.title)}</span></div>
        <div class="db-cap-r">
          <span class="db-timer-wrap"><button type="button" class="db-btn db-ghost db-timer" data-act="timer" title="Draw the happy path in two minutes: start, pause, and start again">${icon("hourglass", 14)}<span class="db-timer-t tn">2:00</span></button><button type="button" class="db-x db-timer-reset" data-act="timer-reset" aria-label="Reset the timer" hidden>${icon("x", 12, "", 2.25)}</button></span>
          <button type="button" class="db-btn db-ghost" data-act="break" aria-pressed="false">${icon("zap", 14)}Break it</button>
          <button type="button" class="db-btn db-ghost" data-act="tip">${icon("lightbulb", 14)}Get a tip</button>
          <button type="button" class="db-btn db-ghost" data-act="reset">${icon("rotate-ccw", 14)}Reset</button>
          <button type="button" class="db-btn db-primary" data-act="check">${icon("circle-check", 14, "", 2.25)}Check design<span class="db-kbd">${MOD} ↵</span></button>
        </div>
      </div>
      <p class="db-brief">${md(x.brief)}</p>
      <div class="db-body">
        <aside class="db-rail" aria-label="Parts"><div class="db-rail-in">
          <label class="db-search">${icon("search", 14)}<span class="sr-only">Search parts</span><input type="search" placeholder="Search: alb, redis, kafka…" autocomplete="off" spellcheck="false"></label>
          <div class="db-parts"></div>
        </div></aside>
        <div class="db-stage" tabindex="-1">
          <svg class="db-svg" viewBox="0 0 ${W} ${H}" role="application" aria-label="Diagram canvas. Parts, boxes and arrows you draw."></svg>
          <div class="db-layer"></div>
        </div>
      </div>
      <div class="db-strip" aria-live="polite"><div class="db-strip-l"></div><div class="db-strip-r">${icon("corner-down-right", 13)}<span><b>A → B</b> means A sends a request or a message to B; the answer rides back on it.</span></div></div>
      <div class="db-tip" hidden aria-live="polite"></div>
      <div class="db-results"><div class="db-list" role="listbox" aria-label="Checks"></div><div class="db-detail"></div></div>
      <div class="db-credit">Parts: AWS Architecture Icons, used under AWS's terms for architecture diagrams. What an arrow carries is yours to write: it is shown, never graded.</div>
    </section>`);
    this.mount.replaceChildren(this.root);
    this.root.dbBoard = this;             // for site/tools/designboard-check.mjs
    const q = (s) => this.root.querySelector(s);
    this.svg = q(".db-svg"); this.stage = q(".db-stage"); this.layer = q(".db-layer");
    this.partsBox = q(".db-parts"); this.search = q(".db-search input");
    this.stripL = q(".db-strip-l"); this.tipBox = q(".db-tip"); this.list = q(".db-list"); this.detail = q(".db-detail");
    this.renderPalette("");

    q('[data-act="check"]').addEventListener("click", () => this.check());
    q('[data-act="reset"]').addEventListener("click", () => this.reset());
    q('[data-act="tip"]').addEventListener("click", () => this.showTip(this.tip ? this.tip.k + 1 : 0));
    q('[data-act="break"]').addEventListener("click", () => this.setMode(this.mode === "break" ? "draw" : "break"));
    q('[data-act="timer"]').addEventListener("click", () => this.timerToggle());
    q('[data-act="timer-reset"]').addEventListener("click", () => this.timerReset());
    this.search.addEventListener("input", () => this.renderPalette(this.search.value));
    this.search.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { const first = this.partsBox.querySelector(".db-part"); if (first) { e.preventDefault(); this.addFromPalette(first.dataset.kind, first.dataset.id); } }
      if (e.key === "Escape") { this.search.value = ""; this.renderPalette(""); }
    });
    this.root.addEventListener("keydown", (e) => this.onKey(e));
    this.svg.addEventListener("pointerdown", (e) => this.onDown(e));
    this.svg.addEventListener("dblclick", (e) => this.onDouble(e));
    this.svg.addEventListener("pointermove", (e) => this.onHover(e));
    this.svg.addEventListener("pointerleave", () => { if (this.hoverNode && !this.connectFrom) { this.hoverNode = null; this.svg.querySelectorAll(".db-node.is-hot").forEach((x) => x.classList.remove("is-hot")); } });
    this.svg.addEventListener("focusin", (e) => { const g = e.target.closest("[data-node],[data-edge],[data-group]"); if (g) this.focusId = g.dataset.node || g.dataset.edge || g.dataset.group; });
    this.detail.addEventListener("mouseover", (e) => { const r = e.target.closest(".db-ref"); this.setHoverRef(r ? r.dataset.ref : null); });
    this.detail.addEventListener("mouseleave", () => this.setHoverRef(null));
    this.detail.addEventListener("click", (e) => {
      const r = e.target.closest(".db-ref");
      if (r) { const id = r.dataset.ref; this.select(this.state.nodes.some((n) => n.id === id) ? { type: "node", id } : { type: "group", id }); }
    });
    new ResizeObserver(() => this.layout()).observe(this.stage);
  }

  // ---------------------------------------------------------------- palette
  renderPalette(query) {
    const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const hit = (p) => !words.length || words.every((w) => `${p.label} ${p.short} ${p.aliases} ${p.kind}`.toLowerCase().includes(w));
    const tile = (p, kind) => `<button type="button" class="db-part${kind === "group" ? " is-group" : ""}" data-kind="${kind}" data-id="${esc(p.id)}" title="${esc(p.label)}${kind === "part" ? "" : " (a box: drop it, then put parts inside)"}">
        ${p.icon ? `<img src="${iconUrl(p.icon)}" alt="" draggable="false">` : `<span class="db-az-glyph" aria-hidden="true"></span>`}<span>${esc(p.short)}</span></button>`;
    const parts = CATALOG.parts.filter(hit), groups = CATALOG.groups.filter(hit);
    let html = "";
    if (words.length) {
      html += parts.length || groups.length ? `<div class="db-grid">${groups.map((g) => tile(g, "group")).join("")}${parts.map((p) => tile(p, "part")).join("")}</div>`
        : `<p class="db-none">Nothing matches “${esc(query)}”. Try a service name, or what it does: queue, cache, dns.</p>`;
    } else {
      html += `<div class="db-sec">Boxes</div><div class="db-grid">${CATALOG.groups.filter((g) => g.id !== "cloud").map((g) => tile(g, "group")).join("")}</div>`;
      html += `<div class="db-sec">Common parts</div><div class="db-grid">${CATALOG.parts.filter((p) => p.common).map((p) => tile(p, "part")).join("")}</div>`;
      for (const c of CATALOG.categories) {
        const more = CATALOG.parts.filter((p) => !p.common && p.category === c.id);
        if (more.length) html += `<details class="db-more"><summary>${esc(c.label)} <span class="tn">${more.length}</span></summary><div class="db-grid">${more.map((p) => tile(p, "part")).join("")}</div></details>`;
      }
      html += `<details class="db-more"><summary>AWS Cloud box</summary><div class="db-grid">${tile(CATALOG.groups.find((g) => g.id === "cloud"), "group")}</div></details>`;
    }
    this.partsBox.innerHTML = html;
    this.partsBox.querySelectorAll(".db-part").forEach((b) => {
      b.addEventListener("pointerdown", (e) => this.paletteDown(e, b));
      b.addEventListener("click", (e) => { if (!this.dragged) this.addFromPalette(b.dataset.kind, b.dataset.id); this.dragged = false; });
    });
  }

  // A click adds the part where it does not cover another; a drag puts it
  // where it is dropped.
  paletteDown(e, btn) {
    this.dragged = false;
    if (e.button !== 0 || this.mode === "break") return;
    const start = { x: e.clientX, y: e.clientY };
    let ghost = null;
    const move = (ev) => {
      if (!ghost && Math.hypot(ev.clientX - start.x, ev.clientY - start.y) < 4) return;
      if (!ghost) {
        this.dragged = true;
        ghost = el(`<div class="db-dragghost">${btn.querySelector("img") ? `<img src="${btn.querySelector("img").src}" alt="">` : ""}<span>${esc(btn.textContent.trim())}</span></div>`);
        document.body.append(ghost);
      }
      ghost.style.left = ev.clientX + "px"; ghost.style.top = ev.clientY + "px";
      const r = this.svg.getBoundingClientRect();
      this.stage.classList.toggle("is-drop", ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom);
    };
    const up = (ev) => {
      removeEventListener("pointermove", move); removeEventListener("pointerup", up);
      this.stage.classList.remove("is-drop");
      if (!ghost) return;
      ghost.remove();
      const r = this.svg.getBoundingClientRect();
      if (ev.clientX < r.left || ev.clientX > r.right || ev.clientY < r.top || ev.clientY > r.bottom) return;
      const p = this.toLogical(ev);
      this.add(btn.dataset.kind, btn.dataset.id, p.x, p.y);
    };
    addEventListener("pointermove", move); addEventListener("pointerup", up);
  }

  addFromPalette(kind, id) {
    if (this.mode === "break") return;
    if (kind === "group") {
      const [w, h] = GROUP_SIZE[INDEX.groups.get(id).type] || [240, 160];
      return this.add(kind, id, W / 2, H / 2 - 10, { w, h });
    }
    // The first free spot on a loose grid, left to right, top to bottom.
    for (let row = 0; row < 6; row++) for (let col = 0; col < 7; col++) {
      const x = 90 + col * 115, y = 70 + row * 88;
      if (this.state.nodes.every((n) => Math.hypot(n.x - x, n.y - y) > 80)) return this.add(kind, id, x, y);
    }
    return this.add(kind, id, W / 2, H / 2);
  }

  add(kind, partId, x, y) {
    if (kind === "group") {
      const def = INDEX.groups.get(partId);
      const [w, h] = GROUP_SIZE[def.type] || [240, 160];
      const id = this.nextId("g");
      const zones = this.state.groups.filter((g) => (INDEX.groups.get(g.part) || {}).type === "az").length;
      const name = def.type === "az" ? `us-east-1${"abcdef"[zones] || "x"}` : def.type === "region" ? "us-east-1" : "";
      const gx = clamp(snap(x - w / 2), 4, W - w - 4), gy = clamp(snap(y - 14), 4, H - h - 4);
      this.change((s) => s.groups.push({ id, part: partId, name, x: gx, y: gy, w: Math.min(w, W - 8), h: Math.min(h, H - 8) }));
      this.select({ type: "group", id });
    } else {
      const part = INDEX.parts.get(partId);
      const id = this.nextId("n");
      const n = { id, part: partId, name: "", x: clamp(snap(x), 30, W - 30), y: clamp(snap(y), 30, H - 44) };
      if (part.placement === "multiaz" && part.multiAzDefault) n.multiAz = true;
      this.change((s) => s.nodes.push(n));
      this.select({ type: "node", id });
    }
  }

  // ---------------------------------------------------------------- canvas
  toLogical(e) {
    const r = this.svg.getBoundingClientRect();
    return { x: ((e.clientX - r.left) / r.width) * W, y: ((e.clientY - r.top) / r.height) * H };
  }
  layout() {
    const r = this.svg.getBoundingClientRect();
    this.scale = r.width / W || 1;
    this.layer.style.width = r.width + "px"; this.layer.style.height = r.height + "px";
    this.placeToolbar();
  }

  render() {
    const m = this.model();
    this.m = m;
    const sim = this.mode === "break" ? simulate(m, this.failed) : null;
    this.sim = sim;
    const off = this.offenders();
    const sel = this.sel || {};
    const hover = this.hoverRef;
    let out = `<defs>
      <pattern id="db-dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#d7ddd2"/></pattern>
      ${["plain", "sel", "bad", "dead"].map((k) => `<marker id="db-m-${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="db-mk-${k}"/></marker>`).join("")}
    </defs><rect class="db-bg" x="0" y="0" width="${W}" height="${H}" fill="url(#db-dots)"/>`;

    // Boxes, biggest first, so a subnet sits on top of its VPC.
    const groups = [...m.groups.values()].sort((a, b) => b.w * b.h - a.w * a.h);
    for (const g of groups) {
      const d = g.def, failed = this.failed.groups.has(g.id), canFail = FAILS.has(g.type);
      const cls = ["db-group", `t-${g.type}`, sel.type === "group" && sel.id === g.id ? "is-sel" : "", (off.groups || []).includes(g.id) ? "is-bad" : "",
        hover === g.id ? "is-hover" : "", failed ? "is-failed" : "", this.mode === "break" && canFail ? "can-fail" : ""].filter(Boolean).join(" ");
      const label = g.name || d.short || d.label;
      out += `<g class="${cls}" data-group="${esc(g.id)}" tabindex="0" role="button" aria-label="${esc(label)}, ${esc(d.label)}${failed ? ", failed" : ""}">
        <rect class="db-g-body" x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="2" style="--c:${d.color};--f:${d.fill || "transparent"}"/>
        ${d.icon ? `<image href="${iconUrl(d.icon)}" x="${g.x}" y="${g.y}" width="24" height="24"/>` : ""}
        <text class="db-g-label" x="${g.x + (d.icon ? 30 : 8)}" y="${g.y + 16}">${esc(label)}${g.name && g.name !== (d.short || d.label) && d.type !== "az" && d.type !== "region" ? `<tspan class="db-g-kind"> · ${esc(d.short || d.label)}</tspan>` : ""}</text>
        <rect class="db-g-grip" x="${g.x}" y="${g.y}" width="${g.w}" height="24" data-grip="1"/>
        ${failed ? `<text class="db-failed-tag" x="${g.x + g.w - 8}" y="${g.y + 16}" text-anchor="end">✕ failed</text>` : ""}
        ${sel.type === "group" && sel.id === g.id && this.mode === "draw" ? `<rect class="db-resize" x="${g.x + g.w - 7}" y="${g.y + g.h - 7}" width="12" height="12" rx="2" data-resize="${esc(g.id)}"/>` : ""}
      </g>`;
    }

    // Arrows. A pair drawn both ways is pulled apart so both stay visible.
    const body = new Map([...m.nodes.values()].map((n) => [n.id, this.labelBlock(n)]));
    for (const e of m.edges) {
      const a = m.nodes.get(e.from), b = m.nodes.get(e.to);
      const twin = m.edge(e.to, e.from);
      const ba = body.get(a.id), bb = body.get(b.id);
      let [x1, y1] = exitPoint(a.x, a.y, b.x, b.y, ba.h, ba.w / 2), [x2, y2] = exitPoint(b.x, b.y, a.x, a.y, bb.h, bb.w / 2);
      if (twin) { const len = Math.hypot(x2 - x1, y2 - y1) || 1, nx = -(y2 - y1) / len * 6, ny = (x2 - x1) / len * 6; x1 += nx; y1 += ny; x2 += nx; y2 += ny; }
      const isSel = sel.type === "edge" && sel.id === e.id, bad = (off.edges || []).includes(e.id);
      const dead = sim && (sim.down.has(e.from) || sim.down.has(e.to) || ["stuck"].includes(sim.health.get(e.to)));
      const kind = bad ? "bad" : isSel ? "sel" : dead ? "dead" : "plain";
      const guards = GUARDS.filter((k) => (e.guards || {})[k]).map((k) => GUARD_SHORT[k]);
      const text = [e.label, guards.length ? guards.join(" · ") : ""].filter(Boolean).join("  ·  ");
      out += `<g class="db-edge is-${kind}" data-edge="${esc(e.id)}" tabindex="0" role="button" aria-label="Arrow from ${esc(m.name(e.from))} to ${esc(m.name(e.to))}${e.label ? ", " + esc(e.label) : ""}">
        <line class="db-e-hit" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>
        <line class="db-e-line" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" marker-end="url(#db-m-${kind})"/>`;
      if (text) {
        const mx = x1 + (x2 - x1) * 0.42, my = y1 + (y2 - y1) * 0.42, w = textWidth(text, EDGE_FONT) + 10;
        out += `<rect class="db-e-labelbg" x="${mx - w / 2}" y="${my - 9}" width="${w}" height="17" rx="4"/><text class="db-e-label" x="${mx}" y="${my + 3.5}" text-anchor="middle">${esc(text)}</text>`;
      }
      out += `</g>`;
    }

    // Parts: the icon, and under it the reader's name and AWS's.
    for (const n of m.nodes.values()) {
      const isSel = sel.type === "node" && sel.id === n.id;
      const bad = (off.nodes || []).includes(n.id);
      const health = sim ? sim.health.get(n.id) : "ok";
      const failed = this.failed.nodes.has(n.id), down = sim && sim.down.has(n.id);
      const cls = ["db-node", isSel ? "is-sel" : "", bad ? "is-bad" : "", hover === n.id ? "is-hover" : "", down ? "is-down" : "", this.hoverNode === n.id ? "is-hot" : "",
        health === "stuck" ? "is-stuck" : "", health === "slow" ? "is-slow" : "", this.connectFrom === n.id ? "is-source" : "", this.dropTarget === n.id ? "is-target" : ""].filter(Boolean).join(" ");
      const { top, sub } = this.labels(n);
      const multi = n.placement === "multiaz" && multiAzOn(n);
      const w1 = textWidth(top, NAME_FONT), w2 = sub ? textWidth(sub, PART_FONT) : 0;
      const bw = Math.max(ICON + 16, w1 + 12, w2 + 12);
      out += `<g class="${cls}" data-node="${esc(n.id)}" tabindex="0" role="button" aria-label="${esc(top)}, ${esc(n.p.label)}${multi ? ", Multi-AZ" : ""}${down ? ", failed" : ""}">
        <rect class="db-n-hit" x="${n.x - bw / 2}" y="${n.y - HALF - 4}" width="${bw}" height="${ICON + (sub ? 40 : 26)}" rx="6"/>
        <rect class="db-n-ring" x="${n.x - HALF - 4}" y="${n.y - HALF - 4}" width="${ICON + 8}" height="${ICON + 8}" rx="8"/>
        <image class="db-n-icon" href="${iconUrl(n.p.icon)}" x="${n.x - HALF}" y="${n.y - HALF}" width="${ICON}" height="${ICON}"/>
        <text class="db-n-name" x="${n.x}" y="${n.y + HALF + 15}" text-anchor="middle">${esc(top)}</text>
        ${sub ? `<text class="db-n-part" x="${n.x}" y="${n.y + HALF + 29}" text-anchor="middle">${esc(sub)}</text>` : ""}
        ${multi ? `<g class="db-badge db-b-multi"><rect x="${n.x + HALF - 10}" y="${n.y - HALF - 9}" width="44" height="15" rx="7.5"/><text x="${n.x + HALF + 12}" y="${n.y - HALF + 2}" text-anchor="middle">Multi-AZ</text></g>` : ""}
        ${down ? `<g class="db-badge db-b-down"><circle cx="${n.x + HALF}" cy="${n.y - HALF}" r="9"/><path d="M${n.x + HALF - 3.5} ${n.y - HALF - 3.5}l7 7M${n.x + HALF + 3.5} ${n.y - HALF - 3.5}l-7 7"/></g>` : ""}
        ${!down && (health === "stuck" || health === "slow") ? `<g class="db-badge db-b-${health}"><rect x="${n.x - 30}" y="${n.y - HALF - 20}" width="60" height="15" rx="7.5"/><text x="${n.x}" y="${n.y - HALF - 9}" text-anchor="middle">${health === "stuck" ? "waiting" : "slow"}</text></g>` : ""}
        ${this.mode === "draw" ? `<circle class="db-handle" cx="${n.x + HALF + 7}" cy="${n.y}" r="6" data-handle="${esc(n.id)}"><title>Drag to draw an arrow</title></circle>` : ""}
      </g>`;
    }
    if (this.connectLine) {
      const { x1, y1, x2, y2 } = this.connectLine;
      out += `<line class="db-connecting" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" marker-end="url(#db-m-sel)"/>`;
    }
    this.svg.innerHTML = out;
    this.root.classList.toggle("is-break", this.mode === "break");
    this.root.classList.toggle("is-empty", !this.state.nodes.length && !this.state.groups.length);
    const f = this.focusId && this.svg.querySelector(`[data-node="${CSS_ESC(this.focusId)}"],[data-edge="${CSS_ESC(this.focusId)}"],[data-group="${CSS_ESC(this.focusId)}"]`);
    if (f && this.refocus) { f.focus({ preventScroll: true }); this.refocus = false; }
    this.renderLayer();
    this.renderStrip();
    this.renderList();
    this.renderDetail();
  }

  // What is marked red: the selected check's offenders, if it does not hold.
  offenders() {
    if (!this.results || this.mode === "break") return {};
    const r = this.results.find((x) => x.id === this.selCheck);
    return r && r.status === "fail" ? r.offenders : {};
  }

  // The two lines under a part's icon: the reader's name for it (or the AWS
  // short name), then AWS's name when there is something more to say.
  labels(n) {
    const name = (n.name || "").trim();
    const top = name || n.p.short;
    const sub = name ? n.p.short : (n.p.short !== n.p.label && n.p.label.length < 28 ? n.p.label : "");
    return { top, sub };
  }
  labelBlock(n) {
    const { top, sub } = this.labels(n);
    return { w: Math.max(ICON, textWidth(top, NAME_FONT), sub ? textWidth(sub, PART_FONT) : 0), h: sub ? 34 : 20 };
  }

  setHoverRef(id) { if (this.hoverRef === id) return; this.hoverRef = id; this.render(); }

  // ----------------------------------------------------------- the layer
  // The HTML over the canvas: the empty-board hint, the selection's toolbar,
  // and in break-it mode the panel of what still works.
  renderLayer() {
    const layer = this.layer;
    let hint = layer.querySelector(".db-empty");
    const empty = !this.state.nodes.length && !this.state.groups.length;
    if (empty && this.mode === "draw") {
      const prev = this.previous();
      if (!hint) { hint = el(`<div class="db-empty"></div>`); layer.append(hint); }
      hint.innerHTML = `<p>${icon("spline", 18, "", 1.8)}<span>Drag parts in from the left, or click one. Then drag from a part's dot to the part it calls.</span></p>
        ${prev ? `<button type="button" class="db-btn db-ghost" data-act="continue">${icon("copy-plus", 14)}Start from ${esc(this.data.previous.label)}</button>` : ""}`;
      const b = hint.querySelector('[data-act="continue"]');
      if (b) b.addEventListener("click", () => this.change((s) => { const p = this.previous(); s.nodes = p.nodes; s.groups = p.groups; s.edges = p.edges; }));
    } else if (hint) hint.remove();
    this.renderToolbar();
  }

  renderToolbar() {
    const key = this.mode === "draw" && this.sel ? `${this.sel.type}:${this.sel.id}` : "";
    if (this.toolbar && this.toolbar.dataset.key === key) { this.syncToolbar(); return this.placeToolbar(); }
    if (this.toolbar) { this.toolbar.remove(); this.toolbar = null; }
    if (!key) return;
    const item = this.find(this.sel);
    if (!item) return;
    let html = "";
    if (this.sel.type === "node") {
      const part = INDEX.parts.get(item.part);
      const others = this.state.nodes.filter((n) => n.id !== item.id);
      html = `<input class="db-tb-name" type="text" value="${esc(item.name || "")}" placeholder="Name this ${esc(part.short)}" aria-label="Name" maxlength="40" spellcheck="false">
        ${part.placement === "multiaz" ? `<button type="button" class="db-chip" data-tb="multiaz" aria-pressed="${!!multiAzOn({ ...item, p: part })}" title="A standby in another Availability Zone takes over if this one's zone fails">Multi-AZ</button>` : ""}
        <select class="db-tb-connect" aria-label="Connect to"><option value="">Connect to…</option>${others.map((n) => `<option value="${esc(n.id)}">${esc(this.m.name(n.id))}</option>`).join("")}</select>
        <button type="button" class="db-tb-icon" data-tb="delete" aria-label="Delete this part" title="Delete (Del)">${icon("trash-2", 15)}</button>
        <span class="db-tb-kind">${esc(part.label)}</span>`;
    } else if (this.sel.type === "edge") {
      html = `<input class="db-tb-name" type="text" value="${esc(item.label || "")}" placeholder="What it carries" aria-label="What this arrow carries" maxlength="40" spellcheck="false">
        <span class="db-tb-guards" role="group" aria-label="Guards on this call">${GUARDS.map((g) => `<button type="button" class="db-chip" data-tb="guard" data-guard="${g}" aria-pressed="${!!(item.guards || {})[g]}">${GUARD_LABEL[g]}</button>`).join("")}</span>
        <button type="button" class="db-tb-icon" data-tb="reverse" aria-label="Reverse this arrow" title="Reverse">${icon("arrow-left-right", 15)}</button>
        <button type="button" class="db-tb-icon" data-tb="delete" aria-label="Delete this arrow" title="Delete (Del)">${icon("trash-2", 15)}</button>`;
    } else {
      const def = INDEX.groups.get(item.part);
      html = `<input class="db-tb-name" type="text" value="${esc(item.name || "")}" placeholder="${esc(def.label)}" aria-label="Name" maxlength="40" spellcheck="false">
        <button type="button" class="db-tb-icon" data-tb="delete" aria-label="Delete this box" title="Delete the box; what is inside stays">${icon("trash-2", 15)}</button>
        <span class="db-tb-kind">${esc(def.label)}</span>`;
    }
    const tb = el(`<div class="db-toolbar is-${this.sel.type}" data-key="${esc(key)}">${html}</div>`);
    this.toolbar = tb;
    this.layer.append(tb);
    const input = tb.querySelector(".db-tb-name");
    // Typing renames live; the undo step is taken once, when the field is left.
    let before = null;
    input.addEventListener("focus", () => { before = clone(this.state); });
    input.addEventListener("input", () => {
      const it = this.find(this.sel); if (!it) return;
      if (this.sel.type === "edge") it.label = input.value; else it.name = input.value;
      this.save(); if (this.live) this.check({ quiet: true }); this.render();
    });
    input.addEventListener("blur", () => { if (before && JSON.stringify(before) !== JSON.stringify(this.state)) { this.undoStack.push(before); this.redoStack = []; } before = null; });
    input.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === "Escape") { e.preventDefault(); input.blur(); this.refocus = true; this.focusId = this.sel && this.sel.id; this.render(); } });
    tb.querySelectorAll("[data-tb]").forEach((b) => b.addEventListener("click", () => this.toolbarAct(b)));
    const conn = tb.querySelector(".db-tb-connect");
    if (conn) conn.addEventListener("change", () => { if (conn.value) this.connect(this.sel.id, conn.value); conn.value = ""; });
    this.placeToolbar();
  }
  syncToolbar() {
    const item = this.find(this.sel), tb = this.toolbar;
    if (!item || !tb) return;
    tb.querySelectorAll('[data-tb="guard"]').forEach((b) => b.setAttribute("aria-pressed", String(!!(item.guards || {})[b.dataset.guard])));
    const ma = tb.querySelector('[data-tb="multiaz"]');
    if (ma) ma.setAttribute("aria-pressed", String(!!multiAzOn({ ...item, p: INDEX.parts.get(item.part) })));
    const input = tb.querySelector(".db-tb-name");
    const want = this.sel.type === "edge" ? item.label || "" : item.name || "";
    if (document.activeElement !== input && input.value !== want) input.value = want;
  }
  toolbarAct(b) {
    const act = b.dataset.tb, sel = this.sel;
    if (act === "delete") return this.deleteSel();
    if (act === "reverse") return this.change((s) => {
      const e = s.edges.find((x) => x.id === sel.id);
      if (s.edges.some((x) => x.from === e.to && x.to === e.from)) return;
      [e.from, e.to] = [e.to, e.from];
    });
    if (act === "guard") return this.change((s) => { const e = s.edges.find((x) => x.id === sel.id); e.guards = { ...(e.guards || {}), [b.dataset.guard]: !(e.guards || {})[b.dataset.guard] }; });
    if (act === "multiaz") return this.change((s) => { const n = s.nodes.find((x) => x.id === sel.id); n.multiAz = !multiAzOn({ ...n, p: INDEX.parts.get(n.part) }); });
  }
  // The toolbar floats next to what is selected, at the first of a few spots
  // that covers no other part: above, below, to the right, to the left. A
  // toolbar over the part a reader clicks next swallows the click, and nothing
  // on the screen says why.
  placeToolbar() {
    const tb = this.toolbar;
    if (!tb || !this.sel) return;
    const it = this.find(this.sel), s = this.scale || 1;
    if (!it) return;
    const w = tb.offsetWidth / s, h = tb.offsetHeight / s, gap = 8;
    let spots;
    if (this.sel.type === "node") {
      const lb = this.m && this.m.nodes.get(it.id) ? this.labelBlock(this.m.nodes.get(it.id)) : { w: ICON, h: 34 };
      spots = [[it.x - w / 2, it.y - HALF - gap - h], [it.x - w / 2, it.y + HALF + lb.h + gap], [it.x + Math.max(HALF, lb.w / 2) + gap, it.y - h / 2], [it.x - Math.max(HALF, lb.w / 2) - gap - w, it.y - h / 2]];
    } else if (this.sel.type === "group") {
      spots = [[it.x, it.y - gap - h], [it.x + it.w - w, it.y - gap - h], [it.x + it.w - w, it.y + 30], [it.x, it.y + it.h + gap]];
    } else {
      const a = this.state.nodes.find((n) => n.id === it.from), b = this.state.nodes.find((n) => n.id === it.to);
      const mx = a.x + (b.x - a.x) * 0.42, my = a.y + (b.y - a.y) * 0.42;
      spots = [[mx - w / 2, my - 14 - h], [mx - w / 2, my + 14], [mx + 16, my - h / 2], [mx - 16 - w, my - h / 2]];
    }
    const boxes = this.state.nodes.filter((n) => !(this.sel.type === "node" && n.id === it.id)).map((n) => {
      const lb = this.m && this.m.nodes.get(n.id) ? this.labelBlock(this.m.nodes.get(n.id)) : { w: ICON, h: 34 };
      const hw = Math.max(HALF, lb.w / 2) + 4;
      return [n.x - hw, n.y - HALF - 6, n.x + hw, n.y + HALF + lb.h + 4];
    });
    const fits = ([x, y]) => x >= 2 && y >= 2 && x + w <= W - 2 && y + h <= H - 2;
    const clear = ([x, y]) => boxes.every(([x1, y1, x2, y2]) => x + w < x1 || x > x2 || y + h < y1 || y > y2);
    const clamped = ([x, y]) => [clamp(x, 2, W - w - 2), clamp(y, 2, H - h - 2)];
    const pick = spots.find((p) => fits(p) && clear(p)) || spots.map(clamped).find(clear) || clamped(spots[0]);
    tb.style.left = pick[0] * s + "px"; tb.style.top = pick[1] * s + "px";
  }

  // What a member can still do, for break-it mode: evaluated once per render.
  capabilities() {
    return this.x.capabilities.map((c) => ({ ...c, r: CAPABILITIES[c.id](this.sim) }));
  }

  capNote(r, m) {
    const who = r.at ? `<b>${esc(m.name(r.at))}</b>` : "";
    const notes = {
      load: ` · every read now reaches the database`, cached: ` · only what ${who || "the cache"} still holds`,
      waiting: ` · jobs wait in ${who || "the queue"} until a worker is back`, retrying: ` · ${who} retries after each timeout; jobs that never succeed go to the dead-letter queue`,
      hanging: ` · ${who} waits on a call that never answers`, errors: ` · ${who} gives up after its timeout, with an error`,
      "fallback-fast": ` · the breaker is open: ${who} answers with its fallback at once`, "fallback-slow": ` · ${who} answers with its fallback after each timeout`,
    };
    if (r.note && notes[r.note]) return `<span class="db-cap-note">${notes[r.note]}</span>`;
    if (r.status === "slow") return `<span class="db-cap-note"> · waits behind a slow call</span>`;
    return "";
  }

  setMode(mode) {
    this.mode = mode;
    if (mode === "draw") this.failed = { nodes: new Set(), groups: new Set() };
    else { this.sel = null; this.hideTip(); }
    this.root.querySelector('[data-act="break"]').setAttribute("aria-pressed", String(mode === "break"));
    this.render();
  }

  // ------------------------------------------------------------- pointer
  onDown(e) {
    if (e.button !== 0) return;
    // The canvas redraws on almost every press, and a focused element that a
    // redraw replaces takes the focus with it, to the page: then Esc, Delete
    // and the arrow keys never reach the board. So a press never moves focus
    // on its own; it goes to the stage, which is never redrawn.
    e.preventDefault();
    this.stage.focus({ preventScroll: true });
    const t = e.target;
    const handle = t.closest("[data-handle]"), resize = t.closest("[data-resize]");
    const node = t.closest("[data-node]"), edge = t.closest("[data-edge]"), group = t.closest("[data-group]");
    const p = this.toLogical(e);
    if (this.mode === "break") {
      if (node) this.toggleFail("nodes", node.dataset.node);
      else if (group && FAILS.has(this.m.groups.get(group.dataset.group).type)) this.toggleFail("groups", group.dataset.group);
      return;
    }
    if (handle) return this.startConnect(e, handle.dataset.handle, p);
    if (resize) return this.startResize(e, resize.dataset.resize, p);
    if (node) return this.startDrag(e, { type: "node", id: node.dataset.node }, p);
    if (edge) {
      e.preventDefault();
      const id = edge.dataset.edge, now = Date.now(), last = this.lastClick;
      this.lastClick = { id, t: now };
      if (last && last.id === id && now - last.t < 450) { this.lastClick = null; return this.rename({ type: "edge", id }); }
      return this.select({ type: "edge", id });
    }
    if (group && t.closest("[data-grip]") || group && t.classList.contains("db-g-body") && this.nearBorder(this.m.groups.get(group.dataset.group), p)) return this.startDrag(e, { type: "group", id: group.dataset.group }, p);
    this.select(null);
  }
  nearBorder(g, p) { const d = 7; return p.x - g.x < d || g.x + g.w - p.x < d || p.y - g.y < d || g.y + g.h - p.y < d; }

  capture(e, move, up) {
    const id = e.pointerId;
    try { this.svg.setPointerCapture(id); } catch { /* synthetic events */ }
    const mv = (ev) => { if (ev.pointerId === id) move(ev); };
    const u = (ev) => { if (ev.pointerId !== id) return; this.svg.removeEventListener("pointermove", mv); this.svg.removeEventListener("pointerup", u); this.svg.removeEventListener("pointercancel", u); up(ev); };
    this.svg.addEventListener("pointermove", mv); this.svg.addEventListener("pointerup", u); this.svg.addEventListener("pointercancel", u);
  }

  startDrag(e, sel, p) {
    e.preventDefault();
    const item = this.find(sel);
    const before = clone(this.state);
    let moved = false;
    // A box carries what is inside it when it moves.
    const carried = sel.type === "group" ? this.carried(item) : null;
    const origin = { x: item.x, y: item.y, nodes: carried && carried.nodes.map((n) => [n, n.x, n.y]), groups: carried && carried.groups.map((g) => [g, g.x, g.y]) };
    this.capture(e, (ev) => {
      const q = this.toLogical(ev);
      const dx = q.x - p.x, dy = q.y - p.y;
      if (!moved && Math.hypot(dx, dy) < 3) return;
      moved = true;
      if (sel.type === "node") {
        item.x = clamp(snap(origin.x + dx), 26, W - 26); item.y = clamp(snap(origin.y + dy), 26, H - 40);
      } else {
        const ddx = clamp(snap(dx), -origin.x, W - item.w - origin.x), ddy = clamp(snap(dy), -origin.y, H - item.h - origin.y);
        item.x = origin.x + ddx; item.y = origin.y + ddy;
        for (const [n, x, y] of origin.nodes) { n.x = x + ddx; n.y = y + ddy; }
        for (const [g, x, y] of origin.groups) { g.x = x + ddx; g.y = y + ddy; }
      }
      this.sel = sel;
      this.render();
    }, () => {
      if (!moved) {
        const now = Date.now(), last = this.lastClick;
        this.lastClick = { id: sel.id, t: now };
        if (last && last.id === sel.id && now - last.t < 450) { this.lastClick = null; return this.rename(sel); }
        return this.select(sel);
      }
      this.undoStack.push(before); this.redoStack = [];
      this.afterChange();
    });
  }
  carried(g) {
    const inside = (x, y) => x >= g.x && x <= g.x + g.w && y >= g.y && y <= g.y + g.h;
    return {
      nodes: this.state.nodes.filter((n) => inside(n.x, n.y)),
      groups: this.state.groups.filter((o) => o !== g && inside(o.x, o.y) && inside(o.x + o.w, o.y + o.h)),
    };
  }

  startResize(e, id, p) {
    e.preventDefault();
    const g = this.state.groups.find((x) => x.id === id), before = clone(this.state), w0 = g.w, h0 = g.h;
    this.capture(e, (ev) => {
      const q = this.toLogical(ev);
      g.w = clamp(snap(w0 + q.x - p.x), 80, W - g.x - 2); g.h = clamp(snap(h0 + q.y - p.y), 60, H - g.y - 2);
      this.render();
    }, () => { if (g.w !== w0 || g.h !== h0) { this.undoStack.push(before); this.redoStack = []; this.afterChange(); } });
  }

  startConnect(e, from, p) {
    e.preventDefault();
    const a = this.state.nodes.find((n) => n.id === from);
    this.connectFrom = from;
    this.capture(e, (ev) => {
      const q = this.toLogical(ev);
      const over = this.nodeAt(q, from);
      this.dropTarget = over;
      const [x1, y1] = exitPoint(a.x, a.y, q.x, q.y);
      this.connectLine = { x1, y1, x2: q.x, y2: q.y };
      this.render();
    }, (ev) => {
      const to = this.nodeAt(this.toLogical(ev), from);
      this.connectFrom = null; this.connectLine = null; this.dropTarget = null;
      if (to) this.connect(from, to); else this.render();
    });
  }
  nodeAt(q, except) {
    let best = null, bd = 40;
    for (const n of this.state.nodes) {
      if (n.id === except) continue;
      const d = Math.hypot(n.x - q.x, n.y - q.y);
      if (d < bd) { bd = d; best = n.id; }
    }
    return best;
  }
  connect(from, to) {
    if (from === to) return;
    if (this.state.edges.some((e) => e.from === from && e.to === to)) { this.select({ type: "edge", id: this.state.edges.find((e) => e.from === from && e.to === to).id }); return; }
    const id = this.nextId("e");
    this.change((s) => s.edges.push({ id, from, to, label: "", guards: {} }));
    this.select({ type: "edge", id });
  }

  // Double click is detected in startDrag, because each click redraws the
  // canvas and a browser only fires dblclick when both clicks land on the same
  // element. This listener catches the cases a redraw did not interrupt.
  onDouble(e) {
    if (this.mode !== "draw") return;
    const node = e.target.closest("[data-node]"), edge = e.target.closest("[data-edge]"), group = e.target.closest("[data-group]");
    const sel = node ? { type: "node", id: node.dataset.node } : edge ? { type: "edge", id: edge.dataset.edge } : group ? { type: "group", id: group.dataset.group } : null;
    if (sel) this.rename(sel);
  }
  rename(sel) {
    this.select(sel);
    const input = this.toolbar && this.toolbar.querySelector(".db-tb-name");
    if (input) { input.focus(); input.select(); }
  }
  // Which part the pointer is over is state, drawn by render(): a class left
  // on an element vanishes when the next redraw replaces the element, and
  // then the dot never comes back for the part you just drew an arrow from.
  onHover(e) {
    if (this.mode !== "draw" || this.connectFrom) return;
    const n = e.target.closest("[data-node]");
    const id = n ? n.dataset.node : null;
    if (id === this.hoverNode) return;
    this.hoverNode = id;
    this.svg.querySelectorAll(".db-node.is-hot").forEach((x) => x.classList.remove("is-hot"));
    if (n) n.classList.add("is-hot");
  }

  select(sel) {
    this.sel = sel;
    if (sel) { this.focusId = sel.id; }
    this.render();
  }
  deleteSel() {
    const sel = this.sel;
    if (!sel) return;
    this.change((s) => {
      if (sel.type === "node") { s.nodes = s.nodes.filter((n) => n.id !== sel.id); s.edges = s.edges.filter((e) => e.from !== sel.id && e.to !== sel.id); }
      else if (sel.type === "edge") s.edges = s.edges.filter((e) => e.id !== sel.id);
      else s.groups = s.groups.filter((g) => g.id !== sel.id);
    }, { keepSel: false });
    this.stage.focus({ preventScroll: true });
  }
  toggleFail(which, id) {
    const set = this.failed[which];
    if (set.has(id)) set.delete(id); else set.add(id);
    this.render();
  }

  onKey(e) {
    const typing = e.target.matches("input, select, textarea");
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); return this.check(); }
    if (typing) return;
    const mod = e.metaKey || e.ctrlKey;
    if (mod && (e.key === "z" || e.key === "Z")) { e.preventDefault(); return e.shiftKey ? this.redo() : this.undo(); }
    if (mod && (e.key === "y" || e.key === "Y")) { e.preventDefault(); return this.redo(); }
    const g = e.target.closest && e.target.closest("[data-node],[data-edge],[data-group]");
    if ((e.key === "Enter" || e.key === " ") && g) {
      e.preventDefault();
      if (this.mode === "break") { if (g.dataset.node) this.toggleFail("nodes", g.dataset.node); else if (g.dataset.group) this.toggleFail("groups", g.dataset.group); return; }
      this.select(g.dataset.node ? { type: "node", id: g.dataset.node } : g.dataset.edge ? { type: "edge", id: g.dataset.edge } : { type: "group", id: g.dataset.group });
      const input = this.toolbar && this.toolbar.querySelector(".db-tb-name");
      if (input) input.focus();
      return;
    }
    if (e.key === "Escape") { if (this.mode === "break") return this.setMode("draw"); if (this.sel) { e.preventDefault(); return this.select(null); } }
    if ((e.key === "Delete" || e.key === "Backspace") && this.sel && this.mode === "draw") { e.preventDefault(); return this.deleteSel(); }
    const arrows = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
    if (arrows[e.key] && this.sel && this.sel.type !== "edge" && this.mode === "draw") {
      e.preventDefault();
      const [dx, dy] = arrows[e.key].map((v) => v * (e.shiftKey ? 20 : 4));
      const sel = this.sel;
      this.refocus = true;
      this.change((s) => {
        const it = (sel.type === "node" ? s.nodes : s.groups).find((x) => x.id === sel.id);
        if (sel.type === "group") { const c = this.carried(it); for (const n of c.nodes) { n.x += dx; n.y += dy; } for (const o of c.groups) { o.x += dx; o.y += dy; } }
        it.x += dx; it.y += dy;
      });
    }
  }

  reset() {
    if (!this.state.nodes.length && !this.state.groups.length) return;
    const before = clone(this.state);
    this.change((s) => { s.nodes = []; s.groups = []; s.edges = []; }, { keepSel: false });
    this.results = null; this.live = false; this.selCheck = null; this.hideTip();
    this.setStrip(`Cleared. <button type="button" class="db-link" data-act="undo-reset">Undo</button>`);
    this.stripL.querySelector('[data-act="undo-reset"]').addEventListener("click", () => { this.state = before; this.afterChange(); this.stripNote = null; this.renderStrip(); });
  }

  // --------------------------------------------------------------- checks
  check({ quiet = false } = {}) {
    const m = this.model();
    this.results = runChecks(m, this.x.checks);
    this.live = true; this.checkedAt = Date.now();
    if (!quiet || !this.results.some((r) => r.id === this.selCheck)) {
      const bad = this.results.find((r) => r.status === "fail") || this.results.find((r) => r.status === "wait");
      if (!quiet || !this.selCheck) this.selCheck = (bad || this.results[0]).id;
    }
    if (!quiet) { this.hideTip(); this.stripNote = null; this.render(); }
  }

  setStrip(html) { this.stripNote = html; this.stripL.innerHTML = html; }
  renderStrip() {
    if (this.stripNote) { if (!this.stripL.innerHTML) this.stripL.innerHTML = this.stripNote; return; }
    const r = this.results;
    if (this.mode === "break") {
      this.stripL.innerHTML = this.capabilities().map(({ label, r }) => {
        const [ic, word] = CAP[r.status] || CAP.na;
        return `<span class="db-capchip cap-${r.status}">${icon(ic, 14, "", 2.2)}<b>${esc(label)}</b><span>${word}</span></span>`;
      }).join("");
      return;
    }
    if (!r) { this.stripL.innerHTML = `<span>Draw it, then <b>Check design</b> or <b>${MOD} ↵</b>. It saves as you go.</span>`; return; }
    const pass = r.filter((x) => x.status === "pass").length, fail = r.filter((x) => x.status === "fail").length, wait = r.filter((x) => x.status === "wait").length;
    const parts = [`${icon("circle-check", 15, "st-pass", 2.1)}<b class="tn">${pass}</b> of ${r.length} hold`];
    if (fail) parts.push(`${icon("circle-x", 15, "st-fail", 2.1)}<b class="tn">${fail}</b> do${fail === 1 ? "es" : ""} not`);
    if (wait) parts.push(`${icon("circle-dashed", 15, "st-wait", 2.1)}<b class="tn">${wait}</b> waiting`);
    this.stripL.innerHTML = parts.join('<span class="db-sep"></span>') + (pass === r.length ? `<span class="db-sep"></span><span class="db-allgood">Now <button type="button" class="db-link" data-act="go-break">break it</button>.</span>` : `<span class="db-sep"></span><span class="db-live">checking as you draw</span>`);
    const go = this.stripL.querySelector('[data-act="go-break"]');
    if (go) go.addEventListener("click", () => this.setMode("break"));
  }

  renderList() {
    if (this.mode === "break") {
      const n = this.failed.nodes.size + this.failed.groups.size;
      this.list.innerHTML = `<div class="db-list-head">What a member can do <span>${n ? `${n} failed` : "nothing failed yet"}</span></div>` +
        this.capabilities().map(({ label, r }) => {
          const [ic, word] = CAP[r.status] || CAP.na;
          return `<div class="db-caprow cap-${r.status}">${icon(ic, 16, "", 2.1)}<span><b>${esc(label)}</b> <span class="db-cap-word">${word}</span>${this.capNote(r, this.m)}</span></div>`;
        }).join("");
      return;
    }
    const specs = this.x.checks.map((s) => (typeof s === "string" ? { id: s } : s));
    const results = this.results || specs.map((s) => ({ id: s.id, title: s.title || CHECKS[s.id].title, status: "todo" }));
    this.list.innerHTML = `<div class="db-list-head">${results.length} checks <span>for this sketch</span></div>` + results.map((r) => {
      const [ic] = STATUS[r.status];
      return `<button type="button" role="option" class="db-check st-${r.status}" data-check="${esc(r.id)}" aria-selected="${this.selCheck === r.id}">${icon(ic, 16, "st-" + r.status, 2.1)}<span>${esc(r.title)}</span></button>`;
    }).join("");
    this.list.querySelectorAll("[data-check]").forEach((b) => b.addEventListener("click", () => { this.selCheck = b.dataset.check; this.hideTip(); this.render(); }));
  }

  renderDetail() {
    if (this.mode === "break") {
      const n = this.failed.nodes.size + this.failed.groups.size;
      this.detail.innerHTML = `<div class="db-d-head"><span class="db-d-title">${icon("zap", 16)}Break it</span></div>
        ${this.data.breakText ? `<p class="db-bp-prompt">${md(this.data.breakText.charAt(0).toUpperCase() + this.data.breakText.slice(1))}</p>` : ""}
        <p class="db-ask">Click a part, a zone or a subnet on the board to fail it, and again to bring it back. A part of yours that fails is gone. An outside service that fails hangs instead, and whatever calls it without a timeout waits with it.</p>
        <p class="db-bp-act">${n ? `<button type="button" class="db-btn db-ghost" data-bp="restore">${icon("rotate-ccw", 13)}Restore everything</button>` : ""}<button type="button" class="db-btn db-ghost" data-bp="done">Done</button></p>`;
      this.detail.querySelectorAll("[data-bp]").forEach((b) => b.addEventListener("click", () => {
        if (b.dataset.bp === "restore") { this.failed = { nodes: new Set(), groups: new Set() }; this.render(); }
        else this.setMode("draw");
      }));
      return;
    }
    const id = this.selCheck;
    if (!id) {
      this.detail.innerHTML = `<div class="db-guide">${icon("spline", 18, "", 2)}<div>
        <p>Each check is a question a reviewer would ask of this sketch. <b>Check design</b> answers all of them, names the parts that break one, and marks them red on the board.</p>
        <p>Then <b>Break it</b>: fail a part, a subnet or a whole zone, and see what a member can still do.</p></div></div>`;
      return;
    }
    const spec = this.x.checks.map((s) => (typeof s === "string" ? { id: s } : s)).find((s) => s.id === id) || { id };
    const r = this.results && this.results.find((x) => x.id === id);
    const title = (r && r.title) || spec.title || CHECKS[id].title;
    const ask = spec.ask || CHECKS[id].ask;
    const st = r ? r.status : "todo";
    const [ic, word] = STATUS[st];
    const tryZone = r && r.offenders && r.offenders.tryZone;
    this.detail.innerHTML = `<div class="db-d-head"><span class="db-d-title">${esc(title)}</span><span class="db-badge st-${st}">${icon(ic, 13, "", 2.25)}${word}</span></div>
      <p class="db-ask">${esc(ask)}</p>
      ${r ? `<p class="db-why">${r.html}</p>` : ""}
      ${tryZone && this.m.groups.get(tryZone) ? `<p><button type="button" class="db-btn db-ghost" data-act="try-zone">${icon("zap", 13)}Fail ${esc(this.m.name(tryZone))} and watch</button></p>` : ""}`;
    const tz = this.detail.querySelector('[data-act="try-zone"]');
    if (tz) tz.addEventListener("click", () => { this.setMode("break"); this.failed.groups.add(tryZone); this.render(); });
  }

  // ----------------------------------------------------------------- tips
  tipPlan() {
    const T = this.x.tips || {}, r = this.results;
    const empty = !this.state.nodes.length;
    if (empty || !r) return { about: "getting started", list: [].concat(T.start || []) };
    const sel = r.find((x) => x.id === this.selCheck && x.status !== "pass");
    const first = sel || r.find((x) => x.status === "fail") || r.find((x) => x.status === "wait");
    if (!first) return { about: "what to try next", list: [].concat(T.passing || []) };
    return { about: `“${first.title}”`, list: [...[].concat(T[first.id] || []), ...[].concat(T.start || [])] };
  }
  showTip(k) {
    const plan = this.tip && k > 0 ? this.tip.plan : this.tipPlan();
    if (!plan.list.length) return;
    k = Math.min(k, plan.list.length - 1);
    this.tip = { plan, k };
    const tip = plan.list[k], text = typeof tip === "string" ? tip : tip.text, code = typeof tip === "string" ? "" : tip.code || "";
    const last = k === plan.list.length - 1;
    this.tipBox.innerHTML = `<div class="db-tip-in">${icon("lightbulb", 17, "db-tip-ic", 2)}<div class="db-tip-body">
      <div class="db-tip-head">Tip <span class="tn">${k + 1} of ${plan.list.length}</span> <span class="db-tip-about">about ${esc(plan.about)}</span></div>
      <p>${md(text)}</p>${code ? `<pre class="db-tip-code">${esc(code)}</pre>` : ""}
      <div class="db-tip-act">${last ? `<span class="db-note">That is every tip for this.</span>` : `<button type="button" class="db-btn db-ghost" data-tip="next">Another tip</button>`}</div></div>
      <button type="button" class="db-x db-tip-close" aria-label="Close the tip">${icon("x", 14, "", 2.25)}</button></div>`;
    this.tipBox.hidden = false;
    this.tipBox.querySelector('[data-tip="next"]')?.addEventListener("click", () => this.showTip(this.tip.k + 1));
    this.tipBox.querySelector(".db-tip-close").addEventListener("click", () => this.hideTip());
  }
  hideTip() { this.tip = null; if (this.tipBox) { this.tipBox.hidden = true; this.tipBox.innerHTML = ""; } }

  // ---------------------------------------------------------------- timer
  // The page's rehearsal: draw the happy path in two minutes. It counts down,
  // then counts on in amber, because the point is to know how far over you went.
  timerToggle() {
    const t = this.timer;
    if (t.state === "running") { t.left = this.timerLeft(); t.state = "paused"; clearInterval(t.handle); }
    else { t.state = "running"; t.started = Date.now(); t.base = t.left; t.handle = setInterval(() => this.timerDraw(), 250); }
    this.timerDraw();
  }
  timerReset() { const t = this.timer; clearInterval(t.handle); Object.assign(t, { state: "off", left: TIMER_SECONDS, handle: null }); this.timerDraw(); }
  timerLeft() { const t = this.timer; return t.state === "running" ? t.base - (Date.now() - t.started) / 1000 : t.left; }
  timerDraw() {
    const t = this.timer, left = this.timerLeft();
    const btn = this.root.querySelector(".db-timer"), label = btn.querySelector(".db-timer-t");
    const s = Math.abs(Math.round(left)), txt = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    label.textContent = left < 0 && Math.round(left) !== 0 ? `+${txt}` : txt;
    btn.classList.toggle("is-running", t.state === "running");
    btn.classList.toggle("is-over", left < 0);
    btn.setAttribute("aria-label", t.state === "running" ? `Timer running, ${label.textContent}. Pause` : t.state === "paused" ? `Timer paused at ${label.textContent}. Resume` : "Start a two-minute timer");
    this.root.querySelector(".db-timer-reset").hidden = t.state === "off";
  }
}

const BOARDS = new Set();
const CSS_ESC = (s) => (window.CSS && window.CSS.escape ? window.CSS.escape(s) : String(s).replace(/["\\]/g, "\\$&"));

// ------------------------------------------------------------------- mount
function mountAll() {
  const mounts = [...document.querySelectorAll(".designboard[data-board]")];
  if (!mounts.length || !matchMedia(DESKTOP).matches) return;
  const style = document.createElement("style");
  style.textContent = BOARD_CSS;
  document.head.append(style);
  for (const m of mounts) {
    let data;
    try { data = JSON.parse(m.querySelector('script[type="application/json"]').textContent); } catch { continue; }
    BOARDS.add(new Board(m, data));
    m.hidden = false;
    // This sketch's own reference goes behind a click on a desktop: draw
    // first, then compare. It is the next one after the board, before the
    // next heading; asking the page for "the first one" closes sketch 1's
    // four times.
    for (let n = m.nextElementSibling; n && n.tagName !== "H2"; n = n.nextElementSibling) {
      if (n.matches("details.db-reference")) { n.removeAttribute("open"); break; }
    }
  }
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountAll); else mountAll();
