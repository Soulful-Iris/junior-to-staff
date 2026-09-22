import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mapLimit, latestOnly, LRU, reconcile } from './typescript.ts';

test('bounded concurrency, order, and rejection isolation', async () => {
  let active = 0, peak = 0;
  const result = await mapLimit([4,3,2,1],2,async value => {
    active++; peak=Math.max(active,peak);
    try {
      await new Promise(resolve=>setTimeout(resolve,value));
      if(value===3) throw new Error('test failure');
      return value*2;
    } finally { active--; }
  });
  assert.equal(peak,2);assert.equal(active,0);
  assert.deepEqual(result.map(x=>x.status==='fulfilled'?x.value:'error'),[8,'error',4,2]);
  assert.deepEqual(await mapLimit([],2,async x=>x),[]);
  await assert.rejects(mapLimit([1],0,async x=>x),RangeError);
});
test('stale result cannot render even if load ignores abort',async()=>{
  const pending: Record<string,(x:string)=>void> = {};
  const rendered:string[]=[];
  const search=latestOnly((q)=>new Promise<string>(r=>{pending[q]=r}),v=>rendered.push(v));
  const old=search('old'),fresh=search('new');
  pending.new('new');assert.equal(await fresh,true);
  pending.old('old');assert.equal(await old,false);
  assert.deepEqual(rendered,['new']);
});
test('current failure propagates',async()=>{
  const search=latestOnly(async()=>{throw new Error('offline')},()=>{});
  await assert.rejects(search('q'),/offline/);
});
test('LRU refresh, overwrite, and zero capacity',()=>{
  const c=new LRU<string,number>(2);c.put('a',1);c.put('b',2);c.get('a');c.put('c',3);
  assert.equal(c.get('b'),undefined);c.put('a',4);assert.equal(c.get('a'),4);
  const empty=new LRU(0);empty.put('a',1);assert.equal(empty.get('a'),undefined);
});
test('late response cannot regress version',()=>{
  const current={id:'a',title:'new',version:3};
  assert.equal(reconcile(current,{id:'a',title:'old',version:2}),current);
  assert.throws(()=>reconcile(current,{id:'b',title:'x',version:4}));
});
