// Parts as people draw them on a whiteboard: a few strokes each, the shape an
// engineer would sketch with a marker in an interview (a cylinder for a
// database, a slotted bar for a queue, a bucket for S3), with AWS's name
// written under it by the board. Bruno, 2026-09-26: the AWS icons are "not
// drawable ... they are not gonna be sketching computer images in an
// interview", and a plain box "called a db" is not experience either. This is
// the ground between.
//
// Each glyph lives in the icon's 44 x 44 box. Strokes use currentColor; an
// element with class "t" is the pale fill behind the strokes.
const S = (d) => `<path d="${d}"/>`;
const C = (cx, cy, r, cls = "") => `<circle${cls ? ` class="${cls}"` : ""} cx="${cx}" cy="${cy}" r="${r}"/>`;
const R = (x, y, w, h, rx = 2, cls = "") => `<rect${cls ? ` class="${cls}"` : ""} x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}"/>`;
const dot = (cx, cy, r = 1.4) => `<circle class="f" cx="${cx}" cy="${cy}" r="${r}"/>`;
const head = (x1, y1, x2, y2, s = 4.2) => {        // an arrowhead at (x2, y2) pointing away from (x1, y1)
  const a = Math.atan2(y2 - y1, x2 - x1), p = (t) => [x2 - s * Math.cos(a + t), y2 - s * Math.sin(a + t)];
  const [l, r] = [p(0.5), p(-0.5)];
  return S(`M${l[0].toFixed(1)} ${l[1].toFixed(1)} L${x2} ${y2} L${r[0].toFixed(1)} ${r[1].toFixed(1)}`);
};
const arrow = (x1, y1, x2, y2) => S(`M${x1} ${y1} L${x2} ${y2}`) + head(x1, y1, x2, y2);
const cylinder = (inner = "") => `<path class="t" d="M9 11 V33 A13 4.5 0 0 0 35 33 V11 Z"/>` + `<ellipse cx="22" cy="11" rx="13" ry="4.5"/>` + S("M9 11 V33 A13 4.5 0 0 0 35 33 V11") + inner;

