// Node 24 strips supported TS syntax; this is deliberately not a type checker.
import { stripTypeScriptTypes } from 'node:module';
import { readFile, writeFile } from 'node:fs/promises';
const source = new URL('./web/app.ts', import.meta.url);
await writeFile(new URL('./web/app.js', import.meta.url), stripTypeScriptTypes(await readFile(source, 'utf8')));
console.log('Built web/app.js from web/app.ts (Node syntax stripping; use tsc --noEmit for types).');
