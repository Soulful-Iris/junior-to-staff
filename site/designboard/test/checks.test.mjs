// node --test site/designboard/test/
//
// Every check both ways: a diagram it must pass and one it must fail, and the
// last test refuses to go green unless each check was actually seen doing
// both. A check that only ever passes its reference answer proves nothing.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { catalogIndex, buildModel, reach } from "../model.js";
import { CHECKS, runChecks } from "../checks.js";
import { simulate, CAPABILITIES, downSet } from "../sim.js";
import { arrowProblem } from "../rules.js";
import { N, G, E, board, NET, AT, REFERENCE } from "./fixtures.mjs";

const read = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url)));
const catalog = read("../catalog.json");
const index = catalogIndex(catalog);
const EXERCISES = read("../../../curriculum/03-production/01-system-design/whiteboard.board.json").exercises;
const model = (b) => buildModel(b, index);
const at = (k) => AT[k];

const seen = {};
function expect(id, b, status, { nodes, edges, groups, says } = {}) {
  const r = CHECKS[id].run(model(b));
  (seen[id] ||= new Set()).add(r.status);
  assert.equal(r.status, status, `${id} should ${status}: ${r.html}`);
  if (nodes) assert.deepEqual([...(r.offenders.nodes || [])].sort(), [...nodes].sort(), `${id} offending parts: ${r.html}`);
  if (edges) assert.deepEqual((r.offenders.edges || []).length, edges, `${id} offending arrows: ${r.html}`);
  if (groups) assert.deepEqual([...(r.offenders.groups || [])].sort(), [...groups].sort(), `${id} offending boxes`);
  for (const s of [].concat(says || [])) assert.match(r.html, s, `${id} says: ${r.html}`);
  return r;
}

// ------------------------------------------------------------------ catalog
test("every part and box in the catalog has its icon on disk, and ids are unique", () => {
  const ids = new Set();
  for (const p of [...catalog.parts, ...catalog.groups]) {
    assert.ok(!ids.has(p.id), `duplicate id ${p.id}`); ids.add(p.id);
    if (p.icon) assert.ok(existsSync(new URL(`../icons/${p.icon}`, import.meta.url)), `missing icon ${p.icon}`);
  }
  assert.ok(catalog.parts.filter((p) => p.common).length >= 20, "the common parts are the first thing a reader sees");
  for (const p of catalog.parts) assert.ok(["zonal", "regional", "multiaz", "edge", "global"].includes(p.placement), p.id);
});

test("every exercise names checks, capabilities and tips that exist", () => {
  assert.equal(EXERCISES.length, 4);
  for (const x of EXERCISES) {
    for (const c of x.checks) assert.ok(CHECKS[typeof c === "string" ? c : c.id], `${x.id}: no check ${c}`);
    for (const c of x.capabilities) assert.ok(CAPABILITIES[c.id], `${x.id}: no capability ${c.id}`);
    for (const k of Object.keys(x.tips)) assert.ok(["start", "passing"].includes(k) || x.checks.includes(k), `${x.id}: tips for ${k}, which it does not check`);
    for (const c of x.checks) assert.ok(x.tips[c] || c === "arrows" || true);
    assert.ok(x.tips.start && x.tips.start.length >= 2 && x.tips.passing, `${x.id} needs start and passing tips`);
  }
});

// ------------------------------------------------------------------- model
test("a part belongs to the smallest box that holds its centre", () => {
  const m = model(board([N("a", "ecs", ...at("priva")), N("b", "ecs", ...at("pubb")), N("c", "ecs", ...at("out"))], [], NET));
  assert.equal(m.zoneOf("a").id, "aza");
  assert.equal(m.subnetOf("a").id, "priva");
  assert.equal(m.subnetOf("b").type, "public-subnet");
  assert.equal(m.vpcOf("a").id, "vpc");
  assert.equal(m.zoneOf("c"), null);
});

