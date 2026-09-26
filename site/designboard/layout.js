// Lay out a diagram the way AWS architects draw one. Pure: a graph in,
// positions out, the same positions for the same graph every time.
//
// A generic layered layout (ELK, tried first) treats two Availability Zones
// as consecutive steps whenever an arrow crosses between them, and put zone b
// before zone a. Architects draw zones as parallel lanes. So the conventions
// are written down here instead:
//   * outside boxes, the flow runs left to right: a column per step
//   * a VPC holds its zones side by side, as lanes of equal height; a part in
//     the VPC but in no zone (a load balancer, say) sits in a row above the
//     lanes if requests reach it first, below them if it comes after
//   * a zone stacks its subnets, public above private
//   * a subnet stacks its parts top to bottom in the order requests reach them
// Then one pass the conventions cannot make on their own: every column of a
// flow is centred, so an arrow that skips a column runs straight through
// whatever sits in it (seen on sketch 3: the API's arrow to the results table
// crossed the queue and the worker). So each flow's columns are shifted and
// reordered by a small search that scores the drawing the way a reader sees
// it: an arrow through a part is worst, two arrows crossing next, then length,
// which is what lines an entry point up with what it calls.
//
// Because all of it is deterministic, an edit that does not change the shape
// of the graph (a database swapped for a cache) moves nothing at all.
//
//   graph = { parts: [{ id, part, inside? }], boxes: [{ id, type, name?, inside? }], arrows: [{ from, to }] }
//   -> { nodes: { id: { x, y } }, boxes: { id: { x, y, w, h } }, width, height, fits }

const ICON = 44, HALF = ICON / 2;
const DOORS = new Set(["igw", "lb", "waf", "gateway"]);
const PARENTS = {                       // where each kind of box may sit
  region: ["cloud", null], vpc: ["region", "cloud", null], az: ["vpc", "region"],
  "public-subnet": ["az", "vpc"], "private-subnet": ["az", "vpc"],
  asg: ["public-subnet", "private-subnet", "az", "vpc"], cloud: [null],
};

// A drawing bigger than the canvas is drawn on a bigger one, of the same
// shape, which the board shows zoomed out: smaller, and nothing on top of
// anything. Squeezing the spacing instead (the first fallback) ran AWS's long
// names into each other. Past MAX_ZOOM the text would be too small to read,
// so what is left over is squeezed after all, and fits says so.
export const MAX_ZOOM = 1.6;
export function layout(graph, { kindOf = () => "", measure = () => 60, measureBox = () => 0, measureEdge = () => 0, W = 860, H = 540 } = {}) {
  let r;
  for (const tight of [false, true]) {
    r = attempt(graph, { kindOf, measure, measureBox, measureEdge, tight, W, H });
    if (!r.canvas) break;
  }
  return r;
}