const G = {
  // outside
  users: S("M5 37 C5 27 27 27 27 37") + C(16, 16, 6, "t") + S("M25 26 C32 24 39 28 39 35") + C(29, 13, 5),
  browser: R(8, 9, 28, 19, 2, "t") + S("M4 33 H40 M8 28 L5 33 M36 28 L39 33"),
  mobile: R(14, 5, 16, 34, 3, "t") + dot(22, 34, 1.3) + S("M19 9 H25"),
  website: R(6, 8, 32, 28, 2, "t") + S("M6 14 H38 M11 20 H33 M11 25 H28 M11 30 H31"),
  thirdparty: `<path class="t" d="M13 33 C7 33 6 25 12 24 C11 17 20 14 24 19 C27 14 36 16 35 23 C41 23 41 33 34 33 Z"/>` + S("M13 33 C7 33 6 25 12 24 C11 17 20 14 24 19 C27 14 36 16 35 23 C41 23 41 33 34 33 Z"),
  // network and edge
  route53: S("M22 7 V38 M16 38 H28") + `<path class="t" d="M22 10 H33 L36.5 13.5 L33 17 H22 Z M22 20 H11 L7.5 23.5 L11 27 H22 Z"/>` + S("M22 10 H33 L36.5 13.5 L33 17 H22 M22 20 H11 L7.5 23.5 L11 27 H22"),
  cloudfront: C(22, 22, 14, "t") + S("M8 22 H36") + `<ellipse cx="22" cy="22" rx="6" ry="14"/>` + dot(22, 8, 2.2) + dot(9.9, 29, 2.2) + dot(34.1, 29, 2.2),
  apigw: R(6, 9, 32, 26, 4, "t") + S("M16 16 L11 22 L16 28 M28 16 L33 22 L28 28 M24.5 14.5 L19.5 29.5"),
  alb: C(12, 22, 6, "t") + arrow(18, 20, 36, 9) + arrow(18, 22, 37, 22) + arrow(18, 24, 36, 35),
  natgw: R(6, 12, 32, 20, 4, "t") + arrow(11, 22, 33, 22) + S("M11 17 V27"),
  igw: `<path class="t" d="M10 38 V18 A12 12 0 0 1 34 18 V38 Z"/>` + S("M10 38 V18 A12 12 0 0 1 34 18 V38 M5 38 H39") + arrow(16, 29, 28, 29),
  vpce: R(14, 16, 16, 14, 2, "t") + S("M18 9 V16 M26 9 V16 M22 30 V38"),
  globalaccel: arrow(10, 22, 36, 22) + S("M6 15 H16 M6 29 H16 M11 22 H3"),
  // security
  waf: R(7, 10, 30, 24, 1.5, "t") + S("M7 18 H37 M7 26 H37 M17 10 V18 M27 10 V18 M12 18 V26 M22 18 V26 M32 18 V26 M17 26 V34 M27 26 V34"),
  shield: `<path class="t" d="M22 6 L36 11 V21 C36 30 29 36 22 39 C15 36 8 30 8 21 V11 Z"/>` + S("M22 6 L36 11 V21 C36 30 29 36 22 39 C15 36 8 30 8 21 V11 Z"),
  cognito: R(8, 8, 28, 28, 3, "t") + C(17, 18, 4) + S("M11 30 C11 24 23 24 23 30 M27 17 H32 M27 23 H32"),
  iam: R(11, 20, 22, 17, 3, "t") + S("M15 20 V15 A7 7 0 0 1 29 15 V20") + dot(22, 28.5, 1.8),
  secrets: C(14, 22, 6, "t") + S("M20 22 H37 M31 22 V28 M35.5 22 V27"),
  acm: R(7, 9, 30, 21, 2, "t") + S("M12 15 H30 M12 21 H24") + C(30, 30, 4) + S("M27.5 33.5 L26 39 L30 37 L34 39 L32.5 33.5"),
  // compute
  lambda: R(8, 8, 28, 28, 4, "t") + S("M15 13 H18 C20 13 21 14 22 16 L30 31 M22 21 L15 31"),
  ec2: R(8, 8, 28, 12, 2, "t") + R(8, 24, 28, 12, 2, "t") + dot(13, 14) + dot(13, 30) + S("M18 14 H31 M18 30 H31"),
  ecs: R(6, 11, 32, 22, 2, "t") + S("M12 14 V30 M17 14 V30 M22 14 V30 M27 14 V30 M32 14 V30"),
  eks: `<path class="t" d="M22 5 L37 13.5 V30.5 L22 39 L7 30.5 V13.5 Z"/>` + S("M22 5 L37 13.5 V30.5 L22 39 L7 30.5 V13.5 Z") + C(22, 22, 5),
  batch: R(12, 6, 24, 18, 2) + R(8, 12, 24, 18, 2, "t") + S("M13 20 H27 M13 25 H23"),
  // integration
  sqs: R(4, 15, 36, 14, 2, "t") + S("M11 15 V29 M18 15 V29 M25 15 V29 M32 15 V29"),
  sns: C(11, 22, 4.5, "t") + S("M15.5 22 L31 11 M15.5 22 H31 M15.5 22 L31 33") + C(34, 9.5, 3) + C(35, 22, 3) + C(34, 34.5, 3),
  eventbridge: R(4, 12, 36, 9, 4.5, "t") + arrow(12, 21, 12, 34) + arrow(22, 21, 22, 34) + arrow(32, 21, 32, 34),
  stepfunctions: R(14, 4, 16, 9, 2, "t") + R(14, 18, 16, 9, 2, "t") + R(14, 32, 16, 9, 2, "t") + arrow(22, 13, 22, 17.5) + arrow(22, 27, 22, 31.5),
  kinesis: `<path class="t" d="M4 15 H40 V29 H4 Z"/>` + S("M4 15 H40 M4 29 H40") + S("M8 22 C11 17.5 13 26.5 16 22 C19 17.5 21 26.5 24 22 H31") + head(26, 22, 34, 22),
  appsync: R(12, 5, 20, 34, 4, "t") + S("M17 13 L27 13 M17 22 H27 M17 31 H27") + dot(17, 13, 2) + dot(27, 22, 2) + dot(17, 31, 2) + S("M17 13 L27 22 L17 31"),
  // data
  rds: cylinder(S("M9 22 A13 4.5 0 0 0 35 22")),
  dynamodb: cylinder(S("M14 21 H16 M19 21 H30 M14 27.5 H16 M19 27.5 H30")),
  documentdb: cylinder(S("M16 18 H25 L28 21 V31 H16 Z M25 18 V21 H28")),
  neptune: cylinder(dot(16, 20, 2) + dot(28, 21, 2) + dot(22, 30, 2) + S("M16 20 L28 21 L22 30 Z")),
  elasticache: R(8, 8, 28, 28, 4) + `<path class="t" d="M24 11 L14 24 H21 L18 34 L29 20 H22 Z"/>` + S("M24 11 L14 24 H21 L18 34 L29 20 H22 Z"),
  rdsproxy: R(9, 13, 26, 18, 3, "t") + arrow(15, 22, 31, 22) + head(29, 22, 13, 22),
  s3: `<path class="t" d="M9 12 L13 36 C14 39 30 39 31 36 L35 12 Z"/>` + S("M9 12 L13 36 C14 39 30 39 31 36 L35 12") + `<ellipse cx="22" cy="12" rx="13" ry="4"/>`,
  efs: `<path class="t" d="M6 13 H18 L21 17 H38 V35 H6 Z"/>` + S("M6 13 H18 L21 17 H38 V35 H6 Z"),
  ebs: `<ellipse class="t" cx="22" cy="22" rx="15" ry="11"/>` + `<ellipse cx="22" cy="22" rx="15" ry="11"/>` + `<ellipse cx="22" cy="22" rx="4" ry="3"/>`,
  opensearch: C(19, 19, 10, "t") + S("M26.5 26.5 L37 37"),
  redshift: `<ellipse cx="22" cy="9" rx="12" ry="3.5"/>` + S("M10 9 V17 A12 3.5 0 0 0 34 17 V9 M10 17 V26 A12 3.5 0 0 0 34 26 V17 M10 26 V35 A12 3.5 0 0 0 34 35 V26") + `<path class="t" d="M10 9 V35 A12 3.5 0 0 0 34 35 V9 Z"/>`,
  athena: R(6, 8, 22, 22, 2, "t") + S("M6 15 H28 M6 22 H28 M13 8 V30") + C(29, 29, 6) + S("M33.5 33.5 L39 39"),
  // operations
  cloudwatch: S("M7 8 V36 H38") + `<path class="t" d="M10 30 L17 21 L23 26 L33 12 V36 H10 Z"/>` + S("M10 30 L17 21 L23 26 L33 12"),
  xray: R(6, 8, 32, 28, 3, "t") + S("M11 29 L17 18 L23 25 L29 14 L34 20") + dot(17, 18, 1.8) + dot(23, 25, 1.8) + dot(29, 14, 1.8),
  ses: R(6, 11, 32, 22, 2, "t") + S("M6 13 L22 25 L38 13"),
};
// Parts that draw like another.
const SAME = {
  nlb: "alb", clb: "alb", fargate: "ecs", ecstask: "ecs", apprunner: "ecs", beanstalk: "ec2",
  mq: "sqs", firehose: "kinesis", msk: "kinesis", aurora: "rds", keyspaces: "dynamodb", memorydb: "elasticache",
  redis: "elasticache", valkey: "elasticache", memcached: "elasticache", dax: "elasticache", glacier: "s3", kms: "secrets",
};
export const SKETCH_GLYPHS = Object.fromEntries(Object.keys({ ...G, ...SAME }).map((k) => [k, G[SAME[k] || k]]));