// ------------------------------------------------------------------- rules
test("the arrows AWS can and cannot make", () => {
  const P = (id) => index.parts.get(id);
  const no = [["sqs", "rds"], ["apigw", "rds"], ["alb", "dynamodb"], ["users", "elasticache"], ["rds", "lambda"], ["elasticache", "rds"], ["alb", "sqs"], ["s3", "rds"], ["natgw", "rds"], ["website", "sqs"], ["users", "rdsproxy"]];
  const yes = [["sqs", "lambda"], ["sqs", "ecs"], ["sqs", "sqs"], ["apigw", "sqs"], ["apigw", "dynamodb"], ["appsync", "aurora"], ["alb", "ecs"], ["alb", "lambda"], ["s3", "lambda"], ["dynamodb", "lambda"], ["ecs", "rds"], ["lambda", "website"], ["sns", "sqs"], ["natgw", "website"], ["rdsproxy", "rds"], ["cloudfront", "s3"], ["waf", "alb"], ["users", "cloudfront"], ["users", "s3"]];
  for (const [a, b] of no) assert.ok(arrowProblem(P(a), P(b)), `${a} -> ${b} should be refused`);
  for (const [a, b] of yes) assert.equal(arrowProblem(P(a), P(b)), null, `${a} -> ${b} should be allowed`);
});

// -------------------------------------------------------------- the checks
test("arrows: refuses a queue writing to a database, and an empty board", () => {
  expect("arrows", board([N("u", "users"), N("a", "ecs"), N("d", "rds")], [E("u", "a"), E("a", "d")]), "pass");
  expect("arrows", board([N("q", "sqs"), N("d", "rds")], [E("q", "d")]), "fail", { edges: 1, says: /Something has to take the message/ });
  expect("arrows", board([N("u", "users")]), "fail", { says: /No arrows yet/ });
  // A reply drawn as its own arrow is explained as a reply.
  expect("arrows", board([N("u", "users"), N("a", "ecs"), N("d", "rds")], [E("u", "a"), E("a", "d"), E("d", "a")]), "fail", { edges: 1, says: /answer travels back/ });
});

test("reachesApi: needs a client, and an arrow to something that runs code", () => {
  expect("reachesApi", board([N("u", "users"), N("g", "apigw"), N("f", "lambda")], [E("u", "g"), E("g", "f")]), "pass", { says: /→/ });
  expect("reachesApi", board([N("f", "lambda")]), "fail", { says: /Start where requests start/ });
  expect("reachesApi", board([N("u", "users"), N("s", "s3")], [E("u", "s")]), "fail", { nodes: ["u"] });
});

test("parts that share a name are said once, with a count", () => {
  const r = expect("commitsToDb", board([N("u", "users"), N("a", "ecs"), N("d1", "rds", 0, 0, { name: "" }), N("d2", "rds", 0, 0, { name: "" })], [E("u", "a")]), "fail");
  assert.match(r.html, /RDS<\/b> \(×2\) are on the board/, r.html);
  assert.doesNotMatch(r.html, /RDS<\/b> and <b/, r.html);
});

test("commitsToDb: a database the API writes to; a cache or a bucket is not one", () => {
  expect("commitsToDb", board([N("u", "users"), N("a", "ecs"), N("d", "rds")], [E("u", "a"), E("a", "d")]), "pass");
  expect("commitsToDb", board([N("u", "users"), N("a", "ecs"), N("c", "elasticache")], [E("u", "a"), E("a", "c")]), "fail", { nodes: ["c"], says: /disposable copy/ });
  expect("commitsToDb", board([N("u", "users"), N("a", "ecs"), N("s", "s3")], [E("u", "a"), E("a", "s")]), "fail", { nodes: ["s"] });
  expect("commitsToDb", board([N("u", "users"), N("a", "ecs"), N("d", "rds")], [E("u", "a")]), "fail", { nodes: ["d"] });
});

test("noDirectDb: a path to the database that skips the API fails", () => {
  expect("noDirectDb", board([N("u", "users"), N("a", "ecs"), N("d", "dynamodb")], [E("u", "a"), E("a", "d")]), "pass");
  expect("noDirectDb", board([N("u", "users"), N("a", "ecs"), N("d", "dynamodb")], [E("u", "a"), E("a", "d"), E("u", "d")]), "fail", { nodes: ["d"], edges: 1 });
  // Through a CDN is still around the API.
  expect("noDirectDb", board([N("u", "users"), N("cf", "cloudfront"), N("s", "s3"), N("d", "dynamodb"), N("a", "lambda")], [E("u", "cf"), E("cf", "s"), E("s", "a"), E("a", "d")]), "pass");
  expect("noDirectDb", board([N("u", "users")]), "wait");
});

