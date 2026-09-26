// Parts as they are drawn on a real whiteboard: a handful of plain shapes,
// the name written inside, one marker. Bruno, 2026-09-26, after my first
// "drawable" set turned out to be icons in marker colours: "look for real life
// whiteboard drawings. They are usually pretty shitty but look for each one of
// them. Then make the box version of them."
//
// What the research found (~/scratch/wb-research, about 150 real photos of
// whiteboards, paper and lightboards; AWS architects, interview-prep boards,
// team boards):
// - anything that computes or routes is a box with its name inside. A load
//   balancer or a firewall is often a flat bar across the line.
// - a database is an upright cylinder in 88% of real drawings, and a cylinder
//   means "data is kept here" (object, file and block storage too). A cache
//   or a search index is never a cylinder. The guide's own whiteboard page
//   says the same: "boxes for responsibilities, cylinders for durable state".
// - a cloud means outside the system: the internet, someone else's API.
// - the only pictures are people and devices (stick figure, phone, screen),
//   and they get their name underneath rather than inside.
// - nobody draws vendor icons, and nobody draws a brick wall.
// Real boards say "LB" and "DB"; this board writes AWS's names, because
// picking the right part is the exercise.
//
// Geometry is in board units, centred on the part's (x, y).

// kind -> shape. Anything not listed is a box.
const BY_KIND = {
  relational: "cyl", nosql: "cyl", objects: "cyl", files: "cyl",
  client: "box", external: "cloud", lb: "bar", waf: "bar", igw: "circle",
};
// part -> shape, where the part differs from its kind.
const BY_PART = {
  users: "person", mobile: "phone", browser: "screen",
  redshift: "cyl", athena: "box", neptune: "cyl", memorydb: "cyl",
};
// What goes inside when the full name cannot fit its shape: what people
// actually write. The network research saw "IGW" in a small circle on the
// VPC's edge. Long names elsewhere wrap onto two lines instead.
const INSIDE = { igw: "IGW" };

export function shapeOf(part) {
  return BY_PART[part.id] || BY_KIND[part.kind] || "box";
}
export const PICTURES = new Set(["person", "phone", "screen"]);   // name underneath, not inside
export function insideText(part) {
  return INSIDE[part.id] || part.short;
}

// Split a long name into two lines at the space nearest its middle.
export function lines(text, measure, max = 104) {
  if (measure(text) <= max || !text.includes(" ")) return [text];
  let best = null;
  for (let i = text.indexOf(" "); i >= 0; i = text.indexOf(" ", i + 1)) {
    const a = text.slice(0, i), b = text.slice(i + 1), w = Math.max(measure(a), measure(b));
    if (!best || w < best.w) best = { a, b, w };
  }
  return [best.a, best.b];
}

// The size a part takes on the board: w x h of the shape itself.
export function sizeOf(part, measure) {
  const shape = shapeOf(part);
  if (PICTURES.has(shape)) return { shape, w: 44, h: 44, text: [] };
  const text = lines(insideText(part), measure);
  const tw = Math.max(...text.map(measure));
  const two = text.length > 1;
  switch (shape) {
    case "cyl": return { shape, w: Math.max(46, tw + 20), h: two ? 56 : 48, text };
    case "cloud": return { shape, w: Math.max(66, tw + 34), h: two ? 50 : 42, text };
    case "circle": return { shape, w: Math.max(40, tw + 14), h: Math.max(40, tw + 14), text };
    case "bar": return { shape, w: Math.max(64, tw + 28), h: two ? 42 : 28, text };
    default: return { shape, w: Math.max(46, tw + 20), h: two ? 44 : 34, text };
  }
}

const f = (n) => Math.round(n * 10) / 10;

