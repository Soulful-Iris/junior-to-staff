// Run: node tests/browser.mjs. Uses installed playwright or the Work runtime copy.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import {mkdtemp, mkdir, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require = createRequire(import.meta.url);
const {chromium} = require(require.resolve('playwright', {paths: [process.cwd(), process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES || process.cwd()]}));
const root = fileURLToPath(new URL('../', import.meta.url));
const temp = await mkdtemp(path.join(tmpdir(), 'bookmark-browser-'));
const server = spawn(process.env.CODEX_PRIMARY_RUNTIME_PYTHON || 'python3', ['server.py', '--port', '0', '--db', path.join(temp, 'data.db')], {cwd: root});
const base = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('server startup timeout')), 5000);
  server.stdout.on('data', data => {const match = String(data).match(/http:\/\/127\.0\.0\.1:\d+/); if (match) {clearTimeout(timer); resolve(match[0]);}});
  server.on('error', reject);
});
const launch = {headless:true};
if (process.env.BOOKMARK_CHROMIUM_PATH) {
  launch.executablePath = process.env.BOOKMARK_CHROMIUM_PATH;
  launch.args = ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--single-process', '--no-zygote'];
}
const browser = await chromium.launch(launch);
const context = await browser.newContext({viewport:{width:1100,height:900}});
const auth = {Authorization:'Bearer alice-local-token'};
const json = async (url, options = {}) => {
  const response = await fetch(base + url, {headers: auth, ...options});
  return {status: response.status, body: await response.json()};
};
async function setTitle(title) {
  const {body: old} = await json('/api/bookmarks/b');
  return json('/api/bookmarks/b', {method:'PATCH', headers:{...auth,'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()}, body:JSON.stringify({title,expectedVersion:old.version})});
}
function deferred() {let resolve; const promise = new Promise(r => {resolve = r;}); return {promise, resolve};}
async function newPage() {
  await setTitle('Beta');
  const page = await context.newPage();
  page.on('pageerror', error => console.error('BROWSER ERROR', error.message));
  await page.goto(base);
  await page.getByRole('button', {name:'Edit Beta', exact:true}).waitFor();
  return page;
}
async function textIs(page, selector, expected) {
  await page.waitForFunction(({selector, expected}) => document.querySelector(selector)?.textContent.includes(expected), {selector,expected});
}
async function open(page) {await page.getByRole('button',{name:'Edit Beta',exact:true}).click();}
let checks = 0;
async function check(name, fn) {await fn(); checks++; console.log(`PASS ${name}`);}
try {
  await check('save A preserves newer draft B', async () => {
    const page = await newPage(); await open(page);
    const caught = deferred(), release = deferred();
    await page.route('**/api/bookmarks/b', async route => {
      if(route.request().method() !== 'PATCH') return route.continue();
      const response = await route.fetch(); caught.resolve(); await release.promise; await route.fulfill({response});
    });
    await page.getByLabel('Title',{exact:true}).fill('Edit A');
    await page.getByRole('button',{name:'Save title',exact:true}).click(); await caught.promise;
    await page.getByLabel('Title',{exact:true}).fill('Edit B'); release.resolve();
    await textIs(page,'#edit-status','newer draft is unsaved');
    assert.equal(await page.getByLabel('Title',{exact:true}).inputValue(),'Edit B');
    assert.equal((await json('/api/bookmarks/b')).body.title,'Edit A');
    await mkdir(path.join(root,'tests/artifacts'),{recursive:true});
    await page.screenshot({path:path.join(root,'tests/artifacts/draft-preserved.png'),fullPage:true});
    await page.close();
  });
  await check('409 retains B; keyboard conflict recovery has focus and live status', async () => {
    const page = await newPage(); await open(page);
    const caught = deferred(), release = deferred();
    await page.route('**/api/bookmarks/b', async route => {
      if(route.request().method() !== 'PATCH') return route.continue();
      caught.resolve(); await release.promise; await route.continue();
    });
    await page.getByLabel('Title',{exact:true}).fill('Edit A');
    await page.getByLabel('Title',{exact:true}).press('Enter'); await caught.promise;
    await page.getByLabel('Title',{exact:true}).fill('Edit B');
    await setTitle('External edit'); release.resolve();
    await textIs(page,'#edit-status','Conflict.');
    assert.equal(await page.getByLabel('Title',{exact:true}).inputValue(),'Edit B');
    assert.equal(await page.locator('#resolve').evaluate(el=>el===document.activeElement),true);
    assert.equal(await page.locator('#edit-status').getAttribute('role'),'status');
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#title').evaluate(el=>el===document.activeElement),true);
    await page.unroute('**/api/bookmarks/b');
    await page.keyboard.press('Enter'); await textIs(page,'#edit-status','Saved.');
    assert.equal((await json('/api/bookmarks/b')).body.title,'Edit B');
    await page.close();
  });
  await check('old refetch cannot replace confirmed version or unsaved draft', async () => {
    const page = await newPage(); await open(page);
    const caught = deferred(), release = deferred();
    await page.route('**/api/bookmarks/b', async route => {
      if(route.request().method() !== 'GET') return route.continue();
      const response = await route.fetch(); caught.resolve(); await release.promise; await route.fulfill({response});
    });
    await page.getByRole('button',{name:'Refresh server copy'}).click(); await caught.promise;
    await page.getByLabel('Title',{exact:true}).fill('New confirmed');
    await page.getByRole('button',{name:'Save title',exact:true}).click(); await textIs(page,'#edit-status','Saved.');
    await page.getByLabel('Title',{exact:true}).fill('Unsaved next'); release.resolve();
    await textIs(page,'#edit-status','Server copy unchanged');
    assert.equal(await page.getByLabel('Title',{exact:true}).inputValue(),'Unsaved next');
    assert.match(await page.locator('#confirmed').textContent(),/New confirmed/);
    await page.close();
  });
  await check('lost acknowledgement retries same key and duplicate response increments once', async () => {
    const page = await newPage(); await open(page);
    const before = (await json('/api/bookmarks/b')).body.version;
    let first = true; const keys = [];
    await page.route('**/api/bookmarks/b', async route => {
      if(route.request().method() !== 'PATCH') return route.continue();
      keys.push(route.request().headers()['idempotency-key']);
      const response = await route.fetch();
      if(first) {first=false; return route.abort('failed');}
      await route.fulfill({response});
    });
    await page.getByLabel('Title',{exact:true}).fill('Edit A');
    await page.getByRole('button',{name:'Save title',exact:true}).click();
    await textIs(page,'#edit-status','outcome unavailable');
    await page.getByLabel('Title',{exact:true}).fill('Edit B');
    await page.getByRole('button',{name:'Retry save',exact:true}).click();
    await textIs(page,'#edit-status','newer draft is unsaved');
    assert.equal(keys.length,2); assert.equal(keys[0],keys[1]);
    assert.equal((await json('/api/bookmarks/b')).body.version,before+1);
    assert.equal(await page.getByLabel('Title',{exact:true}).inputValue(),'Edit B');
    await page.close();
  });
  await check('close disposes editor even when transport ignores abort; focus returns', async () => {
    const page = await newPage(); await open(page);
    await page.evaluate(()=>{const original=window.fetch;window.fetch=(url,options)=>original(url,{...options,signal:undefined});});
    const caught = deferred(), release = deferred(), delivered = deferred();
    await page.route('**/api/bookmarks/b', async route => {
      if(route.request().method() !== 'PATCH') return route.continue();
      const response=await route.fetch();caught.resolve();await release.promise;await route.fulfill({response});delivered.resolve();
    });
    await page.getByLabel('Title',{exact:true}).fill('Late edit');
    await page.getByRole('button',{name:'Save title',exact:true}).click();await caught.promise;
    await page.getByRole('button',{name:'Close editor'}).click();
    assert.equal(await page.locator('#editor').isHidden(),true);
    assert.equal(await page.getByRole('button',{name:'Edit Beta',exact:true}).evaluate(el=>el===document.activeElement),true);
    release.resolve();await delivered.promise;
    await page.getByRole('button',{name:'Edit Alpha',exact:true}).click();
    assert.equal(await page.getByLabel('Title',{exact:true}).inputValue(),'Alpha');
    await page.close();
  });
  await check('search race ignores older response; empty, error and keyboard retry work', async () => {
    const page = await newPage();
    await page.evaluate(()=>{const original=window.fetch;window.fetch=(url,options)=>original(url,{...options,signal:undefined});});
    const caught=deferred(), release=deferred(), delivered=deferred();
    await page.route('**/api/bookmarks?*', async route=>{
      if(new URL(route.request().url()).searchParams.get('q')!=='Alpha')return route.continue();
      const response=await route.fetch();caught.resolve();await release.promise;await route.fulfill({response});delivered.resolve();
    });
    await page.getByLabel('Search bookmarks').fill('Alpha');await page.getByLabel('Search bookmarks').press('Enter');await caught.promise;
    await page.getByLabel('Search bookmarks').fill('Beta');await page.getByLabel('Search bookmarks').press('Enter');
    await textIs(page,'#list-status','1 bookmarks');release.resolve();await delivered.promise;
    assert.equal(await page.getByRole('button',{name:'Edit Beta',exact:true}).count(),1);
    assert.equal(await page.getByRole('button',{name:'Edit Alpha',exact:true}).count(),0);
    await page.unroute('**/api/bookmarks?*');
    await page.getByLabel('Search bookmarks').fill('none-match');await page.getByLabel('Search bookmarks').press('Enter');
    await textIs(page,'#list-status','No bookmarks');
    await page.route('**/api/bookmarks?*',route=>route.fulfill({status:503,contentType:'application/json',body:'{"error":"injected outage"}'}));
    await page.getByLabel('Search bookmarks').fill('');await page.getByLabel('Search bookmarks').press('Enter');
    await textIs(page,'#list-status','Search failed');await page.unroute('**/api/bookmarks?*');
    await page.getByRole('button',{name:'Retry search'}).focus();await page.keyboard.press('Enter');await textIs(page,'#list-status','2 bookmarks');
    await page.getByRole('button',{name:'Load more'}).focus();await page.keyboard.press('Enter');await textIs(page,'#list-status','3 bookmarks');
    assert.equal(await page.locator('#results li').count(),3);
    assert.equal(await page.getByRole('button',{name:'Edit Bob private',exact:true}).count(),0);
    await page.close();
  });
  await check('failed new search cannot reuse an old query cursor', async () => {
    const page = await newPage();
    assert.equal(await page.locator('#more').isVisible(),true);
    await page.route('**/api/bookmarks?*',route=>route.fulfill({status:503,contentType:'application/json',body:'{"error":"injected outage"}'}));
    await page.getByLabel('Search bookmarks').fill('Gamma');
    await page.getByLabel('Search bookmarks').press('Enter');
    await textIs(page,'#list-status','Search failed');
    assert.equal(await page.locator('#more').isHidden(),true);
    assert.equal(await page.locator('#results li').count(),0);
    await page.unroute('**/api/bookmarks?*');
    const next = page.waitForRequest(request=>request.url().includes('/api/bookmarks?'));
    await page.getByRole('button',{name:'Retry search'}).click();
    const request = await next;
    assert.equal(new URL(request.url()).searchParams.get('cursor'),null);
    await textIs(page,'#list-status','1 bookmarks');
    assert.equal(await page.getByRole('button',{name:'Edit Gamma',exact:true}).count(),1);
    assert.equal(await page.getByRole('button',{name:'Edit Beta',exact:true}).count(),0);
    await page.close();
  });
  console.log(`${checks} browser scenarios passed against real HTTP + SQLite.`);
} finally {
  await browser.close(); server.kill('SIGTERM');
  await new Promise(resolve=>server.once('exit',resolve));
  await rm(temp,{recursive:true,force:true});
}
