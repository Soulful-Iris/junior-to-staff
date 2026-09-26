// Bundle the code field for one release: node build-codefield.mjs <out-dir>
// Writes assets/codefield/{codefield,worker}.<hash>.js and harness.<hash>.py,
// and prints a JSON manifest the page builder uses to reference them, with a
// subresource-integrity hash for the module the pages load directly.
import { build } from "esbuild";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "..", "codefield");
const out = resolve(process.argv[2] || resolve(here, "..", "out"));
const dest = join(out, "assets", "codefield");
mkdirSync(dest, { recursive: true });

const hashed = (name, ext, bytes) => {
  const h = createHash("sha256").update(bytes).digest();
  const file = `${name}.${h.toString("hex").slice(0, 16)}.${ext}`;
  writeFileSync(join(dest, file), bytes);
  return { file: `assets/codefield/${file}`, integrity: "sha256-" + h.toString("base64") };
};

const bundle = await build({
  entryPoints: [join(src, "codefield.js")], bundle: true, format: "esm", minify: true,
  target: ["es2020"], loader: { ".css": "text" }, write: false, legalComments: "eof",
  nodePaths: [join(here, "node_modules")],   // the sources live beside tools/, not under it
});
const manifest = {
  js: hashed("codefield", "js", Buffer.from(bundle.outputFiles[0].contents)),
  worker: hashed("worker", "js", readFileSync(join(src, "worker.js"))),
  harness: hashed("harness", "py", readFileSync(join(src, "harness.py"))),
};
process.stdout.write(JSON.stringify(manifest));