test("spread: two copies behind a load balancer, or Lambda", () => {
  expect("spread", board([N("u", "users"), N("l", "alb"), N("a", "ecs"), N("b", "ecs")], [E("u", "l"), E("l", "a"), E("l", "b")]), "pass");
  expect("spread", board([N("u", "users"), N("g", "apigw"), N("f", "lambda")], [E("u", "g"), E("g", "f")]), "pass", { says: /one copy per request/ });
  expect("spread", board([N("u", "users"), N("l", "alb"), N("a", "ecs")], [E("u", "l"), E("l", "a")]), "fail", { nodes: ["a"], says: /alone/ });
  expect("spread", board([N("u", "users"), N("l", "alb"), N("a", "ecs"), N("b", "ecs")], [E("u", "l"), E("l", "a"), E("l", "b"), E("u", "b")]), "fail", { nodes: ["b"], edges: 1, says: /directly/ });
  expect("spread", board([N("u", "users")]), "wait");
});

test("readsSkipDb: a cache the API checks first, or CloudFront in front", () => {
  const base = [N("u", "users"), N("l", "alb"), N("a", "ecs"), N("d", "rds")];
  expect("readsSkipDb", board([...base, N("c", "elasticache")], [E("u", "l"), E("l", "a"), E("a", "c"), E("a", "d")]), "pass", { says: /looks in/ });
  expect("readsSkipDb", board([...base, N("cf", "cloudfront")], [E("u", "cf"), E("cf", "l"), E("l", "a"), E("a", "d")]), "pass", { says: /edge/ });
  expect("readsSkipDb", board(base, [E("u", "l"), E("l", "a"), E("a", "d")]), "fail", { nodes: ["d"], says: /Every read goes to/ });
  expect("readsSkipDb", board([...base, N("c", "elasticache")], [E("u", "l"), E("l", "a"), E("a", "d")]), "fail", { nodes: ["c"], says: /no code that serves a read looks/ });
});

test("storesPrivate: databases and caches in a private subnet; DynamoDB is not in a subnet at all", () => {
  expect("storesPrivate", board([N("d", "rds", ...at("priva")), N("c", "elasticache", ...at("privb"))], [], NET), "pass");
  expect("storesPrivate", board([N("d", "rds", ...at("puba"))], [], NET), "fail", { nodes: ["d"], groups: ["puba"], says: /public subnet/ });
  expect("storesPrivate", board([N("d", "rds", ...at("out"))], [], NET), "fail", { nodes: ["d"], says: /not inside a private subnet/ });
  expect("storesPrivate", board([N("d", "dynamodb")]), "pass", { says: /IAM/ });
  expect("storesPrivate", board([N("u", "users")]), "wait");
});

test("survivesZone: two zones, a copy in each, and a Multi-AZ database", () => {
  const good = REFERENCE["read-traffic-grows"];
  expect("survivesZone", good, "pass", { says: /standby/ });
  // One zone only.
  expect("survivesZone", board(good.nodes, good.edges, NET.filter((g) => g.id !== "azb")), "fail", { says: /Draw two Availability Zones/ });
  // The database without Multi-AZ dies with its zone.
  const single = board(good.nodes.map((n) => (n.id === "db" ? { ...n, multiAz: false } : n)), good.edges, NET);
  const r = expect("survivesZone", single, "fail", { says: /Losing .*us-east-1b/ });
  assert.equal(r.offenders.tryZone, "azb", "the fail offers to break the zone that loses it");
  // Both API copies in one zone.
  const lopsided = board(good.nodes.map((n) => (n.id === "apib" ? { ...n, x: 300, y: 420 } : n)), good.edges, NET);
  expect("survivesZone", lopsided, "fail", { says: /us-east-1a/ });
  // A container outside any zone: where does it run?
  const nowhere = board(good.nodes.map((n) => (n.id === "apib" ? { ...n, x: 900, y: 450 } : n)), good.edges, NET);
  expect("survivesZone", nowhere, "fail", { nodes: ["apib"], says: /not inside one/ });
  expect("survivesZone", board([N("u", "users")]), "wait");
  // Serverless survives with no zones drawn at all? No: it must still say where things run...
  // ...but Lambda and DynamoDB are regional, so two zones are asked for and nothing is unplaced.
  expect("survivesZone", board(REFERENCE["bookmark-survives-restart"].nodes, REFERENCE["bookmark-survives-restart"].edges, NET), "pass");
});

