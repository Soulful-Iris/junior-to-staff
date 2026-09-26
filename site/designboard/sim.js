// Break it: fail parts or zones and see what a member can still do.
//
// Two kinds of failure, because that is how they feel from the outside:
//   * a part of yours that fails is GONE: a call to it errors at once;
//   * an outside service that fails HANGS: a call to it waits until something
//     gives up. Whatever called it without a timeout waits forever, and so does
//     whatever waited on that. A timeout turns the hang into a slow error; a
//     circuit breaker behind the timeout stops calling, so it costs nothing.
// That difference is sketch 4's whole lesson, so it is modelled, not described.
import { KINDS, clients, reach, syncReach } from "./model.js";

export const multiAzOn = (n) => (n.multiAz != null ? !!n.multiAz : !!n.p.multiAzDefault);
// Runs in exactly one zone: instances, containers, a NAT gateway, and a
// database or cache until Multi-AZ is switched on.
export const zonal = (n) => n.placement === "zonal" || (n.placement === "multiaz" && !multiAzOn(n));
export const FAILS = new Set(["az", "public-subnet", "private-subnet", "region"]);

// Everything a set of failed parts and boxes takes down.
export function downSet(model, failed = {}) {
  const down = new Set([...(failed.nodes || [])].filter((id) => model.nodes.has(id)));
  for (const gid of failed.groups || []) {
    const g = model.groups.get(gid);
    if (!g || !FAILS.has(g.type)) continue;
    for (const id of model.members(gid)) {
      const n = model.nodes.get(id);
      // A region takes everything in it but what runs at the edge; a zone or a
      // subnet takes only what runs in one zone. SQS drawn inside a zone's box
      // is still regional, and survives it.
      if (g.type === "region" ? !["edge", "global"].includes(n.placement) : zonal(n)) down.add(id);
    }
  }
  return down;
}

const RANK = { ok: 0, slow: 1, stuck: 2, down: 3, hang: 3 };

export function simulate(model, failed = {}) {
  const down = downSet(model, failed);
  const health = new Map();
  for (const [id, n] of model.nodes) health.set(id, down.has(id) ? (n.kind === "external" ? "hang" : "down") : "ok");
  // Waiting spreads backwards along synchronous calls from code you run. A
  // queue in between absorbs it: the caller has already been answered.
  for (let changed = true; changed;) {
    changed = false;
    for (const e of model.edges) {
      if (!KINDS.CODE.has(model.kindOf(e.from)) || KINDS.ASYNC.has(model.kindOf(e.to))) continue;
      if (health.get(e.from) === "down") continue;
      const t = health.get(e.to), g = e.guards || {};
      let effect = null;
      if (t === "hang" || t === "stuck") effect = !g.timeout ? "stuck" : g.breaker ? null : "slow";
      else if (t === "slow") effect = "slow";
      if (effect && RANK[effect] > RANK[health.get(e.from)]) { health.set(e.from, effect); changed = true; }
    }
  }
  return { model, down, health, failed };
}

const passable = (sim, level) => (id) => RANK[sim.health.get(id)] <= RANK[level];

// Can a request from a client get through something that serves it to one of
// `targets`? Returns "ok", "slow" (only through something waiting on a slow
// call) or null, plus the path it took.
function served(sim, targets, { from = null, through = KINDS.SERVING } = {}) {
  const m = sim.model;
  for (const level of ["ok", "slow"]) {
    const alive = passable(sim, level);
    const starts = from || clients(m);
    // A request waits for what it reaches, and not for what sits behind a queue.
    const first = syncReach(m, starts, { alive });
    const gates = [...first].filter((id) => through.has(m.kindOf(id)));
    const second = syncReach(m, gates, { alive });
    const hit = targets.find((t) => second.has(t));
    if (hit) return { level, hit, gates };
  }
  return null;
}

