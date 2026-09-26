// Bundle the design board for one release: node build-designboard.mjs <out-dir>
// Writes assets/designboard/board.<hash>.js and prints a JSON manifest the
// page builder uses to reference it, with a subresource-integrity hash.
// The AWS icons the catalog names are bundled in, unmodified, as strings: the
// board only loads on pages that have a board, and one file is one thing that
// can fail to arrive rather than two.
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

const catalog = JSON.parse(readFileSync(join(src, "catalog.json"), "utf8"));
const icons = {};
for (const p of [...catalog.parts, ...catalog.groups]) if (p.icon) icons[p.icon] = readFileSync(join(src, "icons", p.icon), "utf8");

const iconsPlugin = {
  name: "designboard-icons",
  setup(b) {
    b.onResolve({ filter: /^designboard:icons$/ }, () => ({ path: "icons", namespace: "designboard" }));
    b.onLoad({ filter: /.*/, namespace: "designboard" }, () => ({ contents: "export default " + JSON.stringify(icons), loader: "js" }));
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
process.stdout.write(JSON.stringify({ js: { file: `assets/designboard/${file}`, integrity: "sha256-" + h.toString("base64") } }));