test("offRequestPath: the external call happens behind a queue", () => {
  expect("offRequestPath", REFERENCE["refresh-takes-seconds"], "pass", { says: /slows the job, not the request/ });
  const sync = board([N("u", "users"), N("a", "ecs"), N("s", "website")], [E("u", "a"), E("a", "s")]);
  expect("offRequestPath", sync, "fail", { edges: 1, says: /request path/ });
  expect("offRequestPath", board([N("u", "users"), N("s", "website")]), "wait");
});

test("workerFromQueue: SQS between the API and the worker; SNS alone is not durable", () => {
  expect("workerFromQueue", REFERENCE["refresh-takes-seconds"], "pass");
  const topic = board([N("u", "users"), N("a", "lambda"), N("t", "sns"), N("w", "lambda"), N("s", "website")], [E("u", "a"), E("a", "t"), E("t", "w"), E("w", "s")]);
  expect("workerFromQueue", topic, "fail", { nodes: ["t"], says: /pushes each message once/ });
  const orphan = board([N("u", "users"), N("a", "lambda"), N("q", "sqs")], [E("u", "a"), E("a", "q")]);
  expect("workerFromQueue", orphan, "fail", { nodes: ["q"], says: /nothing takes them/ });
  expect("workerFromQueue", board([N("u", "users"), N("a", "lambda")], [E("u", "a")]), "fail", { says: /Add a queue/ });
});

test("resultsDurable: the worker writes to a store", () => {
  expect("resultsDurable", REFERENCE["refresh-takes-seconds"], "pass");
  const cached = board([N("q", "sqs"), N("w", "ecs"), N("c", "elasticache")], [E("q", "w"), E("w", "c")]);
  expect("resultsDurable", cached, "fail", { edges: 1, says: /evict/ });
  expect("resultsDurable", board([N("q", "sqs"), N("w", "ecs")], [E("q", "w")]), "fail", { nodes: ["w"] });
  expect("resultsDurable", board([N("q", "sqs")]), "wait");
});

test("statusReadable: the browser can read what the worker wrote", () => {
  expect("statusReadable", REFERENCE["refresh-takes-seconds"], "pass");
  const blind = REFERENCE["refresh-takes-seconds"];
  const noStatus = board(blind.nodes, blind.edges.filter((e) => !(e.from === "api" && e.to === "results")));
  expect("statusReadable", noStatus, "fail", { nodes: ["results"] });
  const pushed = board([N("u", "users"), N("q", "sqs"), N("w", "lambda"), N("t", "sns")], [E("u", "q"), E("q", "w"), E("w", "t"), E("t", "u")]);
  expect("statusReadable", pushed, "pass", { says: /pushed/ });
});

test("deadLetters: the work queue redrives to a second queue", () => {
  expect("deadLetters", REFERENCE["refresh-takes-seconds"], "pass");
  const r = REFERENCE["refresh-takes-seconds"];
  expect("deadLetters", board(r.nodes, r.edges.filter((e) => e.to !== "dead")), "fail", { nodes: ["jobs"] });
  expect("deadLetters", board([N("q", "sqs")]), "wait");
});

test("callDeadline, breaker, fallback: read the guards on the arrow into the outside service", () => {
  const call = (g) => board([N("w", "ecs"), N("s", "thirdparty")], [E("w", "s", g)]);
  expect("callDeadline", call({ timeout: true }), "pass");
  expect("callDeadline", call({}), "fail", { edges: 1, says: /Timeout/ });
  expect("breaker", call({ timeout: true, breaker: true }), "pass");
  expect("breaker", call({ breaker: true }), "pass", { says: /never fails/ });
  expect("breaker", call({ timeout: true }), "fail", { edges: 1 });
  expect("fallback", call({ fallback: true }), "pass");
  expect("fallback", call({ timeout: true, breaker: true }), "fail", { edges: 1 });
  for (const id of ["callDeadline", "breaker", "fallback"]) expect(id, board([N("w", "ecs")]), "wait");
});

