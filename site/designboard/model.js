// The board's state is the graph: nothing here is stored that the checks
// could disagree with. A node belongs to the zone, subnet and VPC whose boxes
// hold its icon's centre; that is computed on demand, never saved, so moving a
// part into a box is the whole gesture for "run it there".
//
//   state = { nodes:  [{ id, part, name, x, y, multiAz? }]     x,y = icon centre
//             groups: [{ id, part, name, x, y, w, h }]          x,y = top left
//             edges:  [{ id, from, to, label, guards }] }       guards = { timeout, retries, breaker, fallback }
//
// A -> B means A sends a request or a message to B. The answer rides back on
// the same arrow, so an arrow is never drawn for a reply.

export const KINDS = {
  SERVING: new Set(["compute", "function", "gateway"]),     // can receive the API request and enforce who owns what
  CODE: new Set(["compute", "function"]),                   // runs your code
  DB: new Set(["relational", "nosql"]),                     // durable truth
  ASYNC: new Set(["queue", "topic", "bus", "stream", "workflow"]),
  HOLDER: new Set(["queue", "stream", "workflow"]),         // keeps a job until something takes it
  STORE: new Set(["relational", "nosql", "objects"]),       // somewhere a result outlives the worker
};

export const GUARDS = ["timeout", "retries", "breaker", "fallback"];

export function catalogIndex(catalog) {
  const parts = new Map(catalog.parts.map((p) => [p.id, p]));
  const groups = new Map(catalog.groups.map((g) => [g.id, g]));
  return { parts, groups, catalog };
}

const inside = (g, x, y) => x >= g.x && x <= g.x + g.w && y >= g.y && y <= g.y + g.h;
const area = (g) => g.w * g.h;

export function buildModel(state, index) {
  const nodes = new Map();
  for (const n of state.nodes || []) {
    const part = index.parts.get(n.part);
    if (!part) continue;                       // a part a newer catalog removed: ignored, not fatal
    nodes.set(n.id, { ...n, p: part, kind: part.kind, placement: part.placement });
  }
  const groups = new Map();
  for (const g of state.groups || []) {
    const def = index.groups.get(g.part);
    if (!def) continue;
    groups.set(g.id, { ...g, def, type: def.type });
  }
  const edges = (state.edges || []).filter((e) => nodes.has(e.from) && nodes.has(e.to) && e.from !== e.to);
  const out = new Map([...nodes.keys()].map((k) => [k, []]));
  const inn = new Map([...nodes.keys()].map((k) => [k, []]));
  for (const e of edges) { out.get(e.from).push(e); inn.get(e.to).push(e); }

  const containing = (x, y, types) => [...groups.values()]
    .filter((g) => types.includes(g.type) && inside(g, x, y))
    .sort((a, b) => area(a) - area(b));
  const memo = new Map();
  const place = (id) => {
    if (memo.has(id)) return memo.get(id);
    const n = nodes.get(id);
    const at = (types) => (n ? containing(n.x, n.y, types)[0] || null : null);
    const r = { zone: at(["az"]), subnet: at(["public-subnet", "private-subnet"]), vpc: at(["vpc"]), region: at(["region"]) };
    memo.set(id, r);
    return r;
  };

  const model = {
    state, index, nodes, groups, edges, out, inn,
    place,
    zoneOf: (id) => place(id).zone,
    subnetOf: (id) => place(id).subnet,
    vpcOf: (id) => place(id).vpc,
    name: (id) => displayName(nodes.get(id) || groups.get(id)),
    ref: (id) => ({ __ref: true, id, name: displayName(nodes.get(id) || groups.get(id)) }),
    ofKind: (...kinds) => [...nodes.values()].filter((n) => kinds.includes(n.kind)).map((n) => n.id),
    kindOf: (id) => (nodes.get(id) || {}).kind,
    edge: (from, to) => edges.find((e) => e.from === from && e.to === to) || null,
    groupsOf: (type) => [...groups.values()].filter((g) => g.type === type),
    // Which nodes a group holds, by the same centre rule the checks use.
    members: (gid) => { const g = groups.get(gid); return g ? [...nodes.values()].filter((n) => inside(g, n.x, n.y)).map((n) => n.id) : []; },
  };
  return model;
}

export function displayName(x) {
  if (!x) return "?";
  const name = (x.name || "").trim();
  if (name) return name;
  return x.p ? x.p.short : x.def ? x.def.label : "?";
}

// Breadth-first along arrows. `expand(id)` says whether to keep going past a
// node that was reached (a queue on the request path is reached, but the work
// behind it is not waited for); `alive(id)` removes nodes; `edgeOk(e)` removes arrows.
export function reach(model, starts, { expand = () => true, alive = () => true, edgeOk = () => true } = {}) {
  const seen = new Set();
  const queue = [];
  for (const s of starts) if (model.nodes.has(s) && alive(s) && !seen.has(s)) { seen.add(s); queue.push(s); }
  const via = new Map();
  while (queue.length) {
    const u = queue.shift();
    if (!starts.includes(u) && !expand(u)) continue;
    for (const e of model.out.get(u) || []) {
      if (seen.has(e.to) || !alive(e.to) || !edgeOk(e)) continue;
      seen.add(e.to); via.set(e.to, e); queue.push(e.to);
    }
  }
  seen.via = via;            // the arrow each node was first reached by, for naming a path
  return seen;
}

// One shortest path from any start to `target`, as node ids, or null.
export function pathTo(model, starts, target, opts = {}) {
  const got = reach(model, starts, opts);
  if (!got.has(target)) return null;
  const via = got.via, path = [target];
  let at = target;
  while (via.has(at)) { at = via.get(at).from; path.unshift(at); }
  return path;
}

// Nodes reached on the request path: everything a client's request touches
// while the client is still waiting. A queue, topic, bus, stream or workflow is
// reached, but whatever takes work from it is not on the request path.
export function syncReach(model, starts, opts = {}) {
  return reach(model, starts, { ...opts, expand: (id) => !KINDS.ASYNC.has(model.kindOf(id)) && (opts.expand ? opts.expand(id) : true) });
}

export const clients = (model) => model.ofKind("client");
