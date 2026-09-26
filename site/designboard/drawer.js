// Haiku draws on the board. The reader says what they mean in their own words
// ("users hit an ALB in front of two ECS services in two zones"), Haiku turns
// the words into a graph, and the board lays the graph out. Haiku never
// answers in words: the request forces one tool call, and nothing but that
// call's input is ever read.
//
// Three rules, each with a test in test/drawer.test.mjs:
//
//   * It never sees the exercise. The request is built from the parts
//     catalog, the board's own rules, the diagram and the reader's words, and
//     nothing else is passed in. If Haiku knew the question it would quietly
//     fix the reader's design, and the checks would be grading Haiku.
//   * It draws what the reader said, mistakes included. The checks are what
//     say "a queue cannot write to a database", not the drawer.
//   * The key is the reader's own Anthropic API key. It stays in their
//     browser and goes only to api.anthropic.com. A site may not use anyone's
//     claude.ai login or subscription on their behalf, and a claude.ai session
//     token is the key to their whole account: the field refuses one.
//
// The layout is the board's (layout.js), never the model's: Haiku owns what is
// connected to what, the code owns where things go.
import { layout } from "./layout.js";

// The one place the model is named. Haiku 4.5 is committed until at least
// 2026-10-15; after that this line changes and nothing else should have to.
// Forced tool use is refused by some models (Opus 5.5, Fable 5.1); callDrawer
// falls back to tool_choice "auto" with the same strict tool when that happens.
export const MODEL = "claude-haiku-4-5";
export const ENDPOINT = "https://api.anthropic.com/v1/messages";
export const API_VERSION = "2023-06-01";
export const KEY_NAME = "j2s-anthropic-key";
export const CONSOLE_URL = "https://platform.claude.com/settings/keys";

const MAX = { parts: 40, boxes: 20, arrows: 80, name: 40, label: 40, ask: 1000, earlier: 6, earlierLen: 300 };
export const GUARD_NAMES = ["timeout", "retries", "breaker", "fallback"];
// The kinds of box the model may draw, by the catalog's group ids.
export const BOX_KINDS = ["region", "vpc", "az", "public", "private", "asg", "cloud"];
const ID = /^[A-Za-z][A-Za-z0-9_-]{0,23}$/;

// ------------------------------------------------------------------ the key
// null when the key is fit to send, or a sentence saying why not. The known
// prefixes that are NOT API keys are refused by name, because each of them is
// something a person should never paste into a website.
export function keyProblem(raw) {
  const key = String(raw || "").trim();
  if (!key) return "Paste your Anthropic API key first.";
  if (/^sk-ant-sid/.test(key)) return "That is a claude.ai login session, not an API key. Never paste it into a website: it opens your whole account. Create an API key instead.";
  if (/^sk-ant-oat/.test(key)) return "That is a Claude subscription token, not an API key. Keep it out of websites, and create an API key instead.";
  if (/^sk-ant-admin/.test(key)) return "That is an admin key: it can manage your whole organization. Use an ordinary API key.";
  if (!/^sk-ant-/.test(key)) return "An Anthropic API key starts with sk-ant-. You can create one in the Anthropic Console.";
  if (/\s/.test(key)) return "That key has a space in it. Copy it again.";
  if (key.length < 40) return "That key looks cut short. Copy it again.";
  return null;
}

// Session storage unless the reader asks to be remembered on this device.
// Read at the moment of drawing, never kept in a variable between drawings.
export const keyStore = {
  get(s = globalThis.sessionStorage, l = globalThis.localStorage) {
    try { return (s && s.getItem(KEY_NAME)) || (l && l.getItem(KEY_NAME)) || ""; } catch { return ""; }
  },
  remembered(l = globalThis.localStorage) { try { return !!(l && l.getItem(KEY_NAME)); } catch { return false; } },
  set(key, remember, s = globalThis.sessionStorage, l = globalThis.localStorage) {
    const k = String(key).trim();
    try {
      if (remember) { l.setItem(KEY_NAME, k); s.removeItem(KEY_NAME); }
      else { s.setItem(KEY_NAME, k); l.removeItem(KEY_NAME); }
      return true;
    } catch { return false; }
  },
  forget(s = globalThis.sessionStorage, l = globalThis.localStorage) {
    try { s && s.removeItem(KEY_NAME); } catch { /* nothing to forget */ }
    try { l && l.removeItem(KEY_NAME); } catch { /* nothing to forget */ }
  },
};