// The boxes as the parts list shows them: a rectangle drawn the way the board
// draws that box (a VPC solid, a zone dashed, a region dotted), with a hint of
// what goes in it.
const BOXES = {
  region: `<rect x="5" y="9" width="34" height="26" rx="2" stroke-dasharray="1.5 3.5"/>` + S("M10 14 V22 M10 14 H17 L15.5 16.5 L17 19 H10"),
  vpc: `<rect class="t" x="5" y="9" width="34" height="26" rx="2"/>` + `<rect x="5" y="9" width="34" height="26" rx="2"/>` + S("M13 25 C9 25 9 19.5 13 19.5 C13.5 16 19.5 15.5 21 18.5 C23.5 17.5 26 19.5 25 22 C27.5 22.5 27 25 25 25 Z"),
  az: `<rect x="5" y="9" width="34" height="26" rx="2" stroke-dasharray="5 3.5"/>`,
  "public-subnet": `<rect class="t" x="5" y="9" width="34" height="26" rx="2"/>` + `<rect x="5" y="9" width="34" height="26" rx="2"/>` + S("M11 22 V19 A3 3 0 0 1 17 19 M10 22 H18 V28 H10 Z"),
  "private-subnet": `<rect class="t" x="5" y="9" width="34" height="26" rx="2"/>` + `<rect x="5" y="9" width="34" height="26" rx="2"/>` + S("M11 22 V19 A3 3 0 0 1 17 19 V22 M10 22 H18 V28 H10 Z"),
  asg: `<rect x="5" y="9" width="34" height="26" rx="2" stroke-dasharray="5 3.5"/>` + S("M22 14 V30 M14 22 H30") + head(22, 22, 22, 14, 3.5) + head(22, 22, 22, 30, 3.5) + head(22, 22, 14, 22, 3.5) + head(22, 22, 30, 22, 3.5),
  cloud: `<rect x="5" y="9" width="34" height="26" rx="2"/>` + S("M5 16 H39"),
};
export function boxGlyph(def) {
  const g = BOXES[def.type];
  return g ? `<g class="db-sk db-sk-box" style="color:${def.color}">${g}</g>` : "";
}

// A glyph, placed with its box's top left at (x, y), in its category's colour.
export function glyph(part, x, y, size = 44) {
  const g = SKETCH_GLYPHS[part.id];
  if (!g) return "";
  const s = size / 44;
  return `<g class="db-sk c-${part.category}" transform="translate(${x} ${y})${s !== 1 ? ` scale(${s})` : ""}">${g}</g>`;
}
