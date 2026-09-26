// The code field on a coding problem page: write the answer in the page, run
// the problem's own tests, read what each test printed, step through the stops
// your breakpoints recorded, try calls of your own and see their time and
// memory, and ask for a tip when stuck. Desktop only; everywhere else the page
// keeps its static "Write this" block and this file does nothing.
//
// The reader's code never leaves their machine. It runs in Pyodide in a Web
// Worker (worker.js), through harness.py, which enforces every limit itself.
// This file adds the one limit Python cannot: if the worker does not answer,
// it is terminated and a fresh one starts.
import { createEditor, createCellEditor } from "./editor.js";
import { icon } from "./icons.js";
import CSS from "./codefield.css";

const LIMITS = { seconds: 3, maxBytes: 65536, maxStops: 200 };
const MAX_INPUTS = 5;
const HARD_GRACE_MS = 4000;
const DRAW_LINES = 1000;
const DESKTOP = "(min-width: 1024px) and (hover: hover) and (pointer: fine)";
const MOD = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Ctrl";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const kb = (n) => (n < 1024 ? `${n} B` : `${(n / 1024).toFixed(n < 10240 ? 1 : 0)} KB`);
const bytes = (n) => (n < 1048576 ? kb(n) : `${(n / 1048576).toFixed(n < 10485760 ? 1 : 0)} MB`);
// The browser's clock is coarse (a tenth of a millisecond without isolation),
// so anything under that is said as under it rather than as a false zero.
const dur = (ms) => (ms == null ? "" : ms < 0.1 ? "under 0.1 ms" : ms < 10 ? `${ms.toFixed(2)} ms`
  : ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(2)} s`);
const plural = (n, one, many = one + "s") => `${n} ${n === 1 ? one : many}`;
const el = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };
const inline = (s) => esc(s).replace(/`([^`]+)`/g, "<code>$1</code>");
const lastLine = (src) => src.trim().split("\n").filter((l) => l.trim()).pop() || "";

const STATUS = {
  pass: ["circle-check", "Passed"], fail: ["circle-x", "Failed"], error: ["circle-x", "Error"],
  stopped: ["octagon-x", "Stopped"], "not-run": ["circle-dashed", "Not run"], skip: ["circle-dashed", "Skipped"],
  ok: ["corner-down-right", "Returned"],
};

// unittest names a test from its method; the page names it the same way before
// the first run, so the list does not change shape when the results arrive.
const humanise = (id) => { const w = id.replace(/^test_/, "").replace(/_/g, " ").trim(); return w ? w[0].toUpperCase() + w.slice(1) : id; };
function plannedTests(src) {
  const found = []; let cls = null;
  for (const line of src.split("\n")) {
    const c = line.match(/^class\s+(\w+)\s*\(/); if (c) { cls = c[1]; continue; }
    const m = line.match(/^\s+def\s+(test\w*)\s*\(/); if (m && cls) found.push({ cls, id: m[1] });
  }
  found.sort((a, b) => (a.cls === b.cls ? (a.id < b.id ? -1 : 1) : a.cls < b.cls ? -1 : 1));   // the loader's order
  const many = new Set(found.map((f) => f.cls)).size > 1;
  return found.map((f, index) => ({ index, id: f.id, name: (many ? f.cls + ": " : "") + humanise(f.id), status: "not-run", planned: true }));
}

// Tips that apply to any problem. The problem's own tips.json comes first.
const GENERIC = {
  stopped: {
    time: "A loop that never reaches its exit. Something has to change on every turn for the loop's condition to become false. Put a breakpoint inside the loop, run, and step through a few stops: the variable that never changes is the bug.",
    output: "Printing inside a loop that runs many times fills the 64 KB allowance. Print only the first few turns, or use a breakpoint instead: it records every variable without printing anything.",
    hard: "The run stopped answering, which usually means one very long built-in call, such as sorting or copying something enormous on every turn of a loop.",
  },
  errors: {
    AttributeError: (m) => (/NoneType/.test(m)
      ? "Something you expected to be an object was `None` when you read an attribute from it. Which variable can run out, at the end of a list or at a missing child, and is it checked before that line?"
      : "You read an attribute that this object does not have. Check the spelling, and whether the object is the kind you think it is: a breakpoint on that line shows it."),
    IndexError: () => "An index went past the end of a list. Check the loop's bounds and any `i + 1` or `i - 1` near the marked line: off by one is the usual cause.",
    KeyError: () => "A dictionary lookup for a key that is not there yet. Use `d.get(key, default)`, or check `key in d` first.",
    TypeError: (m) => (/NoneType/.test(m)
      ? "Something was `None` where a value was needed. Does every path through your function end in a `return` with a value?"
      : "A value of the wrong type reached an operation. The message names both types, and a breakpoint just before shows where the value came from."),
    RecursionError: () => "The recursion went past Python's limit of about 1,000 calls. These tests build deep inputs on purpose to require a loop: rewrite it with a `while` loop, and an explicit stack if you need one.",
    ZeroDivisionError: () => "A division by zero. Which input makes that divisor zero, and what should the answer be then?",
    NameError: () => "A name is used before it is defined, or is spelled differently where it was defined. Python only looks a name up when the line runs, so it fails the first time that line is reached.",
    UnboundLocalError: () => "The variable is assigned somewhere in this function, so Python treats it as local everywhere in it, and this line reads it before any assignment has run.",
    ValueError: () => "Your code raised ValueError. If this input is valid, the message says which value it objected to.",
    NotImplementedError: () => "The function still raises NotImplementedError: its body is not written yet.",
  },
  syntax: (line) => `Python reads the whole file before it runs any of it, and line ${line} does not parse. Look at the line above it too: an unclosed bracket or a missing colon is reported on the line after.`,
  imported: (m) => `${m} Define it at the top level of the file, spelled exactly the same.`,
  notRaised: "The contract says this input must raise an error (the Rules above the code field list which). Your function returned instead of raising.",
  assertion: (check) => (check
    ? `The check \`${check}\` did not hold, and the Result line shows what came back. Run that same call as your own input to look at it by itself.`
    : "The test's check did not hold. The Result line shows what it compared."),
  unstarted: "Work the smallest example above the code field by hand, and write down each step you take. The steps you repeat are the loop you are about to write.",
  passing: "Every test passes. Add a large input of your own and look at its time and memory: they show the complexity your answer really has.",
  inputError: "Your input itself failed before the call ran. The line number is in the input, not in your solution.",
};

// ------------------------------------------------------------------ runtime
class Runtime {
  constructor(workerUrl, harnessUrl) {
    this.workerUrl = workerUrl; this.harnessUrl = harnessUrl;
    this.state = "idle"; this.listeners = new Set();
    this.worker = null; this.pending = null; this.inflight = null;
  }
  on(fn) { this.listeners.add(fn); fn(this); }
  emit() { for (const fn of this.listeners) fn(this); }
  start() {
    if (this.worker) return;
    this.state = "loading"; this.emit();
    const w = new Worker(this.workerUrl, { type: "module" });
    this.worker = w;
    w.onmessage = (e) => this.message(e.data);
    w.onerror = (e) => this.fail((e && e.message) || "the worker could not start");
    w.postMessage({ type: "init", harness: this.harnessUrl });
  }
  message(m) {
    if (m.type === "ready") {
      this.state = "ready"; this.python = m.python; this.emit();
      if (this.pending) { const job = this.pending; this.pending = null; this.send(job); }
    } else if (m.type === "failed") {
      this.fail(m.message);
    } else if (m.type === "result" && this.inflight && m.id === this.inflight.id) {
      const job = this.inflight; this.inflight = null; clearTimeout(job.timer);
      const res = { ...m.result, wall_ms: m.ms };
      // A JavaScript-level failure inside Python (the engine's stack, say) can
      // leave that Python unusable. Never hand the next run a broken one.
      if (res.status === "harness-error" && res.error && res.error.type === "WorkerError") {
        this.worker.terminate(); this.worker = null; this.state = "idle";
        res.error.message = `${res.error.message}. Python has been restarted; run again.`;
        this.start();
      }
      job.resolve(res);
    }
  }
  fail(message) {
    this.state = "failed"; this.error = message;
    if (this.worker) { this.worker.terminate(); this.worker = null; }
    this.emit();
    if (this.pending) {
      const job = this.pending; this.pending = null;
      job.resolve({ status: "runtime-failed", error: { message }, tests: [], stops: [] });
    }
  }
  run(payload) {
    return new Promise((resolve) => {
      const job = { id: Math.random().toString(36).slice(2), payload, resolve };
      if (this.state === "ready") return this.send(job);
      this.pending = job;
      if (!this.worker) this.start();
    });
  }
  send(job) {
    this.inflight = job;
    job.timer = setTimeout(() => this.hardStop(job), LIMITS.seconds * 1000 + HARD_GRACE_MS);
    this.worker.postMessage({ type: "run", id: job.id, payload: job.payload });
  }
  hardStop(job) {
    if (this.inflight !== job) return;
    this.inflight = null;
    this.worker.terminate(); this.worker = null;
    job.resolve({ status: "stopped", tests: [], stops: [],
                  stopped: { kind: "hard", test: null, seconds: (LIMITS.seconds * 1000 + HARD_GRACE_MS) / 1000 } });
    this.start();
  }
}

// ------------------------------------------------------------------- field
class Field {
  constructor(mount, data, runtime) {
    this.mount = mount; this.data = data; this.runtime = runtime;
    this.tips = data.tips || {};
    this.key = `j2s-codefield:v1:${data.id}`;
    this.planned = plannedTests(data.tests);
    this.result = null; this.sel = null; this.stopAt = 0; this.running = false;
    this.inputs = []; this.cells = [];      // the reader's inputs: source text, and a live cell editor each
    this.tip = null;
    this.build();
  }

  load() { try { return JSON.parse(localStorage.getItem(this.key) || "null"); } catch { return null; } }
  save() {
    try {
      const code = this.editor.getCode();
      const inputs = this.cells.map((c) => c.getCode());
      if (code === this.data.starter && !this.editor.getBreakpoints().length && !inputs.length) localStorage.removeItem(this.key);
      else localStorage.setItem(this.key, JSON.stringify({ code, bps: this.editor.getBreakpoints(), inputs, at: Date.now() }));
    } catch { /* private mode: the field still works, it just forgets */ }
  }

  givenStillIntact(code) {
    const start = this.data.starter.split("\n"), now = code.split("\n");
    return this.data.given.every(([a, b]) => { for (let n = a; n <= b; n++) if (start[n - 1] !== now[n - 1]) return false; return true; });
  }

  build() {
    const saved = this.load();
    const code = saved && typeof saved.code === "string" ? saved.code : this.data.starter;
    this.root = el(`<section class="cf" aria-label="Write and run your solution">
      <div class="cf-cap">
        <div class="cf-cap-l">${icon("file-code", 15, "", 2)}<span class="cf-fname">solution.py</span>
          <span class="cf-dot">·</span><span class="cf-py">Python, in your browser</span>
          <span class="cf-status" role="status"></span></div>
        <div class="cf-cap-r">
          <span class="cf-limits" title="Each run gets 3 seconds and 64 KB of printed output. Past either, it is stopped and you are told where.">${icon("shield-check", 14)}<span class="tn">3 s</span><span class="cf-dot">·</span><span class="tn">64 KB</span> of output</span>
          <button type="button" class="cf-btn cf-ghost" data-act="tip">${icon("lightbulb", 14)}Get a tip</button>
          <button type="button" class="cf-btn cf-ghost" data-act="reset">${icon("rotate-ccw", 14)}Reset</button>
          <button type="button" class="cf-btn cf-primary" data-act="run">${icon("play", 14, "", 2.25)}<span class="cf-run-label">Run</span><span class="cf-kbd">${MOD} ↵</span></button>
        </div>
      </div>
      <div class="cf-editor"></div>
      <div class="cf-strip" aria-live="polite"><div class="cf-strip-l"></div><div class="cf-strip-r"></div></div>
      <div class="cf-tip" hidden aria-live="polite"></div>
      <div class="cf-results"><div class="cf-cases" role="listbox" aria-label="Your inputs and the tests"></div><div class="cf-detail"></div></div>
    </section>`);
    this.mount.replaceChildren(this.root);
    this.root.cfField = this;          // for site/tools/codefield-check.mjs
    this.status = this.root.querySelector(".cf-status");
    this.runBtn = this.root.querySelector('[data-act="run"]');
    this.stripL = this.root.querySelector(".cf-strip-l");
    this.stripR = this.root.querySelector(".cf-strip-r");
    this.tipBox = this.root.querySelector(".cf-tip");
    this.list = this.root.querySelector(".cf-cases");
    this.detail = this.root.querySelector(".cf-detail");

    this.saveSoon = () => { clearTimeout(this.saveTimer); this.saveTimer = setTimeout(() => this.save(), 400); };
    this.editor = createEditor(this.root.querySelector(".cf-editor"), {
      doc: code,
      given: this.givenStillIntact(code) ? this.data.given : [],
      breakpoints: (saved && saved.bps) || [],
      onRun: () => this.run(),
      onChange: () => {
        this.saveSoon();
        // After a whole-text paste, protect the given lines again if they came
        // back intact. Not from inside this callback: CodeMirror forbids a
        // dispatch while an update is being applied.
        queueMicrotask(() => {
          if (this.data.given.length && !this.editor.hasGiven() && this.givenStillIntact(this.editor.getCode()))
            this.editor.setGiven(this.data.given);
        });
      },
    });
    for (const src of ((saved && saved.inputs) || []).slice(0, MAX_INPUTS)) this.newCell(String(src));
    addEventListener("pagehide", () => this.save());

    this.runBtn.addEventListener("click", () => this.run());
    this.root.querySelector('[data-act="reset"]').addEventListener("click", () => this.reset());
    this.root.querySelector('[data-act="tip"]').addEventListener("click", () => this.showTip(this.tip ? this.tip.k + 1 : 0));
    this.root.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); this.run(); }
    });
    this.runtime.on((rt) => this.showRuntime(rt));

    const restored = saved && (code !== this.data.starter || this.cells.length);
    this.idle(restored
      ? `Restored your code from your last visit. <button type="button" class="cf-link" data-act="starter">Start again from the starter</button>`
      : `Write your answer above, then <b>Run</b> or press <b>${MOD} ↵</b>. It saves as you type.`);
    this.render();
  }

  // ---------------------------------------------------------- your inputs
  newCell(src) {
    const holder = el(`<div class="cf-cell"></div>`);
    const cell = createCellEditor(holder, {
      doc: src, label: `Your input ${this.cells.length + 1}, Python`,
      onRun: () => this.run(),
      onChange: () => { this.saveSoon(); this.renderList(); this.refreshStale(); },
    });
    cell.holder = holder;
    this.cells.push(cell);
    return cell;
  }

  exampleInput() {
    if (this.tips.example) return this.tips.example;
    const m = this.data.starter.match(/^def\s+(\w+)\s*\(/m);
    return m ? `${m[1]}()` : "";
  }

  addInput() {
    if (this.cells.length >= MAX_INPUTS) return;
    const cell = this.newCell(this.exampleInput());
    this.sel = { kind: "input", i: this.cells.length - 1 };
    this.save();
    this.render();
    cell.focus();
  }

  removeInput(i) {
    const [cell] = this.cells.splice(i, 1);
    cell.destroy();
    // A result for the inputs no longer lines up with them, so it goes too.
    if (this.result && this.result.inputs) this.result.inputs.splice(i, 1);
    if (this.result) this.result.stops = (this.result.stops || []).filter((s) => !(s.input && s.test === i))
      .map((s) => (s.input && s.test > i ? { ...s, test: s.test - 1 } : s));
    if (this.sel && this.sel.kind === "input") this.sel = this.cells.length ? { kind: "input", i: Math.min(this.sel.i, this.cells.length - 1) } : null;
    this.save();
    this.render();
  }

  // Typing in a cell re-draws the list, never the detail it sits in: moving
  // a focused editor's DOM would take the caret away mid-word.
  refreshStale() {
    const sel = this.sel, out = this.detail.querySelector(".cf-input-out");
    if (!sel || sel.kind !== "input" || !out || !this.inputResult(sel.i)) return;
    const stale = this.stale(sel.i);
    out.classList.toggle("is-stale", stale);
    let note = this.detail.querySelector(".cf-stale");
    if (stale && !note) out.prepend(el(`<p class="cf-note cf-stale">${icon("circle-alert", 13)}Edited since it ran. Run again to see the new result.</p>`));
    if (!stale && note) note.remove();
  }

  idle(html) {
    this.stripL.innerHTML = `<span>${html}</span>`;
    this.stripR.innerHTML = "";
    const b = this.stripL.querySelector('[data-act="starter"]');
    if (b) b.addEventListener("click", () => this.reset());
  }

  showRuntime(rt) {
    const s = this.status;
    s.className = "cf-status";
    if (rt.state === "loading") s.innerHTML = `${icon("loader-circle", 13, "cf-spin")}Loading Python…`;
    else if (rt.state === "ready") { s.classList.add("ready"); s.innerHTML = `${icon("circle-check", 13)}Ready`; this.root.querySelector(".cf-py").textContent = `Python ${rt.python}, in your browser`; }
    else if (rt.state === "failed") {
      s.classList.add("failed");
      s.innerHTML = `${icon("cloud-off", 13)}Python did not load <button type="button" class="cf-link">Try again</button>`;
      s.querySelector("button").addEventListener("click", () => rt.start());
    } else s.textContent = "";
  }

  reset() {
    const before = { code: this.editor.getCode(), bps: this.editor.getBreakpoints() };
    if (before.code === this.data.starter && !before.bps.length) return;
    this.editor.setCode(this.data.starter, this.data.given);
    this.editor.setBreakpoints([]);
    this.save();
    this.idle(`Back to the starter code. Your inputs are kept. <button type="button" class="cf-link" data-act="undo">Undo</button>`);
    this.stripL.querySelector('[data-act="undo"]').addEventListener("click", () => {
      this.editor.setCode(before.code, this.givenStillIntact(before.code) ? this.data.given : []);
      this.editor.setBreakpoints(before.bps);
      this.save();
      this.idle("Your code is back.");
    });
  }

  async run() {
    if (this.running) return;
    this.running = true;
    this.runBtn.disabled = true;
    this.runBtn.querySelector(".cf-run-label").textContent = this.runtime.state === "ready" ? "Running…" : "Starting Python…";
    this.editor.clearMarks();
    this.save();
    const inputs = this.cells.map((c) => c.getCode());
    const payload = JSON.stringify({ code: this.editor.getCode(), tests: this.data.tests,
      breakpoints: this.editor.getBreakpoints(), seconds: LIMITS.seconds,
      max_bytes: LIMITS.maxBytes, max_stops: LIMITS.maxStops, inputs });
    let r;
    try { r = await this.runtime.run(payload); }
    finally {
      this.running = false; this.runBtn.disabled = false;
      this.runBtn.querySelector(".cf-run-label").textContent = "Run";
    }
    // The harness drops blank inputs; keep the page's rows and the results lined up.
    const kept = inputs.map((s, i) => [s, i]).filter(([s]) => s.trim());
    const byRow = new Array(inputs.length).fill(null);
    (r.inputs || []).forEach((rec, k) => { if (kept[k]) byRow[kept[k][1]] = { ...rec, index: kept[k][1] }; });
    for (const s of r.stops || []) if (s.input && kept[s.test]) s.test = kept[s.test][1];
    if (r.stopped && r.stopped.input && kept[r.stopped.test]) r.stopped.test = kept[r.stopped.test][1];
    r.inputs = byRow;
    this.result = r;
    this.hideTip();
    this.stopAt = 0;
    this.sel = this.pick(r);
    this.render();
  }

  // Open what most needs looking at: anything stopped, then the input being
  // worked on, then a failure, then a test with breakpoint stops, then the first.
  pick(r) {
    const tests = r.tests || [], ins = r.inputs || [];
    if (r.stopped && r.stopped.input && ins[r.stopped.test]) return { kind: "input", i: r.stopped.test };
    const s = tests.findIndex((t) => t.status === "stopped");
    if (s >= 0) return { kind: "test", i: s };
    if (this.sel && this.sel.kind === "input" && ins[this.sel.i]) return this.sel;
    const bad = ins.findIndex((x) => x && x.status === "error");
    if (bad >= 0) return { kind: "input", i: bad };
    const order = [(t) => t.status === "fail" || t.status === "error", (t) => (r.stops || []).some((x) => !x.input && x.test === t.index)];
    for (const f of order) { const i = tests.findIndex(f); if (i >= 0) return { kind: "test", i }; }
    return tests.length ? { kind: "test", i: 0 } : ins.findIndex(Boolean) >= 0 ? { kind: "input", i: ins.findIndex(Boolean) } : null;
  }

  tests() { return this.result && (this.result.tests || []).length ? this.result.tests : this.planned; }
  inputResult(i) { return this.result && this.result.inputs ? this.result.inputs[i] : null; }
  stale(i) { const rec = this.inputResult(i); return rec && rec.source !== this.cells[i].getCode(); }

  // ------------------------------------------------------------- rendering
  render() {
    if (this.result) this.renderStrip();
    this.renderList();
    this.renderDetail();
    this.markEditor();
  }

  renderStrip() {
    const r = this.result;
    const tests = r.tests || [];
    const count = (st) => tests.filter((t) => t.status === st).length;
    const passed = count("pass"), failed = count("fail") + count("error"), stopped = count("stopped"), notRun = count("not-run");
    const left = [];
    if (r.stopped && r.stopped.input) {
      left.push(`${icon("octagon-x", 15, "st-stopped", 2.1)}Stopped in your input <b class="tn">${r.stopped.test + 1}</b>`);
      left.push(`${icon("circle-dashed", 15, "st-not-run", 2.1)}The tests did not run`);
    } else if (tests.length) {
      left.push(`${icon("circle-check", 15, "st-pass", 2.1)}<b class="tn">${passed}</b> passed`);
      if (failed) left.push(`${icon("circle-x", 15, "st-fail", 2.1)}<b class="tn">${failed}</b> failed`);
      if (stopped) left.push(`${icon("octagon-x", 15, "st-stopped", 2.1)}Stopped in test <b class="tn">${r.stopped.test + 1}</b>`);
      if (notRun) left.push(`${icon("circle-dashed", 15, "st-not-run", 2.1)}<b class="tn">${notRun}</b> not run`);
    } else {
      left.push(this.globalHeadline(r));
    }
    this.stripL.innerHTML = left.join('<span class="cf-sep"></span>');
    const out = r.output_bytes ?? 0;
    const secs = (r.elapsed_ms ?? 0) / 1000;
    const outHit = r.stopped && r.stopped.kind === "output";
    const timeHit = r.stopped && (r.stopped.kind === "time" || r.stopped.kind === "hard");
    this.stripR.innerHTML = r.status === "runtime-failed" ? "" :
      `<span class="${outHit ? "cf-hit" : ""}">Output <b class="tn">${outHit ? "64 KB" : kb(out)}</b> of 64 KB</span><span class="cf-sep"></span>` +
      `<span class="${timeHit ? "cf-hit" : ""}">Time <b class="tn">${timeHit ? (r.stopped.kind === "hard" ? r.stopped.seconds : LIMITS.seconds).toFixed(1) : secs < 0.1 ? secs.toFixed(2) : secs.toFixed(1)}</b> of ${LIMITS.seconds} s</span>`;
  }

  renderList() {
    const r = this.result;
    const sel = this.sel || {};
    const rows = [];
    if (this.cells.length) rows.push(el(`<div class="cf-cases-head">Your inputs <span class="tn">${this.cells.length} of ${MAX_INPUTS}</span></div>`));
    this.cells.forEach((cell, i) => {
      const rec = this.inputResult(i), stale = this.stale(i);
      const st = !rec ? "not-run" : rec.status;
      const [ic] = STATUS[st] || STATUS["not-run"];
      const sub = !rec || stale ? "" : st === "ok" ? `→ ${rec.value}` : st === "stopped" ? (r.stopped && r.stopped.kind === "output" ? "Too much output" : "Out of time")
        : rec.failure ? `${rec.failure.type}${rec.failure.line ? ` on line ${rec.failure.line}` : ""}` : "";
      const row = el(`<div class="cf-case kind-input st-${st}${stale ? " stale" : ""}" role="option" tabindex="0" aria-selected="${sel.kind === "input" && sel.i === i}">
        ${icon(ic, 16, "st-" + st, 2.1)}<span class="cf-cmain"><span class="cf-cl cf-mono">${esc(lastLine(cell.getCode()) || "(empty)")}</span>${sub ? `<span class="cf-csub">${esc(sub)}</span>` : ""}</span>
        <span class="cf-ct tn">${rec && st === "ok" && !stale ? dur(rec.seconds * 1000) : ""}</span>
        <button type="button" class="cf-x" aria-label="Remove input ${i + 1}" title="Remove this input">${icon("x", 13, "", 2.25)}</button></div>`);
      row.addEventListener("click", (e) => {
        if (e.target.closest(".cf-x")) return this.removeInput(i);
        this.select({ kind: "input", i });
      });
      row.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this.select({ kind: "input", i }); } });
      rows.push(row);
    });
    const full = this.cells.length >= MAX_INPUTS;
    const add = el(`<button type="button" class="cf-add" ${full ? "disabled" : ""}>${icon("plus", 14, "", 2.25)}${full ? `Five inputs is the most` : "Add your own input"}</button>`);
    add.addEventListener("click", () => this.addInput());
    rows.push(add);

    const tests = this.tests();
    rows.push(el(`<div class="cf-cases-head">${plural(tests.length, "test")} <span>from test_solution.py</span></div>`));
    tests.forEach((t, i) => {
      const [ic] = STATUS[t.status] || STATUS["not-run"];
      // The list says WHAT failed: the failing check itself for an assertion,
      // the error and your line for a crash. "AssertionError" alone tells nobody anything.
      const f = t.failure;
      const sub = t.status === "stopped" ? (r.stopped.kind === "output" ? "Too much output" : "Out of time")
        : !f ? ""
        : f.type === "AssertionError" && f.check ? f.check.source.replace(/^self\./, "")
        : `${f.type}${f.line ? ` on line ${f.line}` : ""}`;
      const time = t.status === "stopped" ? `${(r.stopped.seconds ?? 0).toFixed(2)} s` : t.code_ms != null ? dur(t.code_ms) : "";
      const row = el(`<button type="button" role="option" class="cf-case st-${t.status}${t.planned ? " planned" : ""}" aria-selected="${sel.kind === "test" && sel.i === i}">
        ${icon(ic, 16, "st-" + t.status, 2.1)}<span class="cf-cmain"><span class="cf-cl">${esc(t.name)}</span>${sub ? `<span class="cf-csub">${esc(sub)}</span>` : ""}</span>
        <span class="cf-ct tn" ${t.code_ms != null ? 'title="Time spent inside your code during this test"' : ""}>${time}</span></button>`);
      row.addEventListener("click", () => this.select({ kind: "test", i }));
      rows.push(row);
    });
    this.list.replaceChildren(...rows);
  }

  select(sel) { this.sel = sel; this.stopAt = 0; this.render(); }

  renderDetail() {
    const box = this.detail;
    const r = this.result, sel = this.sel;
    if (r && !(r.tests || []).length && !(sel && sel.kind === "input")) return this.renderGlobal(r);
    if (!sel) {
      box.innerHTML = `<div class="cf-guide">${icon("square-terminal", 18, "", 2)}<div>
        <p>Each test from <code class="cf-code">test_solution.py</code> shows up here when you run. Anything your code prints shows up under the test that printed it.</p>
        <p>To stop and look at your variables, click beside a line number to set a breakpoint, then run.</p>
        <p>To try a call of your own and see how long it takes and how much memory it uses, <button type="button" class="cf-link" data-act="add">add your own input</button>.</p></div></div>`;
      box.querySelector('[data-act="add"]').addEventListener("click", () => this.addInput());
      return;
    }
    if (sel.kind === "input") return this.renderInput(box, sel.i);
    const t = this.tests()[sel.i];
    if (!t) { this.sel = null; return this.renderDetail(); }
    this.renderTest(box, t);
  }

  globalHeadline(r) {
    if (r.status === "syntax") return `${icon("circle-x", 15, "st-fail", 2.1)}Your code does not parse yet`;
    if (r.status === "import-error") return `${icon("circle-x", 15, "st-fail", 2.1)}The tests could not start`;
    if (r.status === "stopped") return `${icon("octagon-x", 15, "st-stopped", 2.1)}Stopped before the tests started`;
    if (r.status === "runtime-failed") return `${icon("cloud-off", 15, "st-fail", 2.1)}Python did not load`;
    return `${icon("circle-alert", 15, "st-fail", 2.1)}Something went wrong on our side`;
  }

  renderGlobal(r) {
    let html = "";
    if (r.status === "syntax") {
      html = `<div class="cf-banner err">${icon("circle-x", 18, "st-fail", 2.1)}<div><strong>Line ${r.error.line}${r.error.column ? `, column ${r.error.column}` : ""}: ${esc(r.error.message)}.</strong> Python reads the whole file before running anything, so no test ran.</div></div>`;
    } else if (r.status === "import-error") {
      const e = r.error;
      html = `<div class="cf-banner err">${icon("circle-x", 18, "st-fail", 2.1)}<div><strong>${esc(e.type)}${e.line ? ` on line ${e.line}` : ""}.</strong> ${esc(e.message)}</div></div>`;
    } else if (r.status === "stopped") {
      html = this.stopBanner(r.stopped, "Your file");
    } else if (r.status === "runtime-failed") {
      html = `<div class="cf-banner err">${icon("cloud-off", 18, "st-fail", 2.1)}<div><strong>Python did not load.</strong> The code field downloads it once, about 6 MB, and your browser keeps it after that. Check the connection and try again. (${esc(r.error && r.error.message)})</div></div>`;
    } else {
      html = `<div class="cf-banner err">${icon("circle-alert", 18, "st-fail", 2.1)}<div><strong>The runner itself failed</strong>, not your code: ${esc(r.error && (r.error.type + ": " + r.error.message))}</div></div>`;
    }
    this.detail.innerHTML = html;
  }

  stopBanner(s, who = "This test") {
    const where = s.loop ? ` It was going round the loop on <b>lines ${s.loop[0]} to ${s.loop[1]}</b>.`
      : s.function ? ` It was still inside <b>${esc(s.function)}</b>, on line ${s.line}.`
      : s.line ? ` It was on line ${s.line}.` : "";
    const after = s.input ? " The tests did not run." : "";
    if (s.kind === "output")
      return `<div class="cf-banner">${icon("octagon-x", 18, "st-stopped", 2.1)}<div><strong>Stopped: too much output.</strong> ${who} printed 64 KB and was still going, so the run was ended there.${where}${after}</div></div>`;
    if (s.kind === "hard")
      return `<div class="cf-banner">${icon("timer-off", 18, "st-stopped", 2.1)}<div><strong>Stopped: out of time.</strong> The run did not answer after ${s.seconds} seconds, so Python was restarted. It was stuck somewhere the time check cannot see, like one very long built-in call.</div></div>`;
    return `<div class="cf-banner">${icon("timer-off", 18, "st-stopped", 2.1)}<div><strong>Stopped: out of time.</strong> ${who} ran for ${LIMITS.seconds} seconds without finishing.${where} A loop that never reaches its exit looks exactly like this.${after}</div></div>`;
  }

  failureHtml(f, t) {
    let html = `<dl class="cf-kv">`;
    if (f.check) html += `<dt>Check</dt><dd><code>${esc(f.check.source)}</code> <span class="cf-note">test line ${f.check.line}</span></dd>`;
    if (f.subtest) html += `<dt>Case</dt><dd><code>${esc(Object.entries(f.subtest).map(([k, v]) => `${k}=${v}`).join(", "))}</code></dd>`;
    html += `<dt>${t.status === "fail" ? "Result" : esc(f.type)}</dt><dd><code class="bad">${esc(f.message || f.type)}</code></dd>`;
    if (f.line) html += `<dt>Your code</dt><dd><button type="button" class="cf-link" data-line="${f.line}">line ${f.line}</button></dd>`;
    else if (f.input_line) html += `<dt>Your input</dt><dd>line ${f.input_line}</dd>`;
    return html + `</dl>`;
  }

  printedHtml(t, empty) {
    const printed = t.output || "";
    const lines = printed ? printed.split("\n") : [];
    if (lines.length && lines[lines.length - 1] === "") lines.pop();
    let html = `<div class="cf-sub-head">${icon("square-terminal", 14)}Printed <span class="tn">${lines.length ? plural(lines.length, "line") + (t.output_cut ? ", cut at 64 KB" : "") : "nothing"}</span></div>`;
    if (!lines.length) return html + `<div class="cf-log empty">${icon("terminal", 18)}<span>${empty}</span></div>`;
    let rows = "", i = 0, drawn = 0;
    while (i < lines.length && drawn < DRAW_LINES) {
      let j = i;
      while (j + 1 < lines.length && lines[j + 1] === lines[i]) j++;
      rows += `<div class="cf-ll"><span class="cf-ln">${i + 1}</span>${esc(lines[i]) || " "}</div>`;
      drawn++;
      if (j > i) { rows += `<div class="cf-ll fold"><span class="cf-ln"></span>${icon("repeat", 13, "", 2.25)}<span>Same line <b class="tn">${(j - i).toLocaleString()}</b> more ${j - i === 1 ? "time" : "times"}</span></div>`; drawn++; }
      i = j + 1;
    }
    if (i < lines.length) rows += `<div class="cf-ll cut"><span class="cf-ln"></span>${icon("scissors", 13, "", 2.25)}<span>${(lines.length - i).toLocaleString()} more lines not drawn here.</span></div>`;
    if (t.output_cut) rows += `<div class="cf-ll cut"><span class="cf-ln"></span>${icon("scissors", 13, "", 2.25)}<span>Cut at 64 KB. Nothing after this point was kept.</span></div>`;
    return html + `<div class="cf-log">${rows}</div>`;
  }

  stopsHtml(stops) {
    if (!stops.length) return "";
    const r = this.result;
    const k = Math.min(this.stopAt, stops.length - 1);
    const s = stops[k];
    const more = r.stops_truncated ? ` · recording stopped at ${LIMITS.maxStops}` : "";
    let html = `<div class="cf-sub-head">${icon("circle-dot", 14)}Stopped at line ${s.line} <span class="tn">· stop ${k + 1} of ${stops.length}${more}</span>
      <span class="cf-stops-nav"><button type="button" data-stop="-1" aria-label="Previous stop" ${k === 0 ? "disabled" : ""}>${icon("chevron-left", 15)}</button><button type="button" data-stop="1" aria-label="Next stop" ${k === stops.length - 1 ? "disabled" : ""}>${icon("chevron-right", 15)}</button></span></div>`;
    const vars = Object.entries(s.vars || {});
    return html + (vars.length ? `<table class="cf-vars">${vars.map(([n, v]) => `<tr><th>${esc(n)}</th><td>${esc(v)}</td></tr>`).join("")}</table>`
                                : `<p class="cf-note">No local variables at this point.</p>`);
  }

  wireDetail(box) {
    box.querySelectorAll("[data-line]").forEach((b) => b.addEventListener("click", () => { this.editor.revealLine(+b.dataset.line); this.editor.focus(); }));
    box.querySelectorAll("[data-stop]").forEach((b) => b.addEventListener("click", () => {
      this.stopAt = Math.max(0, this.stopAt + +b.dataset.stop); this.render();
      this.root.querySelector(`[data-stop="${b.dataset.stop}"]`)?.focus();
    }));
    box.querySelectorAll("[data-try]").forEach((b) => b.addEventListener("click", () => this.tryAsInput(b.dataset.try)));
  }

  // A failed check that is one call on plain values can be looked at on its own.
  callIn(check) {
    const plain = (args) => [...args.replace(/"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'/g, "0").matchAll(/[A-Za-z_]\w*/g)]
      .every((m) => ["True", "False", "None"].includes(m[0]));
    const m = /^self\.assert\w*\((.*)\)\s*$/.exec(check || "");
    if (!m) return null;
    const names = [...this.data.starter.matchAll(/^def\s+(\w+)\s*\(/gm)].map((x) => x[1]);
    for (const name of names) {
      const at = m[1].indexOf(name + "(");
      if (at !== 0) continue;
      let depth = 0, end = -1;
      for (let i = name.length; i < m[1].length; i++) {
        const c = m[1][i];
        if ("([{".includes(c)) depth++;
        else if (")]}".includes(c)) { depth--; if (depth === 0) { end = i; break; } }
      }
      if (end > 0 && plain(m[1].slice(name.length + 1, end))) return m[1].slice(0, end + 1);
    }
    return null;
  }

  tryAsInput(call) {
    if (this.cells.length >= MAX_INPUTS) return;
    this.newCell(call);
    this.sel = { kind: "input", i: this.cells.length - 1 };
    this.save();
    this.render();
    this.run();
  }

  renderTest(box, t) {
    const r = this.result;
    const [ic, label] = STATUS[t.status] || STATUS["not-run"];
    let html = `<div class="cf-d-head"><span class="cf-d-title">${esc(t.name)}</span><span class="cf-badge st-${t.status}">${icon(ic, 13, "", 2.25)}${t.planned ? "Not run yet" : label}</span></div>`;
    if (t.planned) {
      box.innerHTML = html + `<p class="cf-note">This test runs when you press <b>Run</b>. What it checks is in <code class="cf-code">test_solution.py</code>, under <code class="cf-code">${esc(t.id)}</code>.</p>`;
      return;
    }
    if (t.status === "stopped") html += this.stopBanner(r.stopped);
    if (t.status === "not-run") html += `<p class="cf-note">This test did not run, because the run was stopped ${r.stopped && r.stopped.input ? "in one of your inputs" : "in an earlier one"}.</p>`;
    if (t.failure) {
      html += this.failureHtml(t.failure, t);
      const call = t.status === "fail" && this.callIn(t.failure.check && t.failure.check.source);
      if (call && this.cells.length < MAX_INPUTS)
        html += `<p class="cf-try"><button type="button" class="cf-link" data-try="${esc(call)}">Run <code>${esc(call)}</code> as your own input</button> to see what it returns on its own.</p>`;
    }
    if (t.code_ms != null && t.status !== "not-run")
      html += `<div class="cf-metrics"><span>${icon("timer", 14)}<b class="tn">${dur(t.code_ms)}</b> inside your code</span><span class="cf-note">the whole test took ${dur(t.ms)}, building its inputs included</span></div>`;
    html += this.printedHtml(t, t.status === "not-run" ? "Did not run." : "Nothing was printed.");
    const stops = (r.stops || []).filter((s) => !s.input && s.test === t.index);
    if (stops.length) html += this.stopsHtml(stops);
    else if (this.editor.getBreakpoints().length && t.status !== "not-run") html += `<p class="cf-note">Your breakpoints were not reached in this test.</p>`;
    box.innerHTML = html;
    this.wireDetail(box);
  }

  renderInput(box, i) {
    const cell = this.cells[i];
    if (!cell) { this.sel = null; return this.renderDetail(); }
    const rec = this.inputResult(i), stale = this.stale(i), r = this.result;
    const st = !rec ? "not-run" : rec.status;
    const [ic, label] = STATUS[st] || STATUS["not-run"];
    const head = el(`<div class="cf-d-head"><span class="cf-d-title">Your input ${i + 1}</span><span class="cf-badge st-${st}">${icon(ic, 13, "", 2.25)}${!rec ? "Not run yet" : label}</span>
      <button type="button" class="cf-link cf-remove">Remove</button></div>`);
    head.querySelector(".cf-remove").addEventListener("click", () => this.removeInput(i));
    const hint = el(`<p class="cf-cell-hint">Setup lines first if you need them, then the call to run on the last line. Only that call is timed.</p>`);
    const out = el(`<div class="cf-input-out"></div>`);
    let html = "";
    if (!rec) {
      html = `<p class="cf-note">Press <b>Run</b> or <b>${MOD} ↵</b>. Your inputs run first, then the tests.</p>`;
    } else {
      if (stale) html += `<p class="cf-note cf-stale">${icon("circle-alert", 13)}Edited since it ran. Run again to see the new result.</p>`;
      if (st === "stopped") html += this.stopBanner(r.stopped, "Your input");
      if (st === "not-run") html += `<p class="cf-note">This input did not run, because the run was stopped in an earlier one.</p>`;
      if (st === "error") html += this.failureHtml(rec.failure, { status: "error" });
      if (st === "ok") {
        html += `<dl class="cf-kv"><dt>Returned</dt><dd><code>${esc(rec.value)}</code> <span class="cf-note">${esc(rec.type)}</span></dd></dl>`;
        const mem = rec.peak_bytes == null ? `<span class="cf-note" title="Memory is measured by running the call a second time with tracing on, which can be 15 times slower. That second run gets a small allowance of its own, so it never uses up your 3 seconds.">memory not measured: the call is too slow to run again with tracing on</span>`
          : `<span title="The most memory the call held at any one moment, not counting its arguments, which were built before it started. Python in the browser is 32-bit, so most sizes are smaller than a 64-bit Python on your computer reports.">${icon("memory-stick", 14)}<b class="tn">${bytes(rec.peak_bytes)}</b> ${rec.peak_bytes ? "peak memory used by the call" : "of new memory used by the call"}</span>`;
        html += `<div class="cf-metrics"><span>${icon("timer", 14)}<b class="tn">${dur(rec.seconds * 1000)}</b> inside ${rec.call ? `<code>${esc(rec.call)}</code>` : "the call"}</span>${mem}</div>`;
      }
      if (st !== "not-run") html += this.printedHtml(rec, "Nothing was printed.");
      const stops = (r.stops || []).filter((s) => s.input && s.test === i);
      if (stops.length) html += this.stopsHtml(stops);
    }
    out.innerHTML = html;
    if (stale) out.classList.add("is-stale");
    box.replaceChildren(head, cell.holder, hint, out);
    cell.view.requestMeasure();
    this.wireDetail(out);
  }

  markEditor() {
    // Everything that applies at once: the loop a run was stopped in AND the
    // breakpoint stop being looked at are usually on the same lines, and the
    // reader stepping through stops needs both.
    const r = this.result, sel = this.sel;
    if (!r) return;
    if (!(r.tests || []).length && !(sel && sel.kind === "input")) {
      if (r.status === "syntax") { this.editor.mark([{ from: r.error.line, to: r.error.line, kind: "error", tag: "does not parse" }]); this.editor.revealLine(r.error.line); }
      else if (r.status === "import-error" && r.error.line) { this.editor.mark([{ from: r.error.line, to: r.error.line, kind: "error", tag: r.error.type }]); this.editor.revealLine(r.error.line); }
      else if (r.status === "stopped" && r.stopped && r.stopped.line) this.markStop(r.stopped);
      return;
    }
    if (!sel) return this.editor.clearMarks();
    const t = sel.kind === "input" ? this.inputResult(sel.i) : (r.tests || [])[sel.i];
    if (!t) return this.editor.clearMarks();
    const marks = [];
    let reveal = null;
    const s = r.stopped;
    if (t.status === "stopped" && s && s.line) {
      const from = s.loop ? s.loop[0] : s.line, to = s.loop ? s.loop[1] : s.line;
      marks.push({ from, to, kind: "stop", tag: s.kind === "output" ? "stopped here, still printing" : `stopped here after ${LIMITS.seconds} s` });
      reveal = from;
    }
    const stops = (r.stops || []).filter((x) => (sel.kind === "input" ? x.input : !x.input) && x.test === sel.i);
    if (stops.length) {
      const k = Math.min(this.stopAt, stops.length - 1);
      marks.push({ from: stops[k].line, to: stops[k].line, kind: "here", tag: `stop ${k + 1} of ${stops.length}` });
      reveal = stops[k].line;
    } else if (t.failure && t.failure.line) {
      marks.push({ from: t.failure.line, to: t.failure.line, kind: "error", tag: t.failure.type });
      reveal = reveal ?? t.failure.line;
    }
    if (!marks.length) return this.editor.clearMarks();
    this.editor.mark(marks);
    if (reveal) this.editor.revealLine(reveal);
  }

  markStop(s) {
    if (!s || !s.line) return;
    const from = s.loop ? s.loop[0] : s.line, to = s.loop ? s.loop[1] : s.line;
    const tag = s.kind === "output" ? "stopped here, still printing" : `stopped here after ${LIMITS.seconds} s`;
    this.editor.mark([{ from, to, kind: "stop", tag }]);
    this.editor.revealLine(from);
  }

  // ------------------------------------------------------------------ tips
  // Unstarted: the body of a function is still only `...` or `pass`.
  unstarted() {
    const code = this.editor.getCode();
    return code === this.data.starter || /def\s+\w+\([^)]*\):\s*\n\s+(\.\.\.|pass)\s*(\n|$)/.test(code);
  }

  // What to say, most specific first, always ending with the approach, so
  // "Another tip" keeps going somewhere useful.
  tipPlan() {
    const T = this.tips, r = this.result, sel = this.sel;
    const list = []; let about = "your code so far";
    const add = (xs) => { for (const x of [].concat(xs || [])) if (x && !list.some((y) => JSON.stringify(y) === JSON.stringify(x))) list.push(x); };
    const rec = !r || !sel ? null : sel.kind === "input" ? this.inputResult(sel.i) : (r.tests || [])[sel.i];
    if (!r || (this.unstarted() && !(rec && rec.status === "stopped"))) {
      about = "getting started"; add(T.start); add(GENERIC.unstarted);
    } else if (r.status === "syntax") {
      about = `line ${r.error.line}`; add(GENERIC.syntax(r.error.line));
    } else if (r.status === "import-error") {
      about = "why the tests could not start"; add(GENERIC.imported(r.error.message));
    } else if (r.status === "stopped" && !(r.tests || []).length && !(r.stopped && r.stopped.input)) {
      about = "the stop"; add(T.stopped); add(GENERIC.stopped[r.stopped.kind] || GENERIC.stopped.time);
    } else if (rec && rec.status === "stopped") {
      about = sel.kind === "input" ? `your input ${sel.i + 1}` : `the test “${rec.name}”`;
      add(T.stopped); add(GENERIC.stopped[r.stopped.kind] || GENERIC.stopped.time);
    } else if (rec && (rec.status === "fail" || rec.status === "error")) {
      const f = rec.failure || {};
      about = sel.kind === "input" ? `your input ${sel.i + 1}` : `the test “${rec.name}”`;
      if (sel.kind === "test") add((T.tests || {})[rec.id]);
      if (sel.kind === "input" && f.input_line && !f.line) add(GENERIC.inputError);
      if (f.type === "AssertionError") add(/not raised/.test(f.message || "") ? GENERIC.notRaised : GENERIC.assertion(f.check && f.check.source));
      else if (f.type) { add((T.errors || {})[f.type]); const g = GENERIC.errors[f.type]; if (g) add(g(f.message || "")); }
    } else {
      const tests = r.tests || [];
      const bad = tests.find((t) => t.status === "fail" || t.status === "error");
      if (bad) { about = `the test “${bad.name}”`; add((T.tests || {})[bad.id]); }
      else if (tests.length && tests.every((t) => t.status === "pass")) { about = "what to try next"; add(T.passing); add(GENERIC.passing); }
    }
    add(T.start);
    return { about, list };
  }

  showTip(k) {
    const plan = this.tip && k > 0 ? this.tip.plan : this.tipPlan();
    if (!plan.list.length) return;
    k = Math.min(k, plan.list.length - 1);
    this.tip = { plan, k };
    const tip = plan.list[k];
    const text = typeof tip === "string" ? tip : tip.text;
    const code = typeof tip === "string" ? "" : tip.code || "";
    const last = k === plan.list.length - 1;
    // A code tip that is an input rather than a skeleton (no def or class, and a
    // last line that is an expression) can be run as one in a click.
    const tail = lastLine(code);
    const runnable = code && !/^(def|class)\s/m.test(code) && !/^\s/.test(tail) && !/:\s*$/.test(tail) && this.cells.length < MAX_INPUTS;
    this.tipBox.innerHTML = `<div class="cf-tip-in">${icon("lightbulb", 17, "cf-tip-ic", 2)}<div class="cf-tip-body">
        <div class="cf-tip-head">Tip <span class="tn">${k + 1} of ${plan.list.length}</span> <span class="cf-tip-about">about ${esc(plan.about)}</span></div>
        <p>${inline(text)}</p>${code ? `<pre class="cf-tip-code"><code>${esc(code)}</code></pre>` : ""}
        <div class="cf-tip-act">${runnable ? `<button type="button" class="cf-btn cf-ghost" data-tip="try">${icon("play", 13, "", 2.25)}Run it as your own input</button>` : ""}${last ? `<span class="cf-note">That is every tip for this.</span>` : `<button type="button" class="cf-btn cf-ghost" data-tip="next">Another tip</button>`}</div>
      </div><button type="button" class="cf-x cf-tip-close" aria-label="Close the tip">${icon("x", 14, "", 2.25)}</button></div>`;
    this.tipBox.hidden = false;
    this.tipBox.querySelector('[data-tip="next"]')?.addEventListener("click", () => this.showTip(this.tip.k + 1));
    this.tipBox.querySelector('[data-tip="try"]')?.addEventListener("click", () => this.tryAsInput(code));
    this.tipBox.querySelector(".cf-tip-close").addEventListener("click", () => this.hideTip());
  }

  hideTip() { this.tip = null; this.tipBox.hidden = true; this.tipBox.innerHTML = ""; }
}

// ------------------------------------------------------------------- mount
function mountAll() {
  const mounts = [...document.querySelectorAll(".codefield[data-worker]")];
  if (!mounts.length || !matchMedia(DESKTOP).matches) return;
  const style = document.createElement("style");
  style.textContent = CSS;
  document.head.append(style);
  const first = mounts[0];
  // Absolute: the worker fetches the harness, and a relative URL inside a
  // worker resolves against the worker's own address, not this page's.
  const abs = (u) => new URL(u, document.baseURI).href;
  const runtime = new Runtime(abs(first.dataset.worker), abs(first.dataset.harness));
  for (const m of mounts) {
    let data;
    try { data = JSON.parse(m.querySelector('script[type="application/json"]').textContent); } catch { continue; }
    const wrap = m.closest(".codefield-wrap");
    new Field(m, data, runtime);
    wrap && wrap.querySelector(".codefield-static")?.setAttribute("hidden", "");
    m.hidden = false;
  }
  // Start Python while the reader is still reading the question, so the first
  // run does not wait for a download.
  const warm = () => runtime.start();
  if ("requestIdleCallback" in window) requestIdleCallback(warm, { timeout: 2500 }); else setTimeout(warm, 800);
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountAll); else mountAll();
