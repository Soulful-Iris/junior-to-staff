// The reader's code runs here: in a Web Worker, on the reader's own machine,
// in Pyodide (CPython compiled to WebAssembly). Nothing is executed on our
// server, so there is nothing there to attack and no bill to run up.
//
// Every limit lives in the harness (Python). The page's only job is the
// backstop: if this worker does not answer in time, the page terminates it
// and starts a fresh one. That covers what Python-level checks cannot see,
// such as a single C call that never returns.
//
// Pinned: bump both together, and re-run site/tools/codefield-check.mjs.
const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

let runJson = null;

self.onmessage = async ({ data }) => {
  if (data.type === "init") {
    const t0 = performance.now();
    try {
      const { loadPyodide } = await import(PYODIDE + "pyodide.mjs");
      const py = await loadPyodide({ indexURL: PYODIDE });
      const res = await fetch(data.harness);
      if (!res.ok) throw new Error(`harness ${res.status}`);
      py.FS.writeFile("/home/pyodide/codefield_harness.py", await res.text());
      py.runPython("import sys\nif '/home/pyodide' not in sys.path: sys.path.insert(0, '/home/pyodide')\n"
        + "import unittest, ast, reprlib, json, random, itertools, collections, heapq, math, copy");
      runJson = py.pyimport("codefield_harness").run_json;
      self.postMessage({ type: "ready", python: py.runPython("import sys; sys.version.split()[0]"),
                         ms: Math.round(performance.now() - t0) });
    } catch (err) {
      self.postMessage({ type: "failed", message: String((err && err.message) || err) });
    }
    return;
  }
  if (data.type === "run") {
    const t0 = performance.now();
    let result;
    try {
      result = JSON.parse(runJson(data.payload));
    } catch (err) {
      result = { status: "harness-error", tests: [], stops: [], stopped: null,
                 error: { type: "WorkerError", message: String((err && err.message) || err) } };
    }
    self.postMessage({ type: "result", id: data.id, result, ms: Math.round(performance.now() - t0) });
  }
};