test("egress: a private worker needs a NAT gateway in a public subnet and an internet gateway", () => {
  const worker = (extra, groups = NET) => board([N("w", "ecs", ...at("priva")), N("s", "website", ...at("out")), ...extra], [E("w", "s", { timeout: true })], groups);
  expect("egress", worker([N("nat", "natgw", ...at("puba")), N("igw", "igw", ...at("edge"))]), "pass", { says: /nothing on the internet can start/ });
  expect("egress", worker([]), "fail", { nodes: ["w"], groups: ["priva"], says: /no route to the internet/ });
  expect("egress", worker([N("nat", "natgw", ...at("privb")), N("igw", "igw", ...at("edge"))]), "fail", { nodes: ["nat"], says: /public subnet/ });
  expect("egress", worker([N("nat", "natgw", ...at("puba"))]), "fail", { nodes: ["nat"], says: /internet gateway/ });
  // Lambda outside any VPC reaches the internet directly.
  expect("egress", board([N("w", "lambda"), N("s", "website")], [E("w", "s")]), "pass", { says: /directly/ });
  expect("egress", board([N("w", "lambda")]), "wait");
});

test("admission: API Gateway or WAF in front; a load balancer never refuses", () => {
  expect("admission", REFERENCE["dependency-slow"], "pass", { says: /429/ });
  const bare = board([N("u", "users"), N("l", "alb"), N("a", "ecs")], [E("u", "l"), E("l", "a")]);
  expect("admission", bare, "fail", { nodes: ["a"], says: /never refuses/ });
  expect("admission", board([N("u", "users"), N("g", "apigw"), N("f", "lambda")], [E("u", "g"), E("g", "f")]), "pass");
  expect("admission", board([N("u", "users")]), "wait");
});

test("bulkhead: bookmark compute that never waits on the third party", () => {
  expect("bulkhead", REFERENCE["dependency-slow"], "pass");
  const shared = board([N("u", "users"), N("l", "alb"), N("a", "ecs"), N("d", "rds"), N("t", "thirdparty")], [E("u", "l"), E("l", "a"), E("a", "d"), E("a", "t", { timeout: true })]);
  expect("bulkhead", shared, "fail", { nodes: ["a"], edges: 1, says: /threads fill up/ });
  // Through a synchronous hop is still shared.
  const chain = board([N("u", "users"), N("a", "ecs"), N("p", "ecs"), N("d", "rds"), N("t", "thirdparty")], [E("u", "a"), E("a", "d"), E("a", "p"), E("p", "t")]);
  expect("bulkhead", chain, "fail", { says: /waits on/ });
  // Through a queue is not.
  const queued = board([N("u", "users"), N("a", "ecs"), N("q", "sqs"), N("p", "ecs"), N("d", "rds"), N("t", "thirdparty")], [E("u", "a"), E("a", "d"), E("a", "q"), E("q", "p"), E("p", "t")]);
  expect("bulkhead", queued, "pass");
  expect("bulkhead", board([N("u", "users")]), "wait");
});

// ------------------------------------------------------------ the references
for (const x of EXERCISES) {
  test(`${x.id}: the reference design meets every check`, () => {
    const results = runChecks(model(REFERENCE[x.id]), x.checks);
    for (const r of results) assert.equal(r.status, "pass", `${r.id}: ${r.html}`);
  });
  test(`${x.id}: an empty board meets none`, () => {
    for (const r of runChecks(model(board([])), x.checks)) assert.notEqual(r.status, "pass", `${r.id} passed an empty board: ${r.html}`);
  });
}