// The shape, drawn centred on (x, y), with its name inside when it has one.
export function drawPart(part, x, y, measure, cls = "db-wb") {
  const s = sizeOf(part, measure), { w, h } = s, l = f(x - w / 2), t = f(y - h / 2);
  let g = "";
  switch (s.shape) {
    case "person":
      g = `<circle cx="${x}" cy="${f(y - 13)}" r="6.5"/><path d="M${x} ${f(y - 6.5)} V${f(y + 8)} M${f(x - 10)} ${f(y - 1)} H${f(x + 10)} M${x} ${f(y + 8)} L${f(x - 8)} ${f(y + 20)} M${x} ${f(y + 8)} L${f(x + 8)} ${f(y + 20)}"/>`;
      break;
    case "phone":
      g = `<rect x="${f(x - 10)}" y="${f(y - 19)}" width="20" height="38" rx="4"/><circle class="f" cx="${x}" cy="${f(y + 13)}" r="1.9"/>`;
      break;
    case "screen":
      g = `<rect x="${f(x - 19)}" y="${f(y - 16)}" width="38" height="25" rx="2"/><path d="M${f(x - 7)} ${f(y + 17)} H${f(x + 7)} M${x} ${f(y + 9)} V${f(y + 17)}"/>`;
      break;
    case "cyl": {
      const ry = 5, top = t + ry, bot = t + h - ry;
      g = `<path d="M${l} ${f(top)} V${f(bot)} A${f(w / 2)} ${ry} 0 0 0 ${f(l + w)} ${f(bot)} V${f(top)}"/><ellipse cx="${x}" cy="${f(top)}" rx="${f(w / 2)}" ry="${ry}"/>`;
      break;
    }
    case "cloud": {
      const r = h * 0.36, cy = y + h * 0.12;
      g = `<path d="M${f(l + r)} ${f(cy + r)} H${f(l + w - r)} A${f(r)} ${f(r)} 0 0 0 ${f(l + w - r * 0.4)} ${f(cy - r * 0.5)} A${f(r * 1.05)} ${f(r * 1.05)} 0 0 0 ${f(x + w * 0.12)} ${f(t + r * 0.6)} A${f(r * 1.25)} ${f(r * 1.25)} 0 0 0 ${f(x - w * 0.22)} ${f(t + r * 0.9)} A${f(r)} ${f(r)} 0 0 0 ${f(l + r * 0.4)} ${f(cy - r * 0.2)} A${f(r)} ${f(r)} 0 0 0 ${f(l + r)} ${f(cy + r)} Z"/>`;
      break;
    }
    case "circle":
      g = `<circle cx="${x}" cy="${y}" r="${f(w / 2)}"/>`;
      break;
    default:     // box and bar
      g = `<rect x="${l}" y="${t}" width="${w}" height="${h}" rx="${s.shape === "bar" ? 3 : 5}"/>`;
  }
  let text = "";
  if (s.text.length) {
    const lh = 13, mid = s.shape === "cyl" ? y + 3 : s.shape === "cloud" ? y + 4 : y, y0 = mid - ((s.text.length - 1) * lh) / 2 + 4;
    text = s.text.map((line, i) => `<text class="db-wb-t" x="${x}" y="${f(y0 + i * lh)}" text-anchor="middle">${esc(line)}</text>`).join("");
  }
  return { svg: `<g class="${cls} s-${s.shape}">${g}${text}</g>`, ...s };
}

// The parts list's tile: the empty shape, small, with the name beside it in the list.
export function tileArt(part) {
  const shape = shapeOf(part);
  const T = {
    person: `<circle cx="22" cy="12" r="5.5"/><path d="M22 17.5 V29 M13 22 H31 M22 29 L15 39 M22 29 L29 39"/>`,
    phone: `<rect x="14" y="5" width="16" height="34" rx="3.5"/><circle class="f" cx="22" cy="33.5" r="1.7"/>`,
    screen: `<rect x="5" y="8" width="34" height="22" rx="2"/><path d="M16 37 H28 M22 30 V37"/>`,
    cyl: `<path d="M8 12 V32 A14 4.5 0 0 0 36 32 V12"/><ellipse cx="22" cy="12" rx="14" ry="4.5"/>`,
    cloud: `<path d="M12 32 H33 A6.5 6.5 0 0 0 34 19.2 A8 8 0 0 0 20.5 14 A7 7 0 0 0 11 20.5 A6 6 0 0 0 12 32 Z"/>`,
    circle: `<circle cx="22" cy="22" r="13"/>`,
    bar: `<rect x="4" y="15" width="36" height="14" rx="2.5"/>`,
    box: `<rect x="7" y="10" width="30" height="24" rx="4"/>`,
  };
  return `<g class="db-wb">${T[shape] || T.box}</g>`;
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