// -------------------------------------------------------------- the request
// What the model knows: the board's rules and the parts it may use. Nothing
// here comes from an exercise; it is built from the catalog alone, so a part
// added to the catalog is one Haiku can draw.
export function systemPrompt(catalog) {
  const parts = catalog.parts.map((p) => `${p.id}: ${p.label}${p.short && p.short !== p.label ? ` (${p.short})` : ""}${p.aliases ? `; ${p.aliases}` : ""}`).join("\n");
  return `You draw cloud architecture diagrams on a design board that engineers use to practise system design. A reader describes a design in their own words and you turn it into a diagram by calling the draw tool. You never answer in words: the draw tool is your only output, and the reader never sees any text from you.

# How the board works
- A diagram is parts (AWS services, plus users, clients and outside services), boxes (region, VPC, Availability Zone, public subnet, private subnet, Auto Scaling group, AWS Cloud) and arrows between parts.
- An arrow from A to B means A sends a request or a message to B. The answer travels back along the same arrow, so never draw an arrow for a reply or a response.
- An arrow starts at the side that asks: a browser calls an API; code reads and writes its database (service -> database); code looks things up in a cache (service -> cache); code puts a job on a queue (service -> queue); a queue hands each message to whatever takes it (queue -> worker); a topic delivers to its subscribers (SNS -> SQS); a load balancer forwards to its targets (ALB -> service); CloudFront fetches from its origin (CloudFront -> S3); DNS points at an entry point (Route 53 -> CloudFront); a bucket or a table can send change events (S3 -> Lambda, DynamoDB -> Lambda); private servers reach the internet through a NAT gateway and then an internet gateway (service -> NAT gateway -> internet gateway -> outside service).
- A part runs inside the box you put it in. Containers and instances (ECS, EC2, EKS) run in one Availability Zone. Managed services (Lambda, SQS, SNS, DynamoDB, S3, API Gateway, load balancers) are regional. RDS, Aurora and ElastiCache run in one zone unless the reader says Multi-AZ: then set multiAz to true.
- Boxes nest the way AWS nests them: region, then VPC, then Availability Zone, then public or private subnet. An Auto Scaling group sits in a subnet or a zone. A load balancer or an internet gateway that serves several zones sits in the VPC itself, in no zone. A NAT gateway sits in a public subnet.

# What to draw
- Draw exactly what the reader describes, including anything that looks like a mistake. Do not fix, improve or complete their design: they are practising, and a quiet correction would hide what they need to learn. If they say the queue writes to the database, draw that arrow. If they leave something out, leave it out.
- Add nothing they did not ask for, with two exceptions: when they describe requests arriving and no client is drawn, add Users as the requester; and when they put parts in zones or subnets, add the boxes those parts need to sit in (a zone sits in a VPC, a subnet in a zone).
- Never add an AWS Cloud, region or VPC box the reader did not mention, except a VPC their zones or subnets need. A box you draw holds what the reader put in it; never draw an empty box they did not ask for.
- One part per thing they describe. "Two services in two zones" is two parts, one in each zone. "An API behind a load balancer" is one API.
- Give a part a name only when the reader gives it one ("the bookmarks API", "a worker called fetcher"). Otherwise leave name out: the board shows AWS's name under the icon.
- An arrow gets a label only when the reader says what it carries, in a few words. Guards on an arrow (timeout, retries, breaker, fallback) only when the reader says that call has one.
- Name Availability Zones us-east-1a, us-east-1b and so on unless the reader names them.
- Pick the part that matches the reader's words: Postgres or MySQL is rds (aurora if they say Aurora); Redis or Memcached is elasticache; Kafka is msk; a server or a VM is ec2; containers are ecs (eks for Kubernetes, fargate if they say Fargate); a function is lambda; a website or an API outside AWS is website or thirdparty.

# Changing a diagram
- The message shows the diagram on the board now. It may hold parts the reader drew by hand. Their ids are the handles for changing it.
- When the reader adds, removes or corrects something, call draw with the whole diagram as it should be after the change. Keep every id, name, box and arrow the change does not touch.
- "I meant a cache, not a database": change that part's part to a cache and keep its id, its box and its arrows.
- When a part is removed, remove its arrows too. When the reader asks to start over, draw only what they describe next.

# Parts you can use (id: AWS name; words readers use for it)
${parts}

# Boxes you can use (kind)
region: an AWS Region. vpc: a virtual private cloud. az: an Availability Zone. public: a public subnet. private: a private subnet. asg: an Auto Scaling group. cloud: the AWS Cloud boundary.`;
}