function attempt(graph, { kindOf, measure, measureBox, measureEdge, tight, W, H }) {
  const S = tight
    ? { gapX: 22, gapY: 12, pad: 10, head: 28, slotH: ICON + 30 + 6, colGap: 34, labelGap: 12, boxGap: 24, arrow: 56 }
    : { gapX: 34, gapY: 18, pad: 14, head: 30, slotH: ICON + 34 + 10, colGap: 54, labelGap: 16, boxGap: 30, arrow: 70 };
  const parts = graph.parts || [], boxes = graph.boxes || [], arrows = graph.arrows || [];
  const boxById = new Map(boxes.map((b) => [b.id, b]));
  const ids = new Set(parts.map((p) => p.id));
  const labelW = new Map(parts.map((p) => [p.id, Math.max(ICON, measure(p.id) || 0)]));

  // Where things sit: a box only where AWS nests it; anything else at the top.
  const parentOf = new Map();
  for (const b of boxes) {
    const p = b.inside && boxById.get(b.inside);
    parentOf.set(b.id, p && (PARENTS[b.type] || [null]).includes(p.type) && !descends(p.id, b.id) ? p.id : null);
  }
  function descends(a, b) { for (let at = a, n = 0; at && n < 50; at = boxById.get(at) && boxById.get(at).inside, n++) if (at === b) return true; return false; }
  for (const p of parts) parentOf.set(p.id, p.inside && boxById.has(p.inside) ? p.inside : null);

  // Steps: the longest chain of requests that reaches each part. A part that
  // starts requests (a client) is step 0; a cycle is broken where it closes.
  const edges = arrows.filter((a) => ids.has(a.from) && ids.has(a.to) && a.from !== a.to);
  // A labelled arrow needs room for its chip between the two icons: the board
  // centres the chip 42% along the line, so the line has to be long enough
  // for the chip to clear the icon it leaves.
  const chip = edges.filter((e) => e.text).map((e) => ({ from: e.from, to: e.to, w: (measureEdge(e.text) || 0) + 10 }));
  const inn = new Map([...ids].map((i) => [i, []]));
  for (const a of edges) inn.get(a.to).push(a.from);
  const rank = new Map(), state = new Map();
  // A part with no arrows has no step: it must not pull its zone, or a whole
  // VPC, into the first column (seen: two NAT gateways and an internet gateway
  // with no arrows put the VPC in the same column as Users, and Users under
  // it). With no arrows at all, the reader's order is the flow.
  const linkedIds = new Set(edges.flatMap((e) => [e.from, e.to]));
  const order = [...ids].sort((a, b) => (kindOf(a) === "client" ? 0 : 1) - (kindOf(b) === "client" ? 0 : 1) || parts.findIndex((p) => p.id === a) - parts.findIndex((p) => p.id === b));
  // A cycle (an upload bucket that also receives the transcoded video) has to
  // be broken somewhere, and where decides the whole drawing. Walk forward
  // from where requests start (clients, then parts nothing calls): the arrow
  // that comes back to something already on the walk is the one drawn going
  // backwards. Breaking it wherever the array order met it first made a Lambda
  // in the middle of a pipeline a starting point, put the whole cloud in
  // Users' column, and ran S3 -> Lambda right to left across the drawing.
  const outs = new Map([...ids].map((i) => [i, []]));
  for (const a of edges) outs.get(a.from).push(a.to);
  const back = new Set(), colour = new Map();
  const walk = (u) => { colour.set(u, 1); for (const v of outs.get(u)) { if (colour.get(v) === 1) back.add(u + "\u0000" + v); else if (!colour.get(v)) walk(v); } colour.set(u, 2); };
  const starts = [...order.filter((u) => kindOf(u) === "client"), ...order.filter((u) => kindOf(u) !== "client" && !inn.get(u).length), ...order];
  for (const u of starts) if (linkedIds.has(u) && !colour.get(u)) walk(u);
  function visit(u) {
    if (state.get(u) === 2) return rank.get(u);
    state.set(u, 1);
    let r = 0;
    if (kindOf(u) !== "client") for (const v of inn.get(u)) { if (back.has(v + "\u0000" + u) || state.get(v) === 1) continue; r = Math.max(r, visit(v) + 1); }
    state.set(u, 2); rank.set(u, r);
    return r;
  }
  for (const u of order) if (linkedIds.has(u)) visit(u);
  if (!edges.length) order.forEach((u, i) => rank.set(u, i));
  const kids = (pid) => [...parts.filter((p) => parentOf.get(p.id) === pid).map((p) => ({ t: "part", id: p.id })),
                         ...boxes.filter((b) => parentOf.get(b.id) === pid).map((b) => ({ t: "box", id: b.id, type: b.type, name: b.name || "" }))];
  const minRank = (item) => {
    if (item.t === "part") return rank.has(item.id) ? rank.get(item.id) : Infinity;
    const rs = kids(item.id).map(minRank).filter((x) => Number.isFinite(x));
    return rs.length ? Math.min(...rs) : Infinity;
  };

  const flows = [];                    // every left-to-right container, the whole drawing first
  const strips = [];                   // every row of parts inside a box: the search picks left, centre or right

  // Sizes bottom up. Each item gets { w, h, at(x, y, pos) } and lays itself out.
  function sized(item) {
    if (item.t === "part") {
      const w = labelW.get(item.id) + 12;
      return { ...item, w, h: S.slotH, rank: minRank(item), at: (x, y, pos) => { pos.nodes[item.id] = { x: x + w / 2, y: y + 6 + HALF }; } };
    }
    const inner = kids(item.id).map(sized);
    // How a box arranges what is in it, by what kind of box it is.
    const hasZones = inner.some((c) => c.type === "az");
    const body = item.type === "vpc" && hasZones ? lanes(inner)
      : item.type === "az" || item.type === "vpc" ? stack(inner)
      : item.type === "region" || item.type === "cloud" ? columns(inner)
      : rows(inner);
    const w = Math.max(160, body.w + 2 * S.pad, measureBox(item.id) || 0), h = Math.max(70, S.head + body.h + S.pad);
    return { ...item, w, h, rank: minRank(item), body,
      at(x, y, pos, stretchW, stretchH) {
        const W2 = Math.max(w, stretchW || 0), H2 = Math.max(h, stretchH || 0);
        pos.boxes[item.id] = { x, y, w: W2, h: H2 };
        body.at(x + S.pad, y + S.head, pos, W2 - 2 * S.pad, H2 - S.head - S.pad);
      } };
  }
  // Items in the order requests reach them; ties keep the order they came in.
  const byRank = (items) => [...items].sort((a, b) => (a.rank ?? Infinity) - (b.rank ?? Infinity));
  function group(items) {
    const m = new Map();
    for (const it of byRank(items)) { const k = Number.isFinite(it.rank) ? it.rank : 1e9; if (!m.has(k)) m.set(k, []); m.get(k).push(it); }
    return [...m.values()];
  }
  // Top to bottom by step, side by side within a step: inside a subnet.
  function rows(items) {
    const rs = group(items).map((r) => ({ items: r, w: r.reduce((s, it) => s + it.w, 0) + S.gapX * (r.length - 1), h: Math.max(...r.map((it) => it.h)) }));
    // An arrow down from one row to the next leaves below the part's labels,
    // so a chip on it needs more than the usual gap.
    const gaps = rs.slice(1).map((r, i) => (linked(rs[i].items, r.items, true) ? Math.max(S.gapY, 30) : S.gapY));
    const w = rs.length ? Math.max(...rs.map((r) => r.w)) : 0, h = rs.reduce((s, r) => s + r.h, 0) + gaps.reduce((s, g) => s + g, 0);
    for (const r of rs) { r.align = 0; strips.push(r); }
    return { w, h, at(x, y, pos, W2) {
      let yy = y;
      rs.forEach((r, i) => { let xx = x + (((W2 || w) - r.w) / 2) * (1 + r.align); for (const it of r.items) { it.at(xx, yy + (r.h - it.h) / 2, pos); xx += it.w + S.gapX; } yy += r.h + (gaps[i] || 0); });
    } };
  }
  // One row, side by side, in the order requests reach them.
  function line(items) {
    const strip = { items: byRank(items), align: 0 };
    strip.order = strip.items.map((_, i) => i);
    const w = strip.items.reduce((s, it) => s + it.w, 0) + S.gapX * (strip.items.length - 1), h = Math.max(...strip.items.map((it) => it.h));
    strips.push(strip);
    return { w, h, at(x, y, pos, W2) { let xx = x + (((W2 || w) - w) / 2) * (1 + strip.align); for (const i of strip.order) { const it = strip.items[i]; it.at(xx, y + (h - it.h) / 2, pos); xx += it.w + S.gapX; } } };
  }
  // Which parts an item stands for: itself, or everything inside a box.
  function inItem(it) { return it.t === "part" ? [it.id] : parts.filter((p) => { for (let at = parentOf.get(p.id); at; at = parentOf.get(at)) if (at === it.id) return true; return false; }).map((p) => p.id); }
  // The widest chip on a labelled arrow between two sets of items (0: none).
  function linked(a, b, any) {
    const A = new Set(a.flatMap(inItem)), B = new Set(b.flatMap(inItem));
    let w = 0;
    for (const c of chip) if ((A.has(c.from) && B.has(c.to)) || (B.has(c.from) && A.has(c.to))) w = Math.max(w, c.w);
    return any ? w > 0 : w;
  }
  // Left to right by step, stacked within a step: the whole drawing, a region.
  // Each column keeps an order and a shift, which the search below chooses.
  function columns(items) {
    const cs = group(items).map((c) => ({ items: c, order: c.map((_, i) => i), dy: 0, w: Math.max(...c.map((it) => it.w)), h: c.reduce((s, it) => s + it.h, 0) + S.gapY * (c.length - 1) }));
    // The gap after each column: wide enough for any chip on an arrow to the
    // next one. Centres must be 1.2 chips + 64 apart for the chip to clear both
    // icons; a box's parts sit at least a padding and half an icon inside it.
    // (A chip slides along its arrow to a clear spot, board.js, so it needs
    // its own width of arrow between the icons: centres chip + 66 apart.)
    // The gap after each column is what it is for, not a constant: two
    // columns' labels 16px apart; at least 70px of arrow showing between two
    // icons (so a column of narrow names still gets room); 30px between a box
    // and its neighbour; and room for a chip on an arrow between two parts
    // side by side. A fixed gap on top of the widest label double-counted, and
    // a pipeline of seven parts with AWS's long names did not fit the canvas.
    // A chip's arrow into a box usually starts deep inside it, and its chip
    // lands there, so only part-to-part arrows widen a gap for one.
    const loose = (c) => c.items.filter((it) => it.t === "part");
    const hasBox = (c) => c.items.some((it) => it.t === "box");
    const gaps = cs.slice(1).map((c, i) => {
      const a = cs[i], half = (a.w + c.w) / 2;
      let g = Math.max(hasBox(a) || hasBox(c) ? S.boxGap : S.labelGap, S.arrow + ICON - half);
      const cw = linked(loose(a), loose(c));
      if (cw) g = Math.max(g, Math.ceil(cw + 66 - Math.min(...loose(a).map((it) => it.w / 2)) - Math.min(...loose(c).map((it) => it.w / 2))));
      return Math.ceil(g);
    });
    const w = cs.reduce((s, c) => s + c.w, 0) + gaps.reduce((s, g) => s + g, 0), h = cs.length ? Math.max(...cs.map((c) => c.h)) : 0;
    const flow = { cs, w, h, at(x, y, pos, W2, H2) {
      const HH = Math.max(h, H2 || 0);
      let xx = x + Math.max(0, ((W2 || w) - w) / 2);
      for (const c of cs) {
        const free = HH - c.h;
        c.room = free;
        let yy = y + free / 2 + Math.max(-free / 2, Math.min(free / 2, c.dy));
        for (const i of c.order) { const it = c.items[i]; it.at(xx + (c.w - it.w) / 2, yy, pos); yy += it.h + S.gapY; }
        xx += c.w + (gaps[cs.indexOf(c)] || 0);
      }
    } };
    flows.push(flow);
    return flow;
  }
  // Subnets stacked in a zone: public first, then private, then loose parts.
  function stack(items) {
    const weight = (it) => (it.type === "public-subnet" ? 0 : it.type === "private-subnet" ? 1 : it.t === "box" ? 2 : 3);
    const boxesIn = items.filter((it) => it.t === "box").sort((a, b) => weight(a) - weight(b) || (a.rank ?? 0) - (b.rank ?? 0));
    const loose = items.filter((it) => it.t === "part");
    const tail = loose.length ? rows(loose) : null;
    const seq = [...boxesIn, ...(tail ? [tail] : [])];
    const w = seq.length ? Math.max(...seq.map((s) => s.w)) : 0, h = seq.reduce((s, it) => s + it.h, 0) + S.gapY * Math.max(0, seq.length - 1);
    return { w, h, at(x, y, pos, W2, H2) {
      let yy = y;
      const extra = Math.max(0, (H2 || h) - h);
      seq.forEach((it, i) => {
        const last = i === boxesIn.length - 1 && !tail;
        it.at(x, yy, pos, W2 || w, last ? it.h + extra : undefined);        // subnets fill the lane's width; the last takes the slack
        yy += it.h + (last ? extra : 0) + S.gapY;
      });
    } };
  }
  // Zones as lanes: side by side, the same height, in name order; parts in the
  // VPC but in no zone go in a row above (if reached first) or below.
  function lanes(items) {
    const zones = items.filter((it) => it.type === "az").sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
    const others = items.filter((it) => it.type !== "az");
    const zr = Math.min(...zones.map((z) => z.rank));
    // A VPC's front door (its internet gateway, a load balancer, a firewall,
    // API Gateway) goes above the lanes whatever its step; anything else above
    // if requests reach it before the zones, below if after. One row each.
    const door = (o) => o.t === "part" && DOORS.has(kindOf(o.id));
    const above = others.filter((o) => door(o) || (o.rank ?? Infinity) <= zr), below = others.filter((o) => !above.includes(o));
    const top = above.length ? line(above) : null, bottom = below.length ? line(below) : null;
    // Every lane as wide as the widest and as tall as the tallest.
    const one = Math.max(...zones.map((z) => z.w)), laneH = Math.max(...zones.map((z) => z.h));
    const laneW = one * zones.length + S.gapX * (zones.length - 1);
    const w = Math.max(laneW, top ? top.w : 0, bottom ? bottom.w : 0);
    const h = (top ? top.h + S.gapY : 0) + laneH + (bottom ? S.gapY + bottom.h : 0);
    return { w, h, at(x, y, pos, W2) {
      let yy = y;
      if (top) { top.at(x, yy, pos, W2 || w); yy += top.h + S.gapY; }
      const each = Math.max(one, ((W2 || w) - S.gapX * (zones.length - 1)) / zones.length);
      let xx = x;
      for (const z of zones) { z.at(xx, yy, pos, each, laneH); xx += each + S.gapX; }
      yy += laneH;
      if (bottom) bottom.at(x, yy + S.gapY, pos, W2 || w);
    } };
  }

  const root = columns(kids(null).map(sized));
  const avail = { w: W - 32, h: H - 32 };
  const place = () => { const pos = { nodes: {}, boxes: {} }; root.at(16, 16, pos, avail.w, Math.max(root.h, avail.h)); return pos; };

  // The search: for each column of each flow, the shift and order that make
  // the drawing read best, holding the rest still; round again until nothing
  // improves. Candidate shifts are the ones that put an arrow level (an arrow
  // between this column and anything else, made horizontal), plus a coarse
  // grid, so a clean straight arrow is always on the menu.
  const rect = new Map(parts.map((p) => [p.id, labelW.get(p.id) / 2 + 3]));
  function score(pos) {
    let s = 0;
    const segs = edges.map((e) => [pos.nodes[e.from], pos.nodes[e.to], e]);
    for (const [a, b, e] of segs) {
      s += Math.hypot(b.x - a.x, b.y - a.y) * 0.08;
      for (const p of parts) {
        if (p.id === e.from || p.id === e.to) continue;
        const c = pos.nodes[p.id], hw = rect.get(p.id);
        if (hitsRect(a, b, c.x - hw, c.y - HALF - 3, c.x + hw, c.y + HALF + 36)) s += 1000;
      }
    }
    // A box's name is read too: an arrow across it costs less than one across
    // a part, and more than a crossing.
    for (const [a, b, e] of segs) for (const bx of boxes) {
      const r = pos.boxes[bx.id];
      if (!r) continue;
      const lw = Math.max(60, (measureBox(bx.id) || 120) - 12);
      if (hitsRect(a, b, r.x + 2, r.y + 2, r.x + lw, r.y + 22)) s += 150;
    }
    for (let i = 0; i < segs.length; i++) for (let j = i + 1; j < segs.length; j++) {
      const [a, b, e] = segs[i], [c, d, f] = segs[j];
      if (e.from === f.from || e.from === f.to || e.to === f.from || e.to === f.to) continue;
      if (crosses(a, b, c, d)) s += 40;
    }
    for (const f of flows) for (const c of f.cs) s += Math.abs(c.dy) * 0.0001;     // a tie-break, never a reason
    return s;
  }
  let pos = place(), best = score(pos);
  // Moves: one column (its order and its shift), or a run of columns shifted
  // together: everything up to a column, or everything from it on. One column
  // at a time cannot straighten a chain (Users -> WAF -> ALB: moving either
  // alone gains nothing), a run can.
  const moves = [];
  for (const f of flows) f.cs.forEach((c, i) => {
    moves.push({ cols: [c], single: c });
    if (i > 0) moves.push({ cols: f.cs.slice(0, i + 1) });
    if (i < f.cs.length - 1 && i > 0) moves.push({ cols: f.cs.slice(i) });
  });
  const searchable = strips.length || flows.some((f) => f.cs.length > 1 || f.cs.some((c) => c.items.length > 1));
  for (let round = 0; round < 5 && searchable && edges.length; round++) {
    let improved = false;
    for (const mv of moves) {
      const inside = new Set(mv.cols.flatMap((c) => c.items.flatMap(inItem)));
      const orders = mv.single ? (mv.single.items.length <= 3 ? permutations(mv.single.order) : [mv.single.order, [...mv.single.order].reverse()]) : [null];
      for (const order of orders) {
        const keep = mv.cols.map((c) => ({ order: c.order, dy: c.dy }));
        if (order) mv.single.order = order;
        const probe = place();
        // Shifts that make some arrow across the edge of the run level, plus a
        // coarse grid across the room the first column has.
        const deltas = new Set([0]);
        const room = Math.min(...mv.cols.map((c) => c.room || 0));
        for (let k = -3; k <= 3; k++) deltas.add(Math.round((k / 3) * (room / 2)) - (mv.single ? mv.single.dy : 0));
        for (const e of edges) {
          const a = inside.has(e.from), b = inside.has(e.to);
          if (a === b) continue;
          const mine = a ? e.from : e.to, other = a ? e.to : e.from;
          deltas.add(Math.round(probe.nodes[other].y - probe.nodes[mine].y));
        }
        let chosen = null;
        for (const d of deltas) {
          if (mv.cols.some((c, j) => Math.abs(keep[j].dy + d) > (c.room || 0) / 2 + 0.5)) continue;
          mv.cols.forEach((c, j) => { c.dy = keep[j].dy + d; });
          const p = place(), sc = score(p);
          if (sc < best - 0.01) { best = sc; pos = p; chosen = mv.cols.map((c) => ({ order: c.order, dy: c.dy })); }
        }
        if (chosen) { mv.cols.forEach((c, j) => Object.assign(c, chosen[j])); improved = true; }
        else mv.cols.forEach((c, j) => Object.assign(c, keep[j]));
      }
    }
    // Rows inside boxes: left, centre or right, and their order when short.
    for (const st of strips) {
      const keep = { align: st.align, order: st.order };
      const orders = st.order ? (st.items.length <= 3 ? permutations(st.order) : [st.order]) : [null];
      let chosen = null;
      for (const order of orders) for (const align of [0, -1, 1]) {
        if (order) st.order = order;
        st.align = align;
        const p = place(), sc = score(p);
        if (sc < best - 0.01) { best = sc; pos = p; chosen = { align, order: st.order }; }
      }
      if (chosen) { Object.assign(st, chosen); improved = true; }
      else Object.assign(st, keep);
    }
    if (!improved) break;
  }

  // Centre what was drawn on the canvas, zooming the canvas out if it needs
  // more room (see MAX_ZOOM).
  const nodeBox = (id) => { const c = pos.nodes[id], hw = labelW.get(id) / 2; return [c.x - hw, c.y - HALF - 10, c.x + hw, c.y + HALF + 36]; };
  const all = [...parts.map((p) => nodeBox(p.id)), ...Object.values(pos.boxes).map((b) => [b.x, b.y - 10, b.x + b.w, b.y + b.h])];
  const x0 = all.length ? Math.min(...all.map((r) => r[0])) : 0, y0 = all.length ? Math.min(...all.map((r) => r[1])) : 0;
  const x1 = all.length ? Math.max(...all.map((r) => r[2])) : 0, y1 = all.length ? Math.max(...all.map((r) => r[3])) : 0;
  const bw = x1 - x0, bh = y1 - y0, m = 12;
  const need = Math.max(1, (bw + 2 * m) / W, (bh + 2 * m) / H), zoom = Math.min(need, MAX_ZOOM);
  const CW = Math.round(W * zoom), CH = Math.round(CW * H / W);
  const fits = need <= MAX_ZOOM;
  const sx = Math.min(1, (CW - 2 * m) / (bw || 1)), sy = Math.min(1, (CH - 2 * m) / (bh || 1));
  const ox = (CW - bw * sx) / 2, oy = (CH - bh * sy) / 2;
  const X = (x) => ox + (x - x0) * sx, Y = (y) => oy + (y - y0) * sy;
  const snap = (v) => Math.round(v / 2) * 2;
  const out = { nodes: {}, boxes: {}, width: Math.round(bw), height: Math.round(bh), fits, canvas: zoom > 1 ? { w: CW, h: CH } : null };
  for (const [k, n] of Object.entries(pos.nodes)) out.nodes[k] = { x: snap(X(n.x)), y: snap(Y(n.y)) };
  for (const [k, b] of Object.entries(pos.boxes)) out.boxes[k] = { x: snap(X(b.x)), y: snap(Y(b.y)), w: snap(b.w * sx), h: snap(b.h * sy) };
  return out;
}

function permutations(a) {
  if (a.length <= 1) return [a];
  return a.flatMap((x, i) => permutations([...a.slice(0, i), ...a.slice(i + 1)]).map((p) => [x, ...p]));
}

// Does the segment a-b pass through the rectangle (Liang-Barsky)?
export function hitsRect(a, b, x0, y0, x1, y1) {
  let t0 = 0, t1 = 1;
  const dx = b.x - a.x, dy = b.y - a.y;
  for (const [p, q] of [[-dx, a.x - x0], [dx, x1 - a.x], [-dy, a.y - y0], [dy, y1 - a.y]]) {
    if (p === 0) { if (q < 0) return false; continue; }
    const t = q / p;
    if (p < 0) { if (t > t1) return false; if (t > t0) t0 = t; }
    else { if (t < t0) return false; if (t < t1) t1 = t; }
  }
  return t0 <= t1;
}
export function crosses(a, b, c, d) {
  const o = (p, q, r) => Math.sign((q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x));
  return o(a, b, c) * o(a, b, d) < 0 && o(c, d, a) * o(c, d, b) < 0;
}
