// Small diagrams for the checks' tests, built the way the board stores them.
// Positions matter only where a check reads containment (zones, subnets).
let seq = 0;
export const N = (id, part, x = 0, y = 0, extra = {}) => ({ id, part, name: extra.name ?? id, x, y, ...extra });
export const G = (id, part, x, y, w, h, name = id) => ({ id, part, name, x, y, w, h });
export const E = (from, to, guards = {}, label = "") => ({ id: `e${++seq}`, from, to, label, guards });
export const board = (nodes, edges = [], groups = []) => ({ nodes, edges, groups });

// A VPC with two zones, each split into a public subnet (top) and a private
// one (bottom). Zone a spans x 100-400, zone b x 420-720.
export const NET = [
  G("vpc", "vpc", 80, 60, 660, 520, "vpc"),
  G("aza", "az", 100, 100, 300, 460, "us-east-1a"),
  G("azb", "az", 420, 100, 300, 460, "us-east-1b"),
  G("puba", "public", 110, 130, 280, 150, "public a"),
  G("pubb", "public", 430, 130, 280, 150, "public b"),
  G("priva", "private", 110, 300, 280, 250, "private a"),
  G("privb", "private", 430, 300, 280, 250, "private b"),
];
export const AT = {                      // centres inside each box
  puba: [250, 200], pubb: [570, 200], priva: [200, 380], privb: [520, 380],
  priva2: [300, 480], privb2: [620, 480], vpc: [410, 90], out: [900, 300], edge: [410, 60],
};
const at = (k) => AT[k];

// ----------------------------------------------------------- references
// One design per sketch that meets every check that sketch asks.
export const REFERENCE = {
  "bookmark-survives-restart": board(
    [N("user", "users"), N("gw", "apigw"), N("fn", "lambda"), N("db", "dynamodb")],
    [E("user", "gw"), E("gw", "fn"), E("fn", "db")],
  ),
  "read-traffic-grows": board(
    [N("user", "users", ...at("out")), N("alb", "alb", ...at("vpc")),
     N("apia", "ecs", ...at("priva")), N("apib", "ecs", ...at("privb")),
     N("cache", "elasticache", ...at("priva2"), { multiAz: true }), N("db", "rds", ...at("privb2"), { multiAz: true })],
    [E("user", "alb"), E("alb", "apia"), E("alb", "apib"), E("apia", "cache"), E("apib", "cache"), E("apia", "db"), E("apib", "db")],
    NET,
  ),
  "refresh-takes-seconds": board(
    [N("user", "users"), N("gw", "apigw"), N("api", "lambda"), N("jobs", "sqs"), N("dead", "sqs"),
     N("worker", "lambda"), N("site", "website"), N("results", "dynamodb")],
    [E("user", "gw"), E("gw", "api"), E("api", "jobs"), E("api", "results"), E("jobs", "worker"), E("jobs", "dead"),
     E("worker", "site", { timeout: true, retries: true }), E("worker", "results")],
  ),
  "dependency-slow": board(
    [N("user", "users", ...at("out")), N("waf", "waf", 900, 200), N("alb", "alb", ...at("vpc")),
     N("crita", "ecs", ...at("priva")), N("critb", "ecs", ...at("privb")), N("prev", "ecs", ...at("priva2")),
     N("db", "rds", ...at("privb2"), { multiAz: true }), N("api3", "thirdparty", 900, 500)],
    [E("user", "waf"), E("waf", "alb"), E("alb", "crita"), E("alb", "critb"), E("alb", "prev"),
     E("crita", "db"), E("critb", "db"), E("prev", "api3", { timeout: true, breaker: true, fallback: true })],
    NET,
  ),
};