// The tool is the whole diagram, every time: an edit is the diagram after the
// edit. Strict, so its input always matches this schema.
export function drawTool(catalog) {
  return {
    name: "draw",
    description: "Draw the whole diagram as it should look on the board now. This is the only way to answer: the board replaces what is drawn with exactly what you pass here. boxes are containers (a VPC, its Availability Zones, their subnets), each optionally inside another box by id. parts are AWS services and outside things, each optionally inside a box by id. arrows go from the part that sends a request or a message to the part that receives it. Keep the ids of everything that stays; give new things short new ids.",
    strict: true,
    input_schema: {
      type: "object",
      properties: {
        boxes: {
          type: "array",
          description: "Region, VPC, Availability Zone, subnet, Auto Scaling group and AWS Cloud boxes.",
          items: {
            type: "object",
            properties: {
              id: { type: "string", description: "Short id, unique across boxes and parts." },
              kind: { type: "string", enum: BOX_KINDS },
              name: { type: "string", description: "Only a name the reader gave it, or an Availability Zone's name such as us-east-1a." },
              inside: { type: "string", description: "Id of the box this box sits in. Leave out at the top level." },
            },
            required: ["id", "kind"],
            additionalProperties: false,
          },
        },
        parts: {
          type: "array",
          items: {
            type: "object",
            properties: {
              id: { type: "string", description: "Short id, unique across boxes and parts." },
              part: { type: "string", enum: catalog.parts.map((p) => p.id) },
              name: { type: "string", description: "Only a name the reader gave it." },
              inside: { type: "string", description: "Id of the box this part runs in. Leave out if it sits in no box." },
              multiAz: { type: "boolean", description: "True only for RDS, Aurora or ElastiCache the reader calls Multi-AZ." },
            },
            required: ["id", "part"],
            additionalProperties: false,
          },
        },
        arrows: {
          type: "array",
          items: {
            type: "object",
            properties: {
              from: { type: "string", description: "Id of the part that sends the request or message." },
              to: { type: "string", description: "Id of the part that receives it." },
              label: { type: "string", description: "What it carries, in a few words, only if the reader said." },
              guards: { type: "array", items: { type: "string", enum: GUARD_NAMES }, description: "Only guards the reader put on this call." },
            },
            required: ["from", "to"],
            additionalProperties: false,
          },
        },
      },
      required: ["boxes", "parts", "arrows"],
      additionalProperties: false,
    },
  };
}

// Everything that goes to Anthropic, and all of it is built from these four
// arguments: nothing on the page reaches it any other way.
export function buildRequest({ catalog, diagram, earlier = [], ask, forced = true }) {
  const empty = !diagram || (!diagram.parts.length && !diagram.boxes.length);
  const asked = earlier.filter((s) => typeof s === "string" && s.trim()).slice(-MAX.earlier).map((s) => clip(s.trim(), MAX.earlierLen));
  const lines = [
    empty ? "The board is empty." : `The diagram on the board now:\n<diagram>\n${JSON.stringify(diagram)}\n</diagram>`,
    asked.length ? `What the reader asked for before, oldest first:\n${asked.map((s) => `- ${s}`).join("\n")}` : "",
    `What the reader asks now:\n<ask>\n${clip(String(ask || "").trim(), MAX.ask)}\n</ask>`,
  ].filter(Boolean);
  return {
    model: MODEL,
    max_tokens: 4096,
    temperature: 0,
    system: [{ type: "text", text: systemPrompt(catalog), cache_control: { type: "ephemeral" } }],
    tools: [drawTool(catalog)],
    tool_choice: forced ? { type: "tool", name: "draw" } : { type: "auto" },
    messages: [{ role: "user", content: lines.join("\n\n") }],
  };
}
const clip = (s, n) => (s.length > n ? s.slice(0, n) : s);