// What each capability needs, in the words the board shows beside it.
export const CAPABILITIES = {
  // A member saves a bookmark: a client, through your API, to a database.
  save(sim) {
    const m = sim.model, dbs = m.ofKind("relational", "nosql");
    if (!dbs.length || !clients(m).length) return { status: "na" };
    const r = served(sim, dbs);
    if (!r) return { status: "down" };
    return { status: r.level === "ok" ? "ok" : "slow", at: r.hit };
  },
  // Reading the list: a database, or a cache when the database is gone.
  read(sim) {
    const m = sim.model, dbs = m.ofKind("relational", "nosql"), caches = m.ofKind("cache", "cdn");
    if (!dbs.length || !clients(m).length) return { status: "na" };
    const r = served(sim, dbs);
    if (r) {
      const cacheGone = caches.some((c) => sim.down.has(c));
      return { status: r.level === "ok" ? "ok" : "slow", at: r.hit, note: cacheGone ? "load" : null };
    }
    // The database is out of reach: whatever a cache still holds can be read.
    const viaCache = served(sim, m.ofKind("cache"));
    if (viaCache) return { status: "degraded", at: viaCache.hit, note: "cached" };
    const edge = reach(m, clients(m), { alive: passable(sim, "ok") });
    const viaCdn = m.ofKind("cdn").find((c) => edge.has(c));
    return viaCdn ? { status: "degraded", at: viaCdn, note: "cached" } : { status: "down" };
  },
  // Accepting a refresh: the API puts a job somewhere it will be kept.
  accept(sim) {
    const m = sim.model, holders = m.ofKind(...KINDS.HOLDER);
    if (!holders.length || !clients(m).length) return { status: "na" };
    const r = served(sim, holders);
    return r ? { status: r.level === "ok" ? "ok" : "slow", at: r.hit } : { status: "down" };
  },
  // Doing the work: something takes jobs from the holder and reaches the
  // outside service. A dead worker pauses the work; nothing is lost.
  process(sim) {
    const m = sim.model;
    const holders = m.ofKind(...KINDS.HOLDER);
    const consumers = [...new Set(m.edges.filter((e) => holders.includes(e.from) && KINDS.CODE.has(m.kindOf(e.to))).map((e) => e.to))];
    if (!consumers.length) return { status: "na" };
    const exts = m.ofKind("external");
    const working = consumers.filter((c) => !sim.down.has(c));
    if (!working.length) {
      const q = m.edges.find((e) => holders.includes(e.from) && consumers.includes(e.to));
      return { status: "paused", at: q && q.from, note: "waiting" };
    }
    const call = m.edges.find((e) => working.includes(e.from) && exts.includes(e.to));
    if (!call) return { status: "na" };
    if (sim.health.get(call.to) === "hang") {
      const g = call.guards || {};
      return { status: g.timeout ? "degraded" : "down", at: call.from, note: g.timeout ? "retrying" : "hanging" };
    }
    return { status: sim.health.get(call.from) === "ok" ? "ok" : "slow", at: call.from };
  },
  // Seeing the result: a client can read what the worker wrote.
  result(sim) {
    const m = sim.model, holders = m.ofKind(...KINDS.HOLDER);
    const consumers = new Set(m.edges.filter((e) => holders.includes(e.from) && KINDS.CODE.has(m.kindOf(e.to))).map((e) => e.to));
    const stores = [...new Set(m.edges.filter((e) => consumers.has(e.from) && KINDS.STORE.has(m.kindOf(e.to))).map((e) => e.to))];
    if (!stores.length || !clients(m).length) return { status: "na" };
    const r = served(sim, stores);
    return r ? { status: r.level === "ok" ? "ok" : "slow", at: r.hit } : { status: "down" };
  },
  // The optional preview: through your code to the third party.
  preview(sim) {
    const m = sim.model, exts = m.ofKind("external");
    if (!exts.length || !clients(m).length) return { status: "na" };
    const callers = m.edges.filter((e) => exts.includes(e.to) && KINDS.CODE.has(m.kindOf(e.from)));
    if (!callers.length) return { status: "na" };
    const r = served(sim, callers.map((e) => e.from));
    if (!r) return { status: "down" };
    const call = callers.find((e) => e.from === r.hit) || callers[0];
    if (sim.health.get(call.to) === "hang") {
      const g = call.guards || {};
      if (g.timeout && g.fallback) return { status: "degraded", at: call.from, note: g.breaker ? "fallback-fast" : "fallback-slow" };
      return { status: "down", at: call.from, note: g.timeout ? "errors" : "hanging" };
    }
    return { status: r.level === "ok" && sim.health.get(call.from) === "ok" ? "ok" : "slow", at: call.from };
  },
};
CAPABILITIES.critical = CAPABILITIES.save;
