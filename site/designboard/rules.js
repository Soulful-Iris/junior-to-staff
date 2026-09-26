// Which arrows AWS can actually make. An arrow is a request or a message, so
// the question is: can this kind of thing send one to that kind of thing?
//
// Written as allow-lists for the kinds whose outgoing traffic is narrow
// (stores send nothing, a queue only hands messages to whoever takes them), and
// deny-lists for the kinds that can call almost anything (API Gateway,
// workflows, clients). Code you run (compute, function) and anything the
// catalog files as "other" are never refused: the board cannot know what your
// code does, and refusing a legitimate design is worse than missing an odd one.

const RULES = {
  relational: { to: [], why: "A database answers queries; it never sends requests. The arrow starts at the code that reads or writes it." },
  nosql: { to: ["function", "stream", "bus"], why: "A NoSQL database sends nothing but change events, to Lambda, a Kinesis stream or EventBridge Pipes. The arrow starts at the code that reads or writes it." },
  cache: { to: [], why: "A cache answers lookups; it never sends requests. The arrow starts at the code that looks things up in it." },
  search: { to: [], why: "OpenSearch answers queries; it never sends requests. The arrow starts at the code that searches it." },
  files: { to: [], why: "A file system or a disk is read and written by servers; it never sends requests." },
  proxy: { to: ["relational"], why: "RDS Proxy only forwards connections to an RDS or Aurora database." },
  objects: { to: ["function", "queue", "topic", "bus"], why: "S3 only sends event notifications, to Lambda, SQS, SNS or EventBridge. The arrow starts at the code that reads or writes the bucket." },
  queue: { to: ["compute", "function", "queue", "bus"], why: "A queue only hands messages to whatever takes them: a worker, a Lambda function, or a dead-letter queue. Something has to take the message and do the writing." },
  topic: { to: ["queue", "function", "compute", "external", "client", "stream", "email"], why: "SNS delivers to subscribers: SQS queues, Lambda functions, HTTP endpoints, email and phones. It cannot write to a store." },
  bus: { to: ["function", "queue", "topic", "bus", "workflow", "stream", "compute", "gateway", "external", "observe"], why: "EventBridge sends events to targets such as Lambda, SQS, SNS, Step Functions or an API destination. It cannot write to a store." },
  stream: { to: ["function", "compute", "objects", "search", "stream", "external", "other"], why: "A stream is read by consumers such as Lambda or your workers, and Firehose delivers to S3, OpenSearch, Redshift or an HTTP endpoint." },
  dns: { to: ["cdn", "gateway", "lb", "compute", "objects", "accelerator"], why: "Route 53 points a name at CloudFront, a load balancer, API Gateway, an S3 website, Global Accelerator or an instance's address." },
  cdn: { to: ["objects", "lb", "gateway", "compute", "function", "external"], why: "CloudFront fetches from an origin: S3, a load balancer, API Gateway, a Lambda function URL or any web server." },
  accelerator: { to: ["lb", "compute"], why: "Global Accelerator forwards to load balancers and instances." },
  waf: { to: ["cdn", "lb", "gateway", "compute", "identity"], why: "AWS WAF sits in front of CloudFront, a load balancer, API Gateway, AppSync, App Runner or Cognito, and passes allowed requests on to it." },
  lb: { to: ["compute", "function", "lb"], why: "A load balancer forwards requests to targets that run code: instances, containers or Lambda functions. It cannot query a database or write to a queue." },
  nat: { to: ["igw", "external"], why: "A NAT gateway only carries outbound traffic to the internet, through the internet gateway." },
  igw: { to: ["lb", "compute", "nat", "external", "client"], why: "An internet gateway joins the VPC to the internet: it carries traffic between the internet and public addresses such as a load balancer." },
  identity: { to: ["function"], why: "Cognito and IAM call nothing but Lambda triggers." },
  secrets: { to: ["function"], why: "Secrets Manager and KMS answer requests; the only thing they call is a rotation Lambda." },
  observe: { to: ["topic", "function", "bus", "queue"], why: "CloudWatch alarms and rules notify SNS, Lambda, EventBridge or SQS." },
  email: { to: ["topic", "function", "objects", "client", "queue"], why: "SES sends mail to people, and hands received mail to S3, SNS or Lambda." },
  external: { to: ["dns", "cdn", "waf", "gateway", "lb", "compute", "function", "accelerator", "igw"], why: "A service outside AWS can only reach your public entry points: DNS, CloudFront, a load balancer or API Gateway." },
  endpoint: { deny: ["client", "external", "dns", "cdn", "waf", "nat", "igw", "accelerator"], why: "A VPC endpoint is a private door from inside the VPC to an AWS service; nothing on the internet comes through it." },
  workflow: { deny: ["client", "dns", "cdn", "waf", "lb", "nat", "igw", "cache", "search", "proxy", "files", "accelerator"], why: "Step Functions calls AWS services and HTTP endpoints; it cannot open a connection to a cache, a proxy or a load balancer." },
  gateway: { deny: ["relational", "cache", "proxy", "search", "files", "nat", "igw", "dns", "cdn", "waf", "accelerator"], why: "API Gateway cannot run a SQL query or read a cache: put a Lambda function or a service between it and the data." },
  client: {
    deny: ["cache", "proxy", "nat", "files", "endpoint"],
    whyTo: {
      cache: "ElastiCache has no public endpoint: only code inside your VPC can reach it.",
      proxy: "RDS Proxy can only be reached from inside your VPC.",
      nat: "A NAT gateway carries traffic out of a VPC, never in.",
      files: "A file system is mounted by servers in your VPC, never reached from a browser.",
      endpoint: "A VPC endpoint is private: nothing outside the VPC comes through it.",
    },
  },
};

// Parts that differ from their kind: AppSync resolvers can query Aurora
// through the Data API, and read caches through Lambda only.
const PART_RULES = {
  appsync: { deny: ["cache", "proxy", "files", "nat", "igw", "dns", "cdn", "waf", "accelerator"], why: "AppSync resolves through Lambda, DynamoDB, Aurora's Data API, OpenSearch, HTTP or EventBridge; it cannot open a connection to a cache or a proxy." },
};

// null if AWS can send this, otherwise a sentence saying why not.
export function arrowProblem(fromPart, toPart) {
  if (!fromPart || !toPart) return null;
  const rule = PART_RULES[fromPart.id] || RULES[fromPart.kind];
  if (!rule) return null;
  const k = toPart.kind;
  if (k === "other" || fromPart.kind === "other") return null;
  const refused = rule.to ? !rule.to.includes(k) : (rule.deny || []).includes(k);
  if (!refused) return null;
  return (rule.whyTo && rule.whyTo[k]) || rule.why;
}

// An arrow into a client from something that cannot push is almost always a
// reply drawn as its own arrow. Say so, instead of the generic sentence.
export const REPLY = "On this board an arrow is a request, and the answer travels back along it. Draw the arrow from the side that asks.";