// ------------------------------------------------------------------ calling
// One drawing. Resolves to { input, usage } or { error } where error is one of
// the kinds below; the words the reader sees are the board's, never the API's
// and never the model's.
export const ERRORS = {
  network: "Could not reach Anthropic. Check your connection and try again.",
  timeout: "Haiku took too long to answer. Try again.",
  key: "Anthropic did not accept that key, so it has been forgotten. Paste it again.",
  forbidden: "That key is not allowed to use Haiku.",
  credit: "Anthropic says the account behind this key has no credit left.",
  model: "Haiku is not available to this key.",
  busy: "Anthropic is busy right now. Try again in a moment.",
  rate: "Too many drawings at once. Wait a moment and try again.",
  big: "That is more than the board can draw at once. Try it in smaller steps.",
  refused: "Anthropic refused the request.",
  nothing: "Nothing came back to draw. Try saying it another way.",
  stopped: "Stopped.",
};

export async function callDrawer({ key, request, fetchImpl = globalThis.fetch, signal }) {
  let req = request, fellBack = false;
  for (;;) {
    let res;
    try {
      res = await fetchImpl(ENDPOINT, {
        method: "POST",
        headers: {
          "x-api-key": key,
          "anthropic-version": API_VERSION,
          "content-type": "application/json",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify(req),
        credentials: "omit", referrerPolicy: "no-referrer", cache: "no-store", mode: "cors",
        signal,
      });
    } catch (e) {
      // An abort with a reason rejects with the reason itself, not an
      // AbortError (seen in Chromium: Stop reported "Could not reach
      // Anthropic"), so ask the signal, not the error.
      if (signal && signal.aborted) return { error: signal.reason === "timeout" ? "timeout" : "stopped" };
      if (e && e.name === "TimeoutError") return { error: "timeout" };
      return { error: "network" };
    }
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    if (res.ok) {
      const use = body && Array.isArray(body.content) ? body.content.find((b) => b && b.type === "tool_use" && b.name === "draw") : null;
      if (body && body.stop_reason === "max_tokens") return { error: "big", usage: body.usage };
      if (!use || !use.input || typeof use.input !== "object") return { error: "nothing", usage: body && body.usage };
      return { input: use.input, usage: body.usage || null, fellBack };
    }
    const type = body && body.error && body.error.type, msg = String((body && body.error && body.error.message) || "");
    // A model that refuses forced tool use: ask once more with "auto". The
    // tool is strict either way, and only its input is ever read.
    if (res.status === 400 && !fellBack && req.tool_choice && req.tool_choice.type === "tool" && /tool_choice|forced tool/i.test(msg)) {
      req = { ...req, tool_choice: { type: "auto" } }; fellBack = true; continue;
    }
    if (res.status === 401) return { error: "key" };
    if (res.status === 403) return { error: "forbidden" };
    if (res.status === 404) return { error: "model" };
    if (res.status === 413) return { error: "big" };
    if (res.status === 429) return { error: "rate" };
    if (res.status === 529 || res.status >= 500 || type === "overloaded_error") return { error: "busy" };
    if (/credit balance/i.test(msg)) return { error: "credit" };
    return { error: "refused" };
  }
}

// --------------------------------------------------------------- validation
// What came back, made safe to draw: unknown parts and kinds dropped, arrows to
// nothing dropped, ids made unique and plain. It never throws; the worst a bad
// answer can do is draw less.
export function validateDrawing(input, index, { keepCloud = false } = {}) {
  const src = input && typeof input === "object" ? input : {};
  const taken = new Set(), rename = new Map();
  const str = (v, n) => (typeof v === "string" ? clip(v.replace(/\s+/g, " ").trim(), n) : "");
  let fresh = 0;
  const idFor = (raw, prefix) => {
    const want = typeof raw === "string" ? raw.trim() : "";
    if (want && ID.test(want) && !taken.has(want)) { taken.add(want); return want; }
    let id;
    do id = `${prefix}${++fresh}`; while (taken.has(id));
    taken.add(id);
    return id;
  };
  const boxes = [];
  for (const b of Array.isArray(src.boxes) ? src.boxes.slice(0, MAX.boxes) : []) {
    if (!b || typeof b !== "object" || !BOX_KINDS.includes(b.kind) || !index.groups.has(b.kind)) continue;
    if (typeof b.id === "string" && rename.has(b.id)) continue;           // a second box claiming an id already used
    const id = idFor(b.id, "g");
    if (typeof b.id === "string") rename.set(b.id, id);
    boxes.push({ id, kind: b.kind, name: str(b.name, MAX.name), inside: typeof b.inside === "string" ? b.inside : "" });
  }
  const parts = [];
  for (const p of Array.isArray(src.parts) ? src.parts.slice(0, MAX.parts) : []) {
    if (!p || typeof p !== "object" || typeof p.part !== "string" || !index.parts.has(p.part)) continue;
    if (typeof p.id === "string" && rename.has(p.id)) continue;
    const id = idFor(p.id, "n");
    if (typeof p.id === "string") rename.set(p.id, id);
    const def = index.parts.get(p.part);
    const out = { id, part: p.part, name: str(p.name, MAX.name), inside: typeof p.inside === "string" ? p.inside : "" };
    if (def.placement === "multiaz" && typeof p.multiAz === "boolean") out.multiAz = p.multiAz;
    parts.push(out);
  }
  // Containers resolve to boxes that exist, never to a part and never in a loop.
  const boxIds = new Set(boxes.map((b) => b.id));
  for (const x of [...boxes, ...parts]) { const to = rename.get(x.inside); x.inside = to && boxIds.has(to) && to !== x.id ? to : ""; }
  for (const b of boxes) {
    const seen = new Set([b.id]);
    for (let at = b.inside; at; at = (boxes.find((o) => o.id === at) || {}).inside) {
      if (seen.has(at)) { b.inside = ""; break; }
      seen.add(at);
    }
  }
  // A name that only repeats AWS's name says nothing, and the board would
  // print it twice.
  for (const p of parts) { const d = index.parts.get(p.part); if (same(p.name, d.short) || same(p.name, d.label) || same(p.name, p.part)) p.name = ""; }
  for (const b of boxes) { const d = index.groups.get(b.kind); if (b.kind !== "az" && b.kind !== "region" && (same(b.name, d.short) || same(b.name, d.label) || same(b.name, b.kind))) b.name = ""; }
  // Haiku draws an AWS Cloud box around its answers whatever the prompt says
  // (in 7 of 11 early drawings, after being told not to in 4 of them), and it
  // was the box that made drawings wrong: empty beside the parts, or holding
  // some parts and not the ones an edit added. So unless the board already had
  // one or the reader asked for one, it is unwrapped here: what was in it
  // moves up a level. Empty, it goes in any case.
  for (let i = boxes.length - 1; i >= 0; i--) {
    const b = boxes[i];
    if (b.kind !== "cloud") continue;
    const holds = [...boxes, ...parts].filter((x) => x.inside === b.id);
    if (keepCloud && holds.length) continue;
    for (const x of holds) x.inside = b.inside;
    boxes.splice(i, 1);
  }
  // Zones get names, as they have on the board; a region, its one.
  const zoneNames = new Set(boxes.filter((b) => b.kind === "az" && b.name).map((b) => b.name));
  let letter = 0;
  for (const b of boxes) if (b.kind === "az" && !b.name) {
    let n;
    do n = `us-east-1${"abcdefghijklmnopqrstuvwxyz"[letter++] || "z"}`; while (zoneNames.has(n) && letter < 26);
    b.name = n; zoneNames.add(n);
  }
  for (const b of boxes) if (b.kind === "region" && !b.name) b.name = "us-east-1";

  const partIds = new Set(parts.map((p) => p.id));
  const arrows = [], pairs = new Set();
  for (const a of Array.isArray(src.arrows) ? src.arrows.slice(0, MAX.arrows) : []) {
    if (!a || typeof a !== "object") continue;
    const from = rename.get(a.from), to = rename.get(a.to);
    if (!from || !to || from === to || !partIds.has(from) || !partIds.has(to)) continue;
    if (pairs.has(from + "\u0000" + to)) continue;
    pairs.add(from + "\u0000" + to);
    const guards = Array.isArray(a.guards) ? [...new Set(a.guards.filter((g) => GUARD_NAMES.includes(g)))] : [];
    arrows.push({ from, to, label: str(a.label, MAX.label), guards });
  }
  return { boxes, parts, arrows };
}
const same = (a, b) => !!a && !!b && a.trim().toLowerCase() === String(b).trim().toLowerCase();
// Keep an AWS Cloud box only if the board has one or the reader asked for one
// ("cloud" as a word: CloudFront and CloudWatch are not it).
export const wantsCloud = (state, asked) => (state.groups || []).some((g) => g.part === "cloud") || asked.some((s) => /\bcloud\b/i.test(s));

// ------------------------------------------------- the board, as the model sees it
const within = (g, x, y) => x >= g.x && x <= g.x + g.w && y >= g.y && y <= g.y + g.h;
const area = (g) => g.w * g.h;

// The diagram on the board as the drawing tool's own shape: which box holds
// what is read from where things are drawn, by the rule the checks use (the
// smallest box that holds a part's centre).
export function diagramFromState(state, index) {
  const groups = (state.groups || []).filter((g) => index.groups.has(g.part));
  const nodes = (state.nodes || []).filter((n) => index.parts.has(n.part));
  const holderOfBox = (g) => groups.filter((o) => o !== g && area(o) > area(g) && within(o, g.x, g.y) && within(o, g.x + g.w, g.y + g.h)).sort((a, b) => area(a) - area(b))[0];
  const holderOfPart = (n) => groups.filter((o) => within(o, n.x, n.y)).sort((a, b) => area(a) - area(b))[0];
  const boxes = groups.map((g) => {
    const out = { id: g.id, kind: g.part };
    if ((g.name || "").trim()) out.name = g.name.trim();
    const h = holderOfBox(g);
    if (h) out.inside = h.id;
    return out;
  });
  const parts = nodes.map((n) => {
    const out = { id: n.id, part: n.part };
    if ((n.name || "").trim()) out.name = n.name.trim();
    const h = holderOfPart(n);
    if (h) out.inside = h.id;
    const def = index.parts.get(n.part);
    if (def.placement === "multiaz" && (n.multiAz != null ? n.multiAz : def.multiAzDefault)) out.multiAz = true;
    return out;
  });
  const ids = new Set(nodes.map((n) => n.id));
  const arrows = (state.edges || []).filter((e) => ids.has(e.from) && ids.has(e.to) && e.from !== e.to).map((e) => {
    const out = { from: e.from, to: e.to };
    if ((e.label || "").trim()) out.label = e.label.trim();
    const guards = GUARD_NAMES.filter((g) => (e.guards || {})[g]);
    if (guards.length) out.guards = guards;
    return out;
  });
  return { boxes, parts, arrows };
}

// ----------------------------------------------------- the drawing, as board state
// The graph layout.js reads, from a diagram in the tool's shape.
export function toLayoutGraph(d, index) {
  return {
    parts: d.parts.map((p) => ({ id: p.id, part: p.part, inside: p.inside || undefined })),
    boxes: d.boxes.map((b) => ({ id: b.id, type: index.groups.get(b.kind).type, name: b.name || "", inside: b.inside || undefined })),
    arrows: d.arrows.map((a) => ({ from: a.from, to: a.to, text: edgeText(a) })),
  };
}
// An arrow's chip, exactly as the board prints it: what it carries, then its guards.
const GUARD_SHORT = { timeout: "timeout", retries: "retries", breaker: "breaker", fallback: "fallback" };
export function edgeText(a) {
  const guards = GUARD_NAMES.filter((g) => (a.guards || []).includes(g)).map((g) => GUARD_SHORT[g]);
  return [a.label || "", guards.join(" · ")].filter(Boolean).join("  ·  ");
}

// The two lines under a part's icon, exactly as the board prints them.
export function partLabels(def, name) {
  const n = (name || "").trim();
  return { top: n || def.short, sub: n ? def.short : def.short !== def.label && def.label.length < 28 ? def.label : "" };
}
export function boxLabel(def, name) {
  const n = (name || "").trim();
  const main = n || def.short || def.label;
  const kind = n && n !== (def.short || def.label) && def.type !== "az" && def.type !== "region" ? ` · ${def.short || def.label}` : "";
  return main + kind;
}

// Where everything goes. `measure(text, "name"|"part"|"box")` is the width the
// board will draw that text at; in the browser it is measured, in tests estimated.
export function placeDrawing(d, index, measure) {
  const byId = new Map(d.parts.map((p) => [p.id, p]));
  const boxById = new Map(d.boxes.map((b) => [b.id, b]));
  const graph = toLayoutGraph(d, index);
  const kindOf = (id) => { const p = byId.get(id); return p ? index.parts.get(p.part).kind : ""; };
  const labelWidth = (id) => {
    const p = byId.get(id), def = index.parts.get(p.part), { top, sub } = partLabels(def, p.name);
    return Math.max(measure(top, "name"), sub ? measure(sub, "part") : 0);
  };
  const boxWidth = (id) => { const b = boxById.get(id), def = index.groups.get(b.kind); return (def.icon ? 30 : 8) + measure(boxLabel(def, b.name), "box") + 12; };
  return layout(graph, { kindOf, measure: labelWidth, measureBox: boxWidth, measureEdge: (t) => measure(t, "edge") });
}

// Same boxes in the same places in the tree, same parts in the same boxes:
// what changed is kinds, names or arrows, and the reader's arrangement can stay.
function sameShape(a, b) {
  const key = (d) => JSON.stringify([
    d.boxes.map((x) => [x.id, x.kind, x.inside || ""]).sort(),
    d.parts.map((x) => [x.id, x.inside || ""]).sort(),
  ]);
  return key(a) === key(b);
}

// The board's new state for a drawing. Positions come from the layout, except
// when the reader has arranged things by hand and the drawing only changes
// kinds, names or arrows: then everything stays where they put it.
export function drawingToState(drawing, { index, current, measure }) {
  const cur = current || { nodes: [], groups: [], edges: [] };
  const before = diagramFromState(cur, index);
  let pos = null;
  if (sameShape(before, drawing) && handArranged(cur, before, index, measure)) {
    pos = { nodes: {}, boxes: {} };
    for (const n of cur.nodes) pos.nodes[n.id] = { x: n.x, y: n.y };
    for (const g of cur.groups) pos.boxes[g.id] = { x: g.x, y: g.y, w: g.w, h: g.h };
  }
  const placed = pos || placeDrawing(drawing, index, measure);
  const edgeIds = new Map(cur.edges.map((e) => [e.from + "\u0000" + e.to, e.id]));
  const used = new Set([...drawing.parts.map((p) => p.id), ...drawing.boxes.map((b) => b.id)]);
  let k = 0;
  const edgeId = (from, to) => {
    const old = edgeIds.get(from + "\u0000" + to);
    if (old && !used.has(old)) { used.add(old); return old; }
    let id;
    do id = `e${++k}`; while (used.has(id));
    used.add(id);
    return id;
  };
  return {
    nodes: drawing.parts.map((p) => {
      const at = placed.nodes[p.id];
      const n = { id: p.id, part: p.part, name: p.name || "", x: at.x, y: at.y };
      if (p.multiAz != null) n.multiAz = p.multiAz;
      return n;
    }),
    groups: drawing.boxes.map((b) => ({ id: b.id, part: b.kind, name: b.name || "", ...placed.boxes[b.id] })),
    edges: drawing.arrows.map((a) => ({ id: edgeId(a.from, a.to), from: a.from, to: a.to, label: a.label || "", guards: Object.fromEntries(a.guards.map((g) => [g, true])) })),
    fits: placed.fits !== false,
    ...(pos ? (cur.canvas ? { canvas: cur.canvas } : {}) : placed.canvas ? { canvas: placed.canvas } : {}),
  };
}

// Has the reader moved anything since the board last laid this diagram out?
// The layout is a pure function of the diagram, so "not moved" is "where the
// layout would put it now". No flag to keep in sync.
function handArranged(cur, before, index, measure) {
  if (!cur.nodes.length && !cur.groups.length) return false;
  const valid = validateDrawing(before, index, { keepCloud: true });
  const p = placeDrawing(valid, index, measure);
  const off = (a, b) => !b || Math.abs(a - b) > 1;
  for (const n of cur.nodes) { const q = p.nodes[n.id]; if (!q || off(n.x, q.x) || off(n.y, q.y)) return true; }
  for (const g of cur.groups) { const q = p.boxes[g.id]; if (!q || off(g.x, q.x) || off(g.y, q.y) || off(g.w, q.w) || off(g.h, q.h)) return true; }
  return false;
}
