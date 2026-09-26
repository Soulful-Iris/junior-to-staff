// The code field on a coding problem page: write the answer in the page, run
// the problem's own tests, read what each test printed, step through the stops
// your breakpoints recorded. Desktop only; everywhere else the page keeps its
// static "Write this" block and this file does nothing.
//
// The reader's code never leaves their machine. It runs in Pyodide in a Web
// Worker (worker.js), through harness.py, which enforces every limit itself.
// This file adds the one limit Python cannot: if the worker does not answer,
// it is terminated and a fresh one starts.
import { createEditor } from "./editor.js";
import { icon } from "./icons.js";
import CSS from "./codefield.css";

const LIMITS = { seconds: 3, maxBytes: 65536, maxStops: 200 };
const HARD_GRACE_MS = 4000;
const DRAW_LINES = 1000;
const DESKTOP = "(min-width: 1024px) and (hover: hover) and (pointer: fine)";
const MOD = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Ctrl";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const kb = (n) => (n < 1024 ? `${n} B` : `${(n / 1024).toFixed(n < 10240 ? 1 : 0)} KB`);
const plural = (n, one, many = one + "s") => `${n} ${n === 1 ? one : many}`;
const el = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };

const STATUS = {
  pass: ["circle-check", "Passed"], fail: ["circle-x", "Failed"], error: ["circle-x", "Error"],
  stopped: ["octagon-x", "Stopped"], "not-run": ["circle-dashed", "Not run"], skip: ["circle-dashed", "Skipped"],
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
    this.key = `j2s-codefield:v1:${data.id}`;
    this.result = null; this.selected = 0; this.stopAt = 0; this.running = false;
    this.build();
  }

  load() { try { return JSON.parse(localStorage.getItem(this.key) || "null"); } catch { return null; } }
  save() {
    try {
      const code = this.editor.getCode();
      if (code === this.data.starter && !this.editor.getBreakpoints().length) localStorage.removeItem(this.key);
      else localStorage.setItem(this.key, JSON.stringify({ code, bps: this.editor.getBreakpoints(), at: Date.now() }));
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
          <button type="button" class="cf-btn cf-ghost" data-act="reset">${icon("rotate-ccw", 14)}Reset</button>
          <button type="button" class="cf-btn cf-primary" data-act="run">${icon("play", 14, "", 2.25)}<span class="cf-run-label">Run tests</span><span class="cf-kbd">${MOD} ↵</span></button>
        </div>
      </div>
      <div class="cf-editor"></div>
      <div class="cf-strip" aria-live="polite"><div class="cf-strip-l"></div><div class="cf-strip-r"></div></div>
      <div class="cf-results"></div>
    </section>`);
    this.mount.replaceChildren(this.root);
    this.root.cfField = this;          // for site/tools/codefield-check.mjs
    this.status = this.root.querySelector(".cf-status");
    this.runBtn = this.root.querySelector('[data-act="run"]');
    this.stripL = this.root.querySelector(".cf-strip-l");
    this.stripR = this.root.querySelector(".cf-strip-r");
    this.results = this.root.querySelector(".cf-results");

    let saveTimer = null;
    this.editor = createEditor(this.root.querySelector(".cf-editor"), {
      doc: code,
      given: this.givenStillIntact(code) ? this.data.given : [],
      breakpoints: (saved && saved.bps) || [],
      onRun: () => this.run(),
      onChange: () => {
        clearTimeout(saveTimer); saveTimer = setTimeout(() => this.save(), 400);
        // After a whole-text paste, protect the given lines again if they came
        // back intact. Not from inside this callback: CodeMirror forbids a
        // dispatch while an update is being applied.
        queueMicrotask(() => {
          if (this.data.given.length && !this.editor.hasGiven() && this.givenStillIntact(this.editor.getCode()))
            this.editor.setGiven(this.data.given);
        });
      },
    });
    addEventListener("pagehide", () => this.save());

    this.runBtn.addEventListener("click", () => this.run());
    this.root.querySelector('[data-act="reset"]').addEventListener("click", () => this.reset());
    this.root.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); this.run(); }
    });
    this.runtime.on((rt) => this.showRuntime(rt));

    const restored = saved && code !== this.data.starter;
    this.idle(restored
      ? `Restored your code from your last visit. <button type="button" class="cf-link" data-act="starter">Start again from the starter</button>`
      : `Write your answer above, then <b>Run tests</b> or press <b>${MOD} ↵</b>. It saves as you type.`);
    this.results.replaceChildren(el(`<div class="cf-empty">${icon("square-terminal", 18, "", 2)}
      <div>Each test from <code class="cf-code">test_solution.py</code> shows up here. Anything your code prints shows up under the test that printed it.
      To stop and look at your variables, click beside a line number to set a breakpoint, then run.</div></div>`));
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
    this.idle(`Back to the starter code. <button type="button" class="cf-link" data-act="undo">Undo</button>`);
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
    const payload = JSON.stringify({ code: this.editor.getCode(), tests: this.data.tests,
      breakpoints: this.editor.getBreakpoints(), seconds: LIMITS.seconds,
      max_bytes: LIMITS.maxBytes, max_stops: LIMITS.maxStops });
    let r;
    try { r = await this.runtime.run(payload); }
    finally {
      this.running = false; this.runBtn.disabled = false;
      this.runBtn.querySelector(".cf-run-label").textContent = "Run tests";
    }
    this.result = r;
    const tests = r.tests || [];
    // Open the test that most needs looking at: stopped, then failed, then one
    // with breakpoint stops, then simply the first.
    const pick = [(t) => t.status === "stopped", (t) => t.status === "fail" || t.status === "error",
                  (t) => (r.stops || []).some((s) => s.test === t.index)]
      .map((f) => tests.findIndex(f)).find((i) => i >= 0);
    this.selected = pick ?? 0;
    this.stopAt = 0;
    this.render();
  }

  // ------------------------------------------------------------- rendering
  render() {
    const r = this.result;
    const tests = r.tests || [];
    const count = (st) => tests.filter((t) => t.status === st).length;
    const passed = count("pass"), failed = count("fail") + count("error"), stopped = count("stopped"), notRun = count("not-run");

    const left = [];
    if (tests.length) {
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

    if (!tests.length) { this.renderGlobal(r); return; }

    const list = el(`<div class="cf-cases" role="listbox" aria-label="Tests"><div class="cf-cases-head">${plural(tests.length, "test")} <span>from test_solution.py</span></div></div>`);
    tests.forEach((t, i) => {
      const [ic] = STATUS[t.status] || STATUS["not-run"];
      // The list says WHAT failed: the failing check itself for an assertion,
      // the error and your line for a crash. "AssertionError" alone tells nobody anything.
      const f = t.failure;
      const sub = t.status === "stopped" ? (r.stopped.kind === "output" ? "Too much output" : "Out of time")
        : !f ? ""
        : f.type === "AssertionError" && f.check ? f.check.source.replace(/^self\./, "")
        : `${f.type}${f.line ? ` on line ${f.line}` : ""}`;
      const time = t.status === "stopped" ? `${(r.stopped.seconds ?? 0).toFixed(2)} s` : t.ms != null ? `${t.ms < 1 ? t.ms.toFixed(2) : t.ms.toFixed(0)} ms` : "";
      const row = el(`<button type="button" role="option" class="cf-case st-${t.status}" aria-selected="${i === this.selected}">
        ${icon(ic, 16, "st-" + t.status, 2.1)}<span class="cf-cmain"><span class="cf-cl">${esc(t.name)}</span>${sub ? `<span class="cf-csub">${esc(sub)}</span>` : ""}</span>
        <span class="cf-ct tn">${time}</span></button>`);
      row.addEventListener("click", () => { this.selected = i; this.stopAt = 0; this.render(); });
      list.append(row);
    });
    const detail = el(`<div class="cf-detail"></div>`);
    this.renderDetail(detail, tests[this.selected]);
    this.results.replaceChildren(list, detail);
    this.markEditor();
  }

  globalHeadline(r) {
    if (r.status === "syntax") return `${icon("circle-x", 15, "st-fail", 2.1)}Your code does not parse yet`;
    if (r.status === "import-error") return `${icon("circle-x", 15, "st-fail", 2.1)}The tests could not start`;
    if (r.status === "stopped") return `${icon("octagon-x", 15, "st-stopped", 2.1)}Stopped before the tests started`;
    if (r.status === "runtime-failed") return `${icon("cloud-off", 15, "st-fail", 2.1)}Python did not load`;
    return `${icon("circle-alert", 15, "st-fail", 2.1)}Something went wrong on our side`;
  }

  renderGlobal(r) {
    const box = el(`<div class="cf-empty"></div>`);
    let html = "";
    if (r.status === "syntax") {
      html = `<div class="cf-banner err">${icon("circle-x", 18, "st-fail", 2.1)}<div><strong>Line ${r.error.line}${r.error.column ? `, column ${r.error.column}` : ""}: ${esc(r.error.message)}.</strong> Python reads the whole file before running anything, so no test ran.</div></div>`;
      this.editor.mark([{ from: r.error.line, to: r.error.line, kind: "error", tag: "does not parse" }]);
      this.editor.revealLine(r.error.line);
    } else if (r.status === "import-error") {
      const e = r.error;
      html = `<div class="cf-banner err">${icon("circle-x", 18, "st-fail", 2.1)}<div><strong>${esc(e.type)}${e.line ? ` on line ${e.line}` : ""}.</strong> ${esc(e.message)}</div></div>`;
      if (e.line) { this.editor.mark([{ from: e.line, to: e.line, kind: "error", tag: e.type }]); this.editor.revealLine(e.line); }
    } else if (r.status === "stopped") {
      html = this.stopBanner(r.stopped, "Your file");
      this.markStop(r.stopped);
    } else if (r.status === "runtime-failed") {
      html = `<div class="cf-banner err">${icon("cloud-off", 18, "st-fail", 2.1)}<div><strong>Python did not load.</strong> The code field downloads it once, about 6 MB, and your browser keeps it after that. Check the connection and try again. (${esc(r.error && r.error.message)})</div></div>`;
    } else {
      html = `<div class="cf-banner err">${icon("circle-alert", 18, "st-fail", 2.1)}<div><strong>The runner itself failed</strong>, not your code: ${esc(r.error && (r.error.type + ": " + r.error.message))}</div></div>`;
    }
    box.innerHTML = `<div style="flex:1">${html}</div>`;
    this.results.replaceChildren(box);
  }

  stopBanner(s, who = "This test") {
    const where = s.loop ? ` It was going round the loop on <b>lines ${s.loop[0]} to ${s.loop[1]}</b>.`
      : s.function ? ` It was still inside <b>${esc(s.function)}</b>, on line ${s.line}.`
      : s.line ? ` It was on line ${s.line}.` : "";
    if (s.kind === "output")
      return `<div class="cf-banner">${icon("octagon-x", 18, "st-stopped", 2.1)}<div><strong>Stopped: too much output.</strong> ${who} printed 64 KB and was still going, so the run was ended there.${where}</div></div>`;
    if (s.kind === "hard")
      return `<div class="cf-banner">${icon("timer-off", 18, "st-stopped", 2.1)}<div><strong>Stopped: out of time.</strong> The run did not answer after ${s.seconds} seconds, so Python was restarted. It was stuck somewhere the time check cannot see, like one very long built-in call.</div></div>`;
    return `<div class="cf-banner">${icon("timer-off", 18, "st-stopped", 2.1)}<div><strong>Stopped: out of time.</strong> ${who} ran for ${LIMITS.seconds} seconds without finishing.${where} A loop that never reaches its exit looks exactly like this.</div></div>`;
  }

  renderDetail(box, t) {
    const r = this.result;
    const [ic, label] = STATUS[t.status] || STATUS["not-run"];
    let html = `<div class="cf-d-head"><span class="cf-d-title">${esc(t.name)}</span><span class="cf-badge st-${t.status}">${icon(ic, 13, "", 2.25)}${label}</span></div>`;
    if (t.status === "stopped") html += this.stopBanner(r.stopped);
    if (t.status === "not-run") html += `<p class="cf-note">This test did not run, because the run was stopped in an earlier one.</p>`;
    if (t.failure) {
      const f = t.failure;
      html += `<dl class="cf-kv">`;
      if (f.check) html += `<dt>Check</dt><dd><code>${esc(f.check.source)}</code> <span class="cf-note">test line ${f.check.line}</span></dd>`;
      if (f.subtest) html += `<dt>Case</dt><dd><code>${esc(Object.entries(f.subtest).map(([k, v]) => `${k}=${v}`).join(", "))}</code></dd>`;
      html += `<dt>${t.status === "fail" ? "Result" : esc(f.type)}</dt><dd><code class="bad">${esc(f.message || f.type)}</code></dd>`;
      if (f.line) html += `<dt>Your code</dt><dd><button type="button" class="cf-link" data-line="${f.line}">line ${f.line}</button></dd>`;
      html += `</dl>`;
    }
    // what this test printed
    const printed = t.output || "";
    const lines = printed ? printed.split("\n") : [];
    if (lines.length && lines[lines.length - 1] === "") lines.pop();
    html += `<div class="cf-sub-head">${icon("square-terminal", 14)}Printed <span class="tn">${lines.length ? plural(lines.length, "line") + (t.output_cut ? ", cut at 64 KB" : "") : "nothing"}</span></div>`;
    if (!lines.length) {
      html += `<div class="cf-log empty">${icon("terminal", 18)}<span>${t.status === "not-run" ? "Did not run." : "Nothing was printed."}</span></div>`;
    } else {
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
      html += `<div class="cf-log">${rows}</div>`;
    }
    // breakpoint stops recorded during this test
    const stops = (r.stops || []).filter((s) => s.test === t.index);
    if (stops.length) {
      const k = Math.min(this.stopAt, stops.length - 1);
      const s = stops[k];
      const more = r.stops_truncated && stops.length >= 1 ? ` · recording stopped at ${LIMITS.maxStops}` : "";
      html += `<div class="cf-sub-head">${icon("circle-dot", 14)}Stopped at line ${s.line} <span class="tn">· stop ${k + 1} of ${stops.length}${more}</span>
        <span class="cf-stops-nav"><button type="button" data-stop="-1" aria-label="Previous stop" ${k === 0 ? "disabled" : ""}>${icon("chevron-left", 15)}</button><button type="button" data-stop="1" aria-label="Next stop" ${k === stops.length - 1 ? "disabled" : ""}>${icon("chevron-right", 15)}</button></span></div>`;
      const vars = Object.entries(s.vars || {});
      html += vars.length ? `<table class="cf-vars">${vars.map(([n, v]) => `<tr><th>${esc(n)}</th><td>${esc(v)}</td></tr>`).join("")}</table>`
                          : `<p class="cf-note">No local variables at this point.</p>`;
    } else if (this.editor.getBreakpoints().length && t.status !== "not-run") {
      html += `<p class="cf-note">Your breakpoints were not reached in this test.</p>`;
    }
    box.innerHTML = html;
    box.querySelectorAll("[data-line]").forEach((b) => b.addEventListener("click", () => { this.editor.revealLine(+b.dataset.line); this.editor.focus(); }));
    box.querySelectorAll("[data-stop]").forEach((b) => b.addEventListener("click", () => { this.stopAt = Math.max(0, this.stopAt + +b.dataset.stop); this.render(); this.root.querySelector(`[data-stop="${b.dataset.stop}"]`)?.focus(); }));
  }

  markStop(s) {
    if (!s || !s.line) return;
    const from = s.loop ? s.loop[0] : s.line, to = s.loop ? s.loop[1] : s.line;
    const tag = s.kind === "output" ? "stopped here, still printing" : `stopped here after ${LIMITS.seconds} s`;
    this.editor.mark([{ from, to, kind: "stop", tag }]);
    this.editor.revealLine(from);
  }

  markEditor() {
    // Everything that applies at once: the loop a run was stopped in AND the
    // breakpoint stop being looked at are usually on the same lines, and the
    // reader stepping through stops needs both.
    const r = this.result, t = (r.tests || [])[this.selected];
    if (!t) return;
    const marks = [];
    let reveal = null;
    const s = r.stopped;
    if (t.status === "stopped" && s && s.line) {
      const from = s.loop ? s.loop[0] : s.line, to = s.loop ? s.loop[1] : s.line;
      marks.push({ from, to, kind: "stop", tag: s.kind === "output" ? "stopped here, still printing" : `stopped here after ${LIMITS.seconds} s` });
      reveal = from;
    }
    const stops = (r.stops || []).filter((x) => x.test === t.index);
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
