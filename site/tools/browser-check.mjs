/* Exercise the reader as a learner: order, context, mobile navigation and recovery. */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '../..');
const shots = process.env.SITE_SCREENSHOTS || mkdtempSync(join(tmpdir(),'engineering-reader-'));
mkdirSync(shots,{recursive:true});
const server=spawn(process.env.PYTHON || 'python',['site/serve.py','8907'],{cwd:root,stdio:['ignore','pipe','pipe']});
const address='http://127.0.0.1:8907';
let browser;
const failures=[]; let passed=0;
try {
  await new Promise((resolve,reject)=>{server.stdout.once('data',resolve);server.once('error',reject);server.once('exit',code=>reject(Error('Server exited '+code)));});
  browser=await chromium.launch({executablePath:process.env.CHROME_PATH || undefined,args:['--no-sandbox','--disable-dev-shm-usage']});
  const context=await browser.newContext({viewport:{width:1440,height:1050}});
  const page=await context.newPage();const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  async function check(name, fn){await fn();passed++;console.log('PASS '+name);}
  async function go(path='/'){await page.goto(address+path);await page.evaluate(()=>document.fonts.ready);}
  const maps='/curriculum/01-code/02-data-structures-algorithms/lessons/01-maps.html';
  const sum='/curriculum/01-code/02-data-structures-algorithms/problems/01-two-sum/';
  await check('Homepage explains the journey and shows the full nested contents',async()=>{
    await go();assert.match(await page.locator('h1').textContent(),/Build the judgment/);
    assert.equal(await page.locator('.toc-area:not(.reference-area)').count(),4);
    assert.equal(await page.locator('.toc-area:not(.reference-area) .toc-chapter').count(),17);
    assert.equal(await page.locator('.toc-area h2').first().evaluate(e=>getComputedStyle(e).fontSize),'10px');
    assert.equal(await page.locator('.lesson-body a:not([data-start])').count(),0);
    await page.screenshot({path:join(shots,'home-desktop.png'),fullPage:true});
  });
  await check('A primer leads directly to its problem, with references inside the lesson',async()=>{
    await go(maps);assert.equal(await page.locator('.next-step').getAttribute('href'),sum);
    await page.locator('.next-step').click();await page.waitForURL(address+sum);
    assert.match(await page.locator('h1').textContent(),/Two sum/);
    assert.equal(await page.locator('.lesson-body details').first().getAttribute('open'),null);
    assert.equal(await page.locator('figure.code-file[data-source$="/solution.py"]').count(),1);
    assert.equal(await page.locator('figure.code-file[data-source$="test_solution.py"]').count(),1);
    await page.screenshot({path:join(shots,'problem-desktop.png'),fullPage:true});
  });
  await check('Subsection navigation reveals its closed answer and keeps the same page',async()=>{
    const follow=page.locator('[data-heading]').filter({hasText:'Follow-up 1'}).first();
    await follow.click();assert.ok(await page.locator('.lesson-body details').first().evaluate(e=>e.open));
    assert.ok(page.url().startsWith(address+sum+'#'));
    await page.waitForFunction(()=>[...document.querySelectorAll('h3')].some(e=>e.textContent.includes('Follow-up 1')&&e.getBoundingClientRect().top>50&&e.getBoundingClientRect().top<180));
    await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await page.screenshot({path:join(shots,'worked-lesson-desktop.png'),fullPage:true});
  });
  await check('Previous and Next agree, and progress resumes on the homepage',async()=>{
    await page.locator('.previous-step').click();await page.waitForURL(address+maps);
    await go();assert.match(await page.locator('[data-start]').textContent(),/Continue learning/);
    assert.equal(await page.locator('[data-start]').getAttribute('href'),maps);
    const completed=await page.evaluate(()=>JSON.parse(localStorage.getItem('engineering-guide:progress:v1')).completed);
    assert.ok(completed.some(s=>s.endsWith('lessons/01-maps.md')));
  });
  await check('Search stays in the left panel and clearing it restores the complete tree',async()=>{
    await page.keyboard.press('/');assert.equal(await page.locator('#contents-search').evaluate(e=>document.activeElement===e),true);
    await page.locator('#contents-search').fill('binary search');await page.locator('#search-results a').first().waitFor();
    assert.ok((await page.locator('#search-results a').count())>0);assert.equal(await page.locator('#contents-tree').isVisible(),false);
    await page.locator('#contents-search').fill('');assert.equal(await page.locator('#contents-tree').isVisible(),true);
  });
  await check('Motion has an authored still and a persistent manual control',async()=>{
    await go(maps);await page.locator('#motion-toggle').click();
    assert.ok((await page.locator('img[data-motion]').first().getAttribute('src')).endsWith('-still.svg'));
    await page.reload();assert.equal(await page.locator('#motion-toggle').getAttribute('aria-pressed'),'true');
    await go();assert.match(await page.locator('.featured-diagram img').getAttribute('src'),/assets\/resting/);
    assert.equal(await page.locator('.featured-diagram img').evaluate(e=>e.complete&&e.naturalWidth>0),true);
  });
  await check('Desktop chapter navigation stays available and never overflows the page',async()=>{
    await go('/curriculum/02-applications/01-backend/request-lifecycle.html');
    assert.equal(await page.locator('.identity').isVisible(),true);
    assert.ok(await page.locator('.identity').evaluate(e=>e.getBoundingClientRect().top>=0));
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.screenshot({path:join(shots,'backend-desktop.png'),fullPage:true});
  });
  await check('Mobile contents opens, traps focus, closes on Escape and returns focus',async()=>{
    await page.setViewportSize({width:390,height:844});await go();
    assert.equal(await page.locator('#sidebar').evaluate(e=>e.inert),true);
    await page.locator('#open-contents').click();assert.equal(await page.locator('#open-contents').getAttribute('aria-expanded'),'true');
    assert.equal(await page.locator('.reading-shell').evaluate(e=>e.inert),true);
    await page.locator('#dismiss-contents').focus();await page.keyboard.press('Shift+Tab');
    assert.equal(await page.locator('#sidebar').evaluate(e=>e.contains(document.activeElement)),true);
    await page.waitForFunction(()=>Math.abs(document.getElementById('sidebar').getBoundingClientRect().x)<1);await page.screenshot({path:join(shots,'mobile-contents.png')});
    await page.keyboard.press('Escape');assert.equal(await page.locator('#sidebar').evaluate(e=>e.inert),true);
    assert.equal(await page.locator('#open-contents').evaluate(e=>document.activeElement===e),true);
  });
  await check('Mobile reading keeps tables and diagrams inside their own scroll areas',async()=>{
    for(const path of ['/',maps,sum,'/curriculum/04-scale-and-evolution/03-ai-systems/evaluation-and-budgets.html']){
      await go(path);await page.locator('.lesson-body details').evaluateAll(ds=>ds.forEach(d=>d.open=true));
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),path);
    }
    await page.screenshot({path:join(shots,'ai-mobile.png'),fullPage:true});
    await go();await page.screenshot({path:join(shots,'home-mobile.png'),fullPage:true});
  });
  await check('System reduced-motion preference displays static visuals immediately',async()=>{
    const c=await browser.newContext({reducedMotion:'reduce'});const p=await c.newPage();await p.goto(address+maps);
    assert.match(await p.locator('img[data-motion]').first().getAttribute('src'),/-still.svg$/);await c.close();
  });
  await check('Reading and navigation survive unavailable local storage',async()=>{
    const c=await browser.newContext();await c.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new Error('Unavailable storage');}});});
    const p=await c.newPage();const e=[];p.on('pageerror',x=>e.push(x.message));await p.goto(address+sum);
    await p.locator('.next-step').click();await p.waitForURL(/02-valid-anagram/);assert.deepEqual(e,[]);await c.close();
  });
  await check('Browser console has no uncaught application errors',async()=>assert.deepEqual(errors,[]));
  console.log(`${passed} browser scenarios passed. Screenshots: ${shots}`);
} catch(e){failures.push(String(e));console.error(e);process.exitCode=1;}
finally{if(browser)await browser.close();server.kill();}
