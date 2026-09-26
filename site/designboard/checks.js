// The checks: pure functions over the board's graph. Each asks a question a
// reviewer would ask of an architecture diagram, and answers in a sentence that
// names the reader's own parts. Three answers:
//   pass  - it holds, and here is why, in their parts
//   fail  - it does not, here is the part or arrow that breaks it (marked red)
//   wait  - it cannot be asked yet (no database to protect, no queue to drain)
// Every check reads kinds and arrows, never the names a reader typed: names
// are only for the sentences. Each is run both ways by site/designboard/test.
import { KINDS, clients, reach, syncReach, pathTo } from "./model.js";
import { arrowProblem, REPLY } from "./rules.js";
import { simulate, CAPABILITIES, zonal, multiAzOn } from "./sim.js";

// ----------------------------------------------------------------- sentences
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const refHtml = (r) => `<b class="db-ref" data-ref="${esc(r.id)}">${esc(r.name)}</b>`;
// "a, b and c". Parts that share a name are said once with a count: two
// unnamed databases are "RDS (×2)", not "RDS and RDS".
function and(items) {
  const groups = [];
  for (const x of items) {
    const key = x && x.__ref ? "ref:" + x.name : "txt:" + x;
    const g = groups.find((y) => y.key === key);
    if (g) g.n++; else groups.push({ key, x, n: 1 });
  }
  const xs = groups.map(({ x, n }) => (x && x.__ref ? refHtml(x) : esc(x)) + (n > 1 ? ` (×${n})` : ""));
  return xs.length <= 1 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1];
}
// h`...${ref}...` escapes what it interpolates and bolds **literal** text.
export function h(strings, ...vals) {
  let out = "";
  strings.forEach((s, i) => {
    out += s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
    if (i < vals.length) {
      const v = vals[i];
      out += v && v.__ref ? refHtml(v) : Array.isArray(v) ? and(v) : v && v.__html ? v.__html : esc(v);
    }
  });
  return out;
}
const raw = (s) => ({ __html: s });
const arrow = (m, e) => raw(`${refHtml(m.ref(e.from))} → ${refHtml(m.ref(e.to))}`);
const pathHtml = (m, ids) => raw(ids.map((id) => refHtml(m.ref(id))).join(" → "));

const pass = (html, offenders) => ({ status: "pass", html, offenders: offenders || {} });
const fail = (html, offenders) => ({ status: "fail", html, offenders: offenders || {} });
const wait = (html) => ({ status: "wait", html, offenders: {} });
const refs = (m, ids) => ids.map((id) => m.ref(id));

// ------------------------------------------------------------ shared queries
// What a member's request reaches while they wait for the answer: through
// your API, but not past a queue. Work behind a queue is not "serving" anyone.
const serving = (m) => [...syncReach(m, clients(m))].filter((id) => KINDS.SERVING.has(m.kindOf(id)));
const dbs = (m) => m.ofKind("relational", "nosql");
// Databases a request reaches after something that can enforce ownership.
function servedDbs(m) {
  const gates = serving(m);
  const after = syncReach(m, gates);
  return dbs(m).filter((d) => after.has(d));
}
const holders = (m) => m.ofKind(...KINDS.HOLDER);
const consumersOf = (m, hs) => [...new Set(m.edges.filter((e) => hs.includes(e.from) && KINDS.CODE.has(m.kindOf(e.to))).map((e) => e.to))];
const intoExternal = (m) => m.edges.filter((e) => m.kindOf(e.to) === "external");
const partList = (m, ids) => refs(m, ids);