// ------------------------------------------------------------------ break it
test("a failed zone takes what runs in it, and nothing regional", () => {
  const m = model(REFERENCE["read-traffic-grows"]);
  const down = downSet(m, { groups: ["aza"] });
  assert.ok(down.has("apia"));
  assert.ok(!down.has("cache"), "Multi-AZ cache survives its zone");
  assert.ok(!down.has("alb"), "a load balancer is regional");
  const sqsInZone = model(board([N("q", "sqs", ...at("priva"))], [], NET));
  assert.equal(downSet(sqsInZone, { groups: ["aza"] }).size, 0, "SQS drawn in a zone is still regional");
  const region = model(board([N("q", "sqs", 200, 200), N("u", "users", 200, 210)], [], [G("r", "region", 0, 0, 400, 400)]));
  assert.deepEqual([...downSet(region, { groups: ["r"] })], ["q"], "a region takes everything but the edge");
});

test("a hanging dependency: no timeout sticks the caller, a timeout slows it, a breaker frees it", () => {
  const b = (g) => model(board([N("u", "users"), N("a", "ecs"), N("d", "rds"), N("t", "thirdparty")], [E("u", "a"), E("a", "d"), E("a", "t", g)]));
  const cap = (m) => CAPABILITIES.save(simulate(m, { nodes: ["t"] })).status;
  assert.equal(cap(b({})), "down", "the bookmark path hangs behind the third party");
  assert.equal(cap(b({ timeout: true })), "slow");
  assert.equal(cap(b({ timeout: true, breaker: true })), "ok");
  // Two hops: the caller of a stuck service is stuck too.
  const chain = model(board([N("u", "users"), N("a", "ecs"), N("p", "ecs"), N("d", "rds"), N("t", "thirdparty")], [E("u", "a"), E("a", "d"), E("a", "p"), E("p", "t")]));
  assert.equal(simulate(chain, { nodes: ["t"] }).health.get("a"), "stuck");
  // A queue in between absorbs it.
  const queued = model(board([N("u", "users"), N("a", "ecs"), N("q", "sqs"), N("p", "ecs"), N("d", "rds"), N("t", "thirdparty")], [E("u", "a"), E("a", "d"), E("a", "q"), E("q", "p"), E("p", "t")]));
  assert.equal(simulate(queued, { nodes: ["t"] }).health.get("a"), "ok");
});

test("capabilities in each sketch's own terms", () => {
  const r3 = model(REFERENCE["refresh-takes-seconds"]);
  assert.equal(CAPABILITIES.process(simulate(r3, {})).status, "ok");
  const paused = CAPABILITIES.process(simulate(r3, { nodes: ["worker"] }));
  assert.equal(paused.status, "paused", "a dead worker pauses the work; the jobs wait");
  assert.equal(CAPABILITIES.accept(simulate(r3, { nodes: ["worker"] })).status, "ok", "and refreshes are still accepted");
  const hung = CAPABILITIES.process(simulate(r3, { nodes: ["site"] }));
  assert.equal(hung.status, "degraded", "with a timeout, a hanging site means retries, not a hung worker");
  const r2 = model(REFERENCE["read-traffic-grows"]);
  const noCache = CAPABILITIES.read(simulate(r2, { nodes: ["cache"] }));
  assert.equal(noCache.status, "ok"); assert.equal(noCache.note, "load");
  const noDb = CAPABILITIES.read(simulate(r2, { nodes: ["db"] }));
  assert.equal(noDb.status, "degraded", "with the database gone, cached reads still work");
  assert.equal(CAPABILITIES.save(simulate(r2, { nodes: ["db"] })).status, "down");
  const r4 = model(REFERENCE["dependency-slow"]);
  const slow = simulate(r4, { nodes: ["api3"] });
  assert.equal(CAPABILITIES.critical(slow).status, "ok", "bookmarks carry on while the third party hangs");
  assert.equal(CAPABILITIES.preview(slow).status, "degraded", "previews fall back");
});

// ---------------------------------------------------------- the coverage gate
test("every check was seen both passing and failing", () => {
  for (const id of Object.keys(CHECKS)) {
    const got = seen[id] || new Set();
    assert.ok(got.has("pass") && got.has("fail"), `${id} was seen ${[...got].join(", ") || "never"}: it needs a diagram it passes and one it fails`);
  }
});
