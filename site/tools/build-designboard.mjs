// Bundle the design board for one release: node build-designboard.mjs <out-dir>
// Writes assets/designboard/board.<hash>.js and icons.<hash>.json, and prints a
// JSON manifest the page builder uses to reference the board, with
// subresource-integrity hashes.
//
// Parts are drawn by sketch.js first. AWS's own icons are the reader's second
// choice, so they are not in the bundle (with them as strings it was 401 KB,
// 125 KB gzipped; without, 171 KB, 53 KB): they sit beside it as one data
// file, and the bundle carries only that file's name and hash. The board
// fetches it the first time a reader picks AWS icons, and the browser refuses
// it if a byte differs from what this build wrote.
import { build } from "esbuild";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "..", "designboard");
const out = resolve(process.argv[2] || resolve(here, "..", "out"));
const dest = join(out, "assets", "designboard");
mkdirSync(dest, { recursive: true });

// The icons, exactly AWS's files, keyed by file name: the map the board used
// to have bundled in.
const catalog = JSON.parse(readFileSync(join(src, "catalog.json"), "utf8"));
const icons = {};
for (const p of [...catalog.parts, ...catalog.groups]) if (p.icon) icons[p.icon] = readFileSync(join(src, "icons", p.icon), "utf8");
const iconBytes = Buffer.from(JSON.stringify(icons));
const ih = createHash("sha256").update(iconBytes).digest();
const iconFile = `icons.${ih.toString("hex").slice(0, 16)}.json`;
writeFileSync(join(dest, iconFile), iconBytes);
const iconRef = { file: iconFile, integrity: "sha256-" + ih.toString("base64") };

// `import ICON_FILE from "designboard:icons"` in board.js: the name and hash,
// so a new set of icons is a new board file too.
const iconsPlugin = {
  name: "designboard-icons",
  setup(b) {
    b.onResolve({ filter: /^designboard:icons$/ }, () => ({ path: "icons", namespace: "designboard" }));
    b.onLoad({ filter: /.*/, namespace: "designboard" }, () => ({ contents: "export default " + JSON.stringify(iconRef), loader: "js" }));
  },
};

const bundle = await build({
  entryPoints: [join(src, "board.js")], bundle: true, format: "esm", minify: true,
  target: ["es2020"], loader: { ".css": "text", ".json": "json" }, write: false, legalComments: "eof",
  plugins: [iconsPlugin], nodePaths: [join(here, "node_modules")],
});
const bytes = Buffer.from(bundle.outputFiles[0].contents);
const h = createHash("sha256").update(bytes).digest();
const file = `board.${h.toString("hex").slice(0, 16)}.js`;
writeFileSync(join(dest, file), bytes);
process.stdout.write(JSON.stringify({
  js: { file: `assets/designboard/${file}`, integrity: "sha256-" + h.toString("base64") },
  icons: { file: `assets/designboard/${iconFile}`, integrity: iconRef.integrity },
}));