// ------------------------------------------------------------------- checks
export const CHECKS = {
  arrows: {
    title: "Every arrow is one AWS can make",
    ask: "An arrow is a request or a message. Each one has to be something that part can really send to that part.",
    run(m) {
      if (!m.edges.length) return fail(h`No arrows yet. Draw what sends requests to what: from a part's dot to the part it calls.`);
      const bad = [];
      for (const e of m.edges) {
        const a = m.nodes.get(e.from), b = m.nodes.get(e.to);
        let why = arrowProblem(a.p, b.p);
        if (!why) continue;
        if (b.kind === "client" || m.edge(e.to, e.from)) why = REPLY;
        bad.push({ e, why });
      }
      if (!bad.length) return pass(h`All ${m.edges.length === 1 ? "1 arrow is" : m.edges.length + " arrows are"} requests AWS can send.`);
      const first = bad[0];
      const more = bad.length > 1 ? h` And ${bad.length - 1} more, also marked.` : "";
      return fail(h`${arrow(m, first.e)} is not a request AWS can send. ${first.why}` + more, { edges: bad.map((b) => b.e.id) });
    },
  },

  reachesApi: {
    title: "A request from the browser reaches your API",
    ask: "Something that runs your API (a container, a function, or API Gateway) receives the member's request.",
    run(m) {
      const cs = clients(m);
      if (!cs.length) return fail(h`Start where requests start: add **Users** or a **Client (browser)**.`);
      const got = serving(m);
      if (!got.length) return fail(h`No arrow from ${refs(m, cs)} leads to anything that runs code. Draw one to what receives the POST: an ALB in front of ECS, or API Gateway in front of Lambda.`, { nodes: cs });
      const p = pathTo(m, cs, got[0]);
      return pass(h`${pathHtml(m, p)} carries the member's request to code that can answer it.`);
    },
  },

  commitsToDb: {
    title: "Bookmarks are committed to a database",
    ask: "The bookmark is written to a database that survives a restart, by the code that serves the request.",
    run(m) {
      const all = dbs(m);
      if (!all.length) {
        const caches = m.ofKind("cache"), objects = m.ofKind("objects");
        if (caches.length) return fail(h`${m.ref(caches[0])} is a disposable copy: an eviction or a restart loses what is in it. A bookmark that must survive needs a database: RDS, Aurora or DynamoDB.`, { nodes: caches });
        if (objects.length) return fail(h`${m.ref(objects[0])} keeps files, but a bookmark is a record you look up by owner. That is a database's job: RDS, Aurora or DynamoDB.`, { nodes: objects });
        return fail(h`Nothing on the board keeps a bookmark. Add the database that holds them: RDS, Aurora or DynamoDB.`);
      }
      const got = servedDbs(m);
      if (!got.length) return fail(h`${refs(m, all)} ${all.length === 1 ? "is" : "are"} on the board, but no request reaches ${all.length === 1 ? "it" : "them"} through your API. Draw the arrow from the code that serves the request to the database.`, { nodes: all });
      const gate = serving(m).find((s) => syncReach(m, [s]).has(got[0]));
      return pass(h`${m.ref(gate)} writes to ${m.ref(got[0])}, which keeps it through any restart of the code in front of it.`);
    },
  },

  noDirectDb: {
    title: "The browser never talks to the database directly",
    ask: "Every way from a client to a database goes through your API, where it is checked who owns what.",
    run(m) {
      const all = dbs(m), cs = clients(m);
      if (!all.length || !cs.length) return wait(h`Waits for a client and a database on the board.`);
      const noApi = { alive: (id) => !KINDS.SERVING.has(m.kindOf(id)) };
      const around = reach(m, cs, noApi);
      const hit = all.filter((d) => around.has(d));
      if (!hit.length) return pass(h`Every way to ${refs(m, all)} passes through code that can check who owns a bookmark.`);
      const bad = m.edges.filter((e) => hit.includes(e.to) && around.has(e.from));
      const who = cs.find((c) => reach(m, [c], noApi).has(hit[0]));
      return fail(h`${m.ref(who)} reaches ${m.ref(hit[0])} without your API in between, so nothing checks that a bookmark is theirs before it is written. Send the request through the API.`, { edges: bad.map((e) => e.id), nodes: hit });
    },
  },

  spread: {
    title: "Reads are served by more than one copy of your API",
    ask: "A load balancer (or API Gateway) spreads requests over at least two copies of the API, or Lambda runs one per request.",
    run(m) {
      const got = serving(m);
      const code = got.filter((id) => KINDS.CODE.has(m.kindOf(id)));
      if (!code.length) return wait(h`Waits for a request to reach your API.`);
      const fn = code.find((id) => m.kindOf(id) === "function");
      if (fn) return pass(h`${m.ref(fn)} is Lambda: AWS runs one copy per request in flight, so there is no single copy to outgrow.`);
      const cs = clients(m);
      const bypass = reach(m, cs, { alive: (id) => !["lb", "gateway"].includes(m.kindOf(id)) });
      const direct = code.filter((id) => bypass.has(id));
      if (direct.length) {
        const e = m.edges.find((x) => x.to === direct[0] && bypass.has(x.from));
        return fail(h`${m.ref(e ? e.from : cs[0])} calls ${m.ref(direct[0])} directly, so no other copy ever takes its share. Put a load balancer in front of the copies.`, { nodes: direct, edges: e ? [e.id] : [] });
      }
      if (code.length < 2) return fail(h`Every read reaches ${m.ref(code[0])} alone. One copy is a ceiling on throughput and a single point of failure: put two behind the load balancer.`, { nodes: code });
      const front = [...reach(m, cs)].find((id) => ["lb", "gateway"].includes(m.kindOf(id)));
      return pass(h`${m.ref(front)} spreads requests over ${refs(m, code)}.`);
    },
  },

  readsSkipDb: {
    title: "Reads can be answered without the database",
    ask: "Repeated reads are answered by a copy kept closer: a cache the API checks first, or CloudFront in front.",
    run(m) {
      const cs = clients(m);
      const cdnHit = m.ofKind("cdn").find((c) => reach(m, cs).has(c) && serving(m).some((s) => reach(m, [c]).has(s)));
      if (cdnHit) return pass(h`${m.ref(cdnHit)} answers a repeated read at the edge, before it reaches your API.`);
      const code = serving(m).filter((id) => KINDS.CODE.has(m.kindOf(id)));
      const lookups = m.edges.filter((e) => code.includes(e.from) && m.kindOf(e.to) === "cache");
      if (lookups.length) {
        const db = servedDbs(m)[0];
        return pass(h`${m.ref(lookups[0].from)} looks in ${m.ref(lookups[0].to)} first` + (db ? h` and goes to ${m.ref(db)} only on a miss.` : "."));
      }
      const caches = m.ofKind("cache");
      if (caches.length) return fail(h`${m.ref(caches[0])} is on the board, but no code that serves a read looks anything up in it. Draw the arrow from the API to the cache.`, { nodes: caches });
      const db = servedDbs(m)[0];
      return fail(db ? h`Every read goes to ${m.ref(db)}. Add a cache the API checks first, such as ElastiCache, so repeated reads never reach the database.` : h`Every read has to reach a database. Add a cache the API checks first, such as ElastiCache.`, { nodes: db ? [db] : [] });
    },
  },

  storesPrivate: {
    title: "No database or cache is reachable from the internet",
    ask: "Databases and caches that live in your VPC sit in a private subnet: nothing on the internet has a route to them.",
    run(m) {
      const stores = [...m.nodes.values()].filter((n) => n.p.vpc && ["relational", "nosql", "cache", "search", "proxy"].includes(n.kind));
      const outside = [...m.nodes.values()].filter((n) => !n.p.vpc && KINDS.DB.has(n.kind));
      if (!stores.length) {
        if (outside.length) return pass(h`${refs(m, outside.map((n) => n.id))} ${outside.length === 1 ? "is" : "are"} not in your VPC at all: IAM, not a subnet, decides who can reach ${outside.length === 1 ? "it" : "them"}.`);
        return wait(h`Waits for a database on the board.`);
      }
      const bad = stores.filter((n) => { const s = m.subnetOf(n.id); return !s || s.type !== "private-subnet"; });
      if (!bad.length) return pass(h`${refs(m, stores.map((n) => n.id))} ${stores.length === 1 ? "sits" : "sit"} in a private subnet, with no route from the internet.`);
      const n = bad[0], s = m.subnetOf(n.id);
      if (s) return fail(h`${m.ref(n.id)} sits in ${m.ref(s.id)}, a public subnet: its route table leads to the internet gateway. Move it into a private subnet.`, { nodes: bad.map((x) => x.id), groups: [s.id] });
      return fail(h`${m.ref(n.id)} is not inside a private subnet, so its reachability is undecided. Draw a VPC with a private subnet and put it there.`, { nodes: bad.map((x) => x.id) });
    },
  },

  survivesZone: {
    title: "It keeps working if one Availability Zone fails",
    ask: "Lose any one Availability Zone and a member can still save and read a bookmark.",
    run(m) {
      const base = CAPABILITIES.save(simulate(m, {}));
      if (base.status === "na" || base.status === "down") return wait(h`Waits for a path from a client, through your API, to a database.`);
      const azs = m.groupsOf("az");
      // The parts on some path from a client to a database: those are what
      // saving a bookmark depends on.
      const fromClients = syncReach(m, clients(m)), targets = dbs(m);
      const onPath = new Set([...fromClients].filter((id) => targets.includes(id) || targets.some((d) => syncReach(m, [id]).has(d))));
      const unplaced = [...onPath].map((id) => m.nodes.get(id)).filter((n) => zonal(n) && !m.zoneOf(n.id));
      if (azs.length < 2) {
        return fail(h`Draw two Availability Zones and spread what runs in one across them. ${azs.length ? h`With only ${m.ref(azs[0].id)}, losing it loses everything in it.` : h`Right now nothing says where anything runs.`}`, { nodes: unplaced.map((n) => n.id) });
      }
      if (unplaced.length) {
        const n = unplaced[0];
        const what = n.placement === "multiaz" ? h`${m.ref(n.id)} runs in one zone until you turn on Multi-AZ for it, and it is not inside a zone.` : h`${m.ref(n.id)} runs in exactly one zone, but it is not inside one.`;
        return fail(what + h` Put it in an Availability Zone${n.placement === "multiaz" ? " or turn on Multi-AZ" : ", and a second copy in the other"}.`, { nodes: unplaced.map((x) => x.id) });
      }
      for (const az of azs) {
        const sim = simulate(m, { groups: [az.id] });
        const r = CAPABILITIES.save(sim);
        if (r.status === "down" || r.status === "na") {
          const lost = [...sim.down].filter((id) => onPath.has(id));
          const single = lost.find((id) => KINDS.DB.has(m.kindOf(id)) || m.kindOf(id) === "cache");
          const tail = single ? h` Turn on Multi-AZ for ${m.ref(single)} so a standby in another zone takes over` + (lost.some((id) => KINDS.CODE.has(m.kindOf(id))) ? h`, and run a copy of the API in each zone.` : ".") : h` Run a copy in each zone.`;
          return fail(h`Losing ${m.ref(az.id)} takes ${refs(m, lost)} with it, and nothing left can save a bookmark.` + tail, { nodes: lost, groups: [az.id], tryZone: az.id });
        }
      }
      const standby = [...onPath].filter((id) => m.nodes.get(id).placement === "multiaz" && multiAzOn(m.nodes.get(id)));
      return pass(h`Lose any one of ${refs(m, azs.map((a) => a.id))} and a path from the client to the database is still there` + (standby.length ? h`: ${refs(m, standby)} fail${standby.length === 1 ? "s" : ""} over to a standby in another zone.` : "."), { tryZone: azs[0].id });
    },
  },

  offRequestPath: {
    title: "The slow website is off the request path",
    ask: "The member's request never waits for the outside service: only a worker behind a queue calls it.",
    run(m) {
      const exts = m.ofKind("external");
      const calls = intoExternal(m);
      if (!exts.length) return wait(h`Waits for the outside service on the board.`);
      if (!calls.length) return wait(h`Waits for something that calls ${refs(m, exts)}.`);
      const sync = syncReach(m, clients(m));
      const bad = calls.filter((e) => sync.has(e.from));
      if (bad.length) return fail(h`${arrow(m, bad[0])} is on the request path: the member's request waits while ${m.ref(bad[0].from)} calls someone else's server. Accept the job, answer 202, and let a worker behind a queue make that call.`, { edges: bad.map((e) => e.id) });
      const e = calls[0];
      const holder = holders(m).find((q) => reach(m, [q]).has(e.from));
      return pass(h`${m.ref(e.to)} is called by ${m.ref(e.from)}` + (holder ? h`, which takes its work from ${m.ref(holder)}` : "") + h`, so a slow site slows the job, not the request.`);
    },
  },

  workerFromQueue: {
    title: "A worker takes the job from a durable queue",
    ask: "The API puts the job in a queue that keeps it (SQS), and a worker takes it from there and does the slow call.",
    run(m) {
      const cs = clients(m), gates = serving(m);
      const after = reach(m, gates);
      const hs = holders(m).filter((q) => after.has(q) || reach(m, cs).has(q));
      if (!hs.length) {
        const pushers = m.ofKind("topic", "bus").filter((t) => after.has(t));
        if (pushers.length) return fail(h`${m.ref(pushers[0])} pushes each message once and moves on: if the worker is busy or down, the job is gone. Put an SQS queue in front of the worker, so the job waits until something takes it.`, { nodes: pushers });
        return fail(h`Nothing keeps the job until a worker is free. Add a queue (SQS) that the API writes the job to.`);
      }
      const cons = consumersOf(m, hs);
      if (!cons.length) return fail(h`${m.ref(hs[0])} holds the jobs, but nothing takes them. Draw the arrow from the queue to the worker: SQS hands each message to whatever polls it.`, { nodes: hs });
      const exts = m.ofKind("external");
      const doer = cons.find((c) => exts.some((x) => reach(m, [c]).has(x)));
      if (exts.length && !doer) return fail(h`${m.ref(cons[0])} takes jobs from ${m.ref(hs[0])}, but never reaches ${refs(m, exts)}. The worker is what should make the slow call.`, { nodes: [cons[0]] });
      const q = hs.find((x) => m.edge(x, doer || cons[0])) || hs[0];
      return pass(h`${m.ref(doer || cons[0])} takes jobs from ${m.ref(q)}. If it is busy or restarting, the job waits in the queue instead of being lost.`);
    },
  },

  resultsDurable: {
    title: "Results outlive the worker",
    ask: "The worker writes what it found somewhere durable, so a restart does not lose it.",
    run(m) {
      const cons = consumersOf(m, holders(m));
      if (!cons.length) return wait(h`Waits for a worker that takes jobs from a queue.`);
      const writes = m.edges.filter((e) => cons.includes(e.from) && KINDS.STORE.has(m.kindOf(e.to)));
      if (writes.length) return pass(h`${m.ref(writes[0].from)} writes each result to ${m.ref(writes[0].to)}; a restart of the worker loses nothing it finished.`);
      const cached = m.edges.find((e) => cons.includes(e.from) && m.kindOf(e.to) === "cache");
      if (cached) return fail(h`${m.ref(cached.from)} writes results only to ${m.ref(cached.to)}, which can evict them at any moment. Write them to a database.`, { edges: [cached.id] });
      return fail(h`${m.ref(cons[0])} keeps what it found only in its own memory: when it restarts, the result is gone. Draw an arrow from the worker to a database.`, { nodes: [cons[0]] });
    },
  },

  statusReadable: {
    title: "The browser can find out when it is done",
    ask: "After the 202, the member can learn the result: the browser polls a status endpoint that reads it, or it is pushed to them.",
    run(m) {
      const cons = consumersOf(m, holders(m));
      const stores = [...new Set(m.edges.filter((e) => cons.includes(e.from) && KINDS.STORE.has(m.kindOf(e.to))).map((e) => e.to))];
      const cs = clients(m);
      if (!cons.length || !cs.length) return wait(h`Waits for a worker and a client.`);
      const pushed = cs.find((c) => cons.some((w) => reach(m, [w]).has(c)));
      if (pushed) return pass(h`The result is pushed to ${m.ref(pushed)} when ${m.ref(cons[0])} finishes.`);
      if (!stores.length) return wait(h`Waits for the worker to write its result somewhere.`);
      const gates = serving(m), after = syncReach(m, gates);
      const readable = stores.find((s) => after.has(s));
      if (readable) {
        const reader = gates.find((g) => syncReach(m, [g]).has(readable));
        return pass(h`${m.ref(cs[0])} asks ${m.ref(reader)}, which reads ${m.ref(readable)}: the member sees the result as soon as it is written.`);
      }
      return fail(h`${m.ref(cs[0])} has no way to read ${refs(m, stores)}. Give it a status endpoint that reads the result, or push the result to it when the job finishes.`, { nodes: stores });
    },
  },

  deadLetters: {
    title: "A job that keeps failing goes somewhere",
    ask: "A job that fails every retry is moved to a dead-letter queue, not retried forever or dropped in silence.",
    run(m) {
      const hs = holders(m).filter((q) => consumersOf(m, [q]).length);
      if (!hs.length) return wait(h`Waits for a queue a worker takes jobs from.`);
      const cons = consumersOf(m, hs);
      const dlq = m.edges.find((e) => hs.includes(e.from) && m.kindOf(e.to) === "queue" && e.to !== e.from)
        || m.edges.find((e) => cons.includes(e.from) && m.kindOf(e.to) === "queue" && !hs.includes(e.to));
      if (dlq) return pass(h`A job that runs out of retries moves from ${m.ref(dlq.from)} to ${m.ref(dlq.to)}, where someone can look at it.`);
      return fail(h`Nothing catches a job that fails every retry: ${m.ref(hs[0])} redelivers it forever, or drops it in silence when it expires. Draw an arrow from it to a second SQS queue, its dead-letter queue.`, { nodes: [hs[0]] });
    },
  },

  callDeadline: {
    title: "Every call to the slow service has a deadline",
    ask: "The arrow into the outside service has a timeout: a call that never answers is abandoned, not waited on forever.",
    run(m) {
      const calls = intoExternal(m);
      if (!calls.length) return wait(h`Waits for something that calls the outside service.`);
      const bad = calls.filter((e) => !(e.guards || {}).timeout);
      if (!bad.length) return pass(h`${arrow(m, calls[0])} gives up after its timeout, so a site that never answers cannot hold ${m.ref(calls[0].from)} forever.`);
      return fail(h`${arrow(m, bad[0])} has no timeout: a server that never answers holds ${m.ref(bad[0].from)} forever. Select the arrow and turn on **Timeout**.`, { edges: bad.map((e) => e.id) });
    },
  },

  egress: {
    title: "The worker can reach the internet",
    ask: "Whatever calls an outside service has a route out: a private subnet reaches the internet only through a NAT gateway in a public subnet, and an internet gateway.",
    run(m) {
      const calls = intoExternal(m);
      if (!calls.length) return wait(h`Waits for something that calls the outside service.`);
      for (const e of calls) {
        const s = m.subnetOf(e.from);
        if (!s) continue;
        const vpc = m.vpcOf(e.from);
        const inVpc = (id) => { const v = m.vpcOf(id); return !vpc || !v || v.id === vpc.id; };
        const igws = m.ofKind("igw").filter((id) => nearVpc(m, id, vpc));
        if (s.type === "public-subnet") {
          if (!igws.length) return fail(h`${m.ref(e.from)} is in a public subnet, but the VPC has no internet gateway, so nothing leaves it. Add an internet gateway on the VPC.`, { nodes: [e.from] });
          continue;
        }
        const nats = m.ofKind("nat").filter(inVpc);
        const goodNat = nats.find((id) => { const ns = m.subnetOf(id); return ns && ns.type === "public-subnet"; });
        if (!nats.length) return fail(h`${m.ref(e.from)} is in ${m.ref(s.id)}, a private subnet, which has no route to the internet. Add a NAT gateway in a public subnet, and an internet gateway on the VPC.`, { nodes: [e.from], groups: [s.id] });
        if (!goodNat) return fail(h`${m.ref(nats[0])} is not in a public subnet. A NAT gateway has to sit in a public subnet: it is how private subnets reach the internet, through the internet gateway.`, { nodes: [nats[0]] });
        if (!igws.length) return fail(h`${m.ref(goodNat)} forwards to the internet through an internet gateway, and the VPC has none. Add an internet gateway on the VPC.`, { nodes: [goodNat] });
      }
      const e = calls[0], s = m.subnetOf(e.from);
      if (!s) return pass(h`${m.ref(e.from)} is not in a subnet of yours, so it reaches the internet directly, as a Lambda function outside a VPC does.`);
      if (s.type === "public-subnet") return pass(h`${m.ref(e.from)} is in a public subnet, so it reaches the internet through the internet gateway.`);
      const nat = m.ofKind("nat").find((id) => { const ns = m.subnetOf(id); return ns && ns.type === "public-subnet"; });
      return pass(h`${m.ref(e.from)} is private, and reaches the internet through ${m.ref(nat)} and the internet gateway, while nothing on the internet can start a connection to it.`);
    },
  },

  admission: {
    title: "Excess requests are turned away at the front",
    ask: "Every request passes something that refuses it when there are too many: API Gateway's throttling or a WAF rate-based rule. A load balancer never refuses one.",
    run(m) {
      const cs = clients(m);
      const code = serving(m).filter((id) => KINDS.CODE.has(m.kindOf(id)));
      if (!code.length) return wait(h`Waits for a request to reach your API.`);
      const around = reach(m, cs, { alive: (id) => !["gateway", "waf"].includes(m.kindOf(id)) });
      const bare = code.filter((id) => around.has(id));
      if (!bare.length) {
        const gate = [...reach(m, cs)].find((id) => ["gateway", "waf"].includes(m.kindOf(id)));
        return pass(h`Every request passes ${m.ref(gate)}, which answers **429** once the limit is reached, before any of it reaches ${refs(m, code)}.`);
      }
      const lb = [...around].find((id) => m.kindOf(id) === "lb");
      const via = lb ? h` ${m.ref(lb)} spreads requests but never refuses one.` : "";
      return fail(h`Requests reach ${m.ref(bare[0])} without passing a throttle.` + via + h` Put API Gateway (with its throttling) or AWS WAF (with a rate-based rule) on the way in.`, { nodes: bare });
    },
  },

  bulkhead: {
    title: "The slow third party cannot tie up the critical work",
    ask: "Saving and reading bookmarks runs on compute that never waits on the third party; the optional work runs apart from it.",
    run(m) {
      const exts = m.ofKind("external");
      const calls = intoExternal(m);
      if (!exts.length || !calls.length) return wait(h`Waits for something that calls the third party.`);
      const got = serving(m).filter((id) => KINDS.CODE.has(m.kindOf(id)));
      const touchesDb = got.filter((id) => dbs(m).some((d) => reach(m, [id], { alive: (x) => !KINDS.ASYNC.has(m.kindOf(x)) }).has(d)));
      if (!touchesDb.length) return wait(h`Waits for your API to reach a database.`);
      const waitsOnExt = (id) => exts.some((x) => syncReach(m, [id]).has(x));
      const clean = touchesDb.filter((id) => !waitsOnExt(id));
      if (clean.length) {
        const optional = got.filter(waitsOnExt);
        return pass(h`${refs(m, clean)} serve${clean.length === 1 ? "s" : ""} bookmarks and never wait${clean.length === 1 ? "s" : ""} on ${refs(m, exts)}` + (optional.length ? h`; ${refs(m, optional)} take${optional.length === 1 ? "s" : ""} the slow calls on ${optional.length === 1 ? "its" : "their"} own threads.` : "."));
      }
      const shared = touchesDb[0];
      const direct = calls.find((e) => e.from === shared);
      if (direct) return fail(h`${m.ref(shared)} serves bookmarks and also calls ${m.ref(direct.to)}: while that call hangs, its threads fill up and bookmark requests wait behind them. Run the optional work on its own compute.`, { nodes: [shared], edges: [direct.id] });
      const mid = syncReach(m, [shared]);
      const chain = calls.find((e) => mid.has(e.from));
      return fail(h`${m.ref(shared)} serves bookmarks and waits on ${m.ref(chain.from)}, which waits on ${m.ref(chain.to)}: the slow call still reaches the critical path. Call the optional service from separate compute, or put a queue between them.`, { nodes: [shared, chain.from], edges: [chain.id] });
    },
  },

  breaker: {
    title: "A circuit breaker stops calling the slow API",
    ask: "After enough failures in a row, calls to the third party stop for a while instead of each one waiting for its timeout.",
    run(m) {
      const calls = intoExternal(m);
      if (!calls.length) return wait(h`Waits for something that calls the third party.`);
      const bad = calls.filter((e) => !(e.guards || {}).breaker);
      if (!bad.length) {
        const noTimeout = calls.find((e) => !(e.guards || {}).timeout);
        return pass(h`${arrow(m, calls[0])} opens its breaker after repeated failures and fails fast until the service recovers.` + (noTimeout ? h` It only counts failures, though, and a call without a timeout never fails: see the deadline check.` : ""));
      }
      return fail(h`${arrow(m, bad[0])} has no circuit breaker, so when the third party is down every request still pays the full timeout. Select the arrow and turn on **Circuit breaker**.`, { edges: bad.map((e) => e.id) });
    },
  },

  fallback: {
    title: "When the breaker is open, there is a defined answer",
    ask: "A failed or skipped call to the third party returns a planned degraded response (no preview, a cached one) instead of an error.",
    run(m) {
      const calls = intoExternal(m);
      if (!calls.length) return wait(h`Waits for something that calls the third party.`);
      const bad = calls.filter((e) => !(e.guards || {}).fallback);
      if (!bad.length) return pass(h`When ${m.ref(calls[0].to)} fails, ${m.ref(calls[0].from)} answers with its fallback: the page shows no preview instead of an error.`);
      return fail(h`${arrow(m, bad[0])} has no fallback: when it fails, the member gets an error for something optional. Select the arrow and turn on **Fallback**.`, { edges: bad.map((e) => e.id) });
    },
  },
};

// An internet gateway is drawn on the edge of its VPC: accept one whose
// centre is inside the VPC box or within a hair of its border.
function nearVpc(m, id, vpc) {
  if (!vpc) return true;
  const n = m.nodes.get(id), pad = 44;
  return n.x >= vpc.x - pad && n.x <= vpc.x + vpc.w + pad && n.y >= vpc.y - pad && n.y <= vpc.y + vpc.h + pad;
}

// Run an exercise's checks. `spec` entries are ids or { id, title, ask }.
export function runChecks(model, specs) {
  return specs.map((s) => {
    const id = typeof s === "string" ? s : s.id;
    const c = CHECKS[id];
    if (!c) return { id, title: id, status: "wait", html: "Unknown check.", offenders: {} };
    let r;
    try { r = c.run(model); }
    catch (err) { r = { status: "wait", html: esc(`This check failed to run: ${err.message}`), offenders: {} }; }
    return { id, title: (s.title || c.title), ask: (s.ask || c.ask), ...r };
  });
}
