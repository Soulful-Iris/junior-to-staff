(() => {
  'use strict';
  const base = window.SITE_BASE || '/';
  // ---------------------------------------------------------------- private track lock
  // Locked content ships as ciphertext. The password derives a key (PBKDF2-SHA256);
  // an HMAC tag proves the key before anything is shown; the keystream is PBKDF2
  // with one iteration, which is HMAC-SHA256 in counter mode. The derived key,
  // not the password, is kept in a cookie so the unlock survives navigation.
  const LOCK={cookie:'j2s_track',salt:'engineering-guide:private-track:v1',iterations:120000,chunk:32768};
  const utf8=s=>new TextEncoder().encode(s);
  const hex=bytes=>[...bytes].map(b=>b.toString(16).padStart(2,'0')).join('');
  const unhex=s=>Uint8Array.from(s.match(/../g),h=>parseInt(h,16));
  const unb64=s=>{const bin=atob(s);const out=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);return out;};
  const concat=(...parts)=>{const out=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let o=0;for(const p of parts){out.set(p,o);o+=p.length;}return out;};
  const be32=n=>new Uint8Array([n>>>24,n>>>16&255,n>>>8&255,n&255]);
  const subtle=(typeof crypto!=='undefined'&&crypto.subtle)||null;
  // Plain-JS SHA-256, HMAC and PBKDF2 for a page served without HTTPS, where WebCrypto is absent.
  const K256=new Uint32Array([0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);
  function sha256(bytes){
    const l=bytes.length,padded=new Uint8Array(((l+9+63)>>6)<<6);padded.set(bytes);padded[l]=0x80;
    const dv=new DataView(padded.buffer);dv.setUint32(padded.length-4,(l*8)>>>0);dv.setUint32(padded.length-8,Math.floor(l/0x20000000));
    const h=new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]);const w=new Uint32Array(64);
    for(let p=0;p<padded.length;p+=64){
      for(let i=0;i<16;i++)w[i]=dv.getUint32(p+i*4);
      for(let i=16;i<64;i++){const a=w[i-15],b=w[i-2];w[i]=(w[i-16]+(((a>>>7)|(a<<25))^((a>>>18)|(a<<14))^(a>>>3))+w[i-7]+(((b>>>17)|(b<<15))^((b>>>19)|(b<<13))^(b>>>10)))>>>0;}
      let a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
      for(let i=0;i<64;i++){
        const t1=(hh+(((e>>>6)|(e<<26))^((e>>>11)|(e<<21))^((e>>>25)|(e<<7)))+((e&f)^(~e&g))+K256[i]+w[i])>>>0;
        const t2=((((a>>>2)|(a<<30))^((a>>>13)|(a<<19))^((a>>>22)|(a<<10)))+((a&b)^(a&c)^(b&c)))>>>0;
        hh=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
      }
      h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;
    }
    const out=new Uint8Array(32),ov=new DataView(out.buffer);h.forEach((v,i)=>ov.setUint32(i*4,v));return out;
  }
  function hmacJS(key,data){
    if(key.length>64)key=sha256(key);
    const k=new Uint8Array(64);k.set(key);
    return sha256(concat(k.map(b=>b^0x5c),sha256(concat(k.map(b=>b^0x36),data))));
  }
  function pbkdf2JS(pw,salt,iterations,length){
    const out=new Uint8Array(length);
    for(let block=1,off=0;off<length;block++){
      let u=hmacJS(pw,concat(salt,be32(block)));const t=u.slice();
      for(let i=1;i<iterations;i++){u=hmacJS(pw,u);for(let j=0;j<32;j++)t[j]^=u[j];}
      out.set(t.subarray(0,Math.min(32,length-off)),off);off+=32;
    }
    return out;
  }
  async function derive(secret,salt,iterations,length){
    if(!subtle)return pbkdf2JS(secret,salt,iterations,length);
    const k=await subtle.importKey('raw',secret,'PBKDF2',false,['deriveBits']);
    return new Uint8Array(await subtle.deriveBits({name:'PBKDF2',hash:'SHA-256',salt,iterations},k,length*8));
  }
  async function verify(macKey,data,tag){
    if(!subtle){const t=hmacJS(macKey,data);return t.length===tag.length&&t.every((b,i)=>b===tag[i]);}
    const k=await subtle.importKey('raw',macKey,{name:'HMAC',hash:'SHA-256'},false,['verify']);
    return subtle.verify('HMAC',k,tag,data);
  }
  const keyFor=password=>derive(utf8(password),utf8(LOCK.salt),LOCK.iterations,64);
  async function openBlob(key,b64){
    const raw=unb64(b64.replace(/\s+/g,''));const nonce=raw.subarray(0,16),tag=raw.subarray(16,48),cipher=raw.subarray(48);
    if(!await verify(key.subarray(32),concat(nonce,cipher),tag))return null;
    const out=new Uint8Array(cipher.length);
    for(let chunk=0,off=0;off<cipher.length;chunk++){
      const n=Math.min(LOCK.chunk,cipher.length-off);
      const ks=await derive(key.subarray(0,32),concat(nonce,be32(chunk)),1,n);
      for(let i=0;i<n;i++)out[off+i]=cipher[off+i]^ks[i];
      off+=n;
    }
    return new TextDecoder().decode(out);
  }
  const blobOf=el=>el.querySelector('.track-lock-blob').textContent;
  function savedKey(){const m=document.cookie.match(/(?:^|;\s*)j2s_track=v1\.([0-9a-f]{128})(?:;|$)/);return m?unhex(m[1]):null;}
  function saveKey(key){document.cookie=`${LOCK.cookie}=v1.${hex(key)}; Max-Age=31536000; Path=${base}; SameSite=Strict${location.protocol==='https:'?'; Secure':''}`;}
  function forgetKey(){document.cookie=`${LOCK.cookie}=; Max-Age=0; Path=${base}; SameSite=Strict`;}
  // 'page': this document is being replaced by the unlocked one. true: locks replaced in place.
  async function reveal(key){
    const locks=[...document.querySelectorAll('.track-lock')];
    const page=locks.find(el=>el.dataset.lock==='page');
    if(page){
      const html=await openBlob(key,blobOf(page));if(html===null)return false;
      document.open();document.write(html);document.close();return 'page';
    }
    const opened=[];
    for(const el of locks){const html=await openBlob(key,blobOf(el));if(html===null)return false;opened.push([el,html]);}
    opened.forEach(([el,html])=>{el.outerHTML=html;});
    return true;
  }
  async function lockInit(){
    const root=document.documentElement;
    if(!document.querySelector('.track-lock')){root.classList.remove('lock-checking');return false;}
    const key=savedKey();
    if(key){
      try{const done=await reveal(key);if(done==='page')return true;if(!done)forgetKey();}
      catch{forgetKey();}
    }
    root.classList.remove('lock-checking');
    document.querySelectorAll('.track-lock').forEach(el=>{
      const form=el.querySelector('form'),input=form.querySelector('input'),note=form.querySelector('.track-lock-note');
      form.addEventListener('submit',async e=>{
        e.preventDefault();
        el.classList.remove('is-wrong');el.classList.add('is-busy');note.textContent='Checking…';
        await new Promise(r=>setTimeout(r,30));
        try{
          const candidate=await keyFor(input.value);
          if(await openBlob(candidate,blobOf(el))===null){
            el.classList.remove('is-busy');el.classList.add('is-wrong');
            note.textContent='That password did not open it. Try again.';input.select();return;
          }
          saveKey(candidate);note.textContent='Unlocked. Opening…';
          if(await reveal(candidate)!=='page')location.reload();
        }catch{el.classList.remove('is-busy');note.textContent='Unlock failed in this browser. Reload and try again.';}
      });
    });
    return false;
  }
  async function main(){
  if(await lockInit())return;
  const state = JSON.parse(document.getElementById('page-state').textContent);
  const key = 'engineering-guide:progress:v1';
  function read(key, fallback, valid) {
    try {
      const raw = localStorage.getItem(key);
      if (raw === null) return fallback;
      const value = JSON.parse(raw);
      return valid(value) ? value : fallback;
    } catch { return fallback; }
  }
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  function progressValue(value) {
    return object(value) && Array.isArray(value.completed) && value.completed.length <= 10000
      && value.completed.every(src => typeof src === 'string' && src.length <= 1000)
      && (value.last === null || (object(value.last) && typeof value.last.url === 'string'
        && value.last.url.length <= 2000 && typeof value.last.title === 'string' && value.last.title.length <= 1000));
  }
  function write(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Reading works without storage. */ } }
  const saved = read(key, {completed: [], last: null}, progressValue);
  const progress = {completed: [...new Set(saved.completed)], last: saved.last};
  if (state.position !== null && state.position > 0) {
    progress.last = {url: state.url, title: state.title, private: !!state.private}; write(key, progress);
  }
  document.querySelectorAll('[data-page]').forEach(a => {
    if (progress.completed.includes(a.dataset.page)) a.classList.add('completed');
  });
  const starts = [...document.querySelectorAll('[data-start]')];
  // A resume pointer into the private track is shown only while the track is unlocked here.
  if (starts.length && progress.last && typeof progress.last.url === 'string' && progress.last.url.startsWith(base) && !progress.last.url.startsWith('//') && (!progress.last.private || savedKey())) {
    starts.forEach(start => {
      start.href = progress.last.url;
      start.textContent = 'Continue learning ';
      const arrow = document.createElement('span');arrow.setAttribute('aria-hidden','true');arrow.textContent = '↗';start.append(arrow);
    });
    document.querySelectorAll('[data-resume-label]').forEach(label => { label.textContent = 'Resume: ' + progress.last.title; });
  }
  function complete(src) {
    if (!progress.completed.includes(src)) progress.completed.push(src);
    write(key, progress);
  }
  document.querySelectorAll('[data-complete]').forEach(a => a.addEventListener('click', () => complete(a.dataset.complete)));
  const finishButtons = [...document.querySelectorAll('[data-finish]')];
  function showFinished() {
    finishButtons.forEach(button => {
      button.textContent = 'Completed ✓';
      button.setAttribute('aria-label', 'Final step completed');
      button.disabled = true;
    });
  }
  if (progress.completed.includes(state.src)) showFinished();
  finishButtons.forEach(button => button.addEventListener('click', () => {
    complete(state.src);showFinished();
  }));
  document.getElementById('reset-progress')?.addEventListener('click', () => {
    // Local, reversible learning preferences; never touches lesson content.
    write(key, {completed: [], last: null}); location.reload();
  });
  const sidebar = document.getElementById('sidebar');
  const openers = [...document.querySelectorAll('[data-open-contents]')];
  const opener = document.getElementById('open-contents');
  let lastOpener = opener;
  const backdrop = document.getElementById('close-contents');
  const mobile = () => matchMedia('(max-width: 760px)').matches;
  const drawerMode = () => mobile() || document.body.classList.contains('home');
  function setDrawer(open) {
    document.body.classList.toggle('contents-open', open);
    openers.forEach(button => button.setAttribute('aria-expanded', String(open))); backdrop.hidden = !open;
    if (drawerMode()) sidebar.inert = !open;
    document.querySelector('.reading-shell').inert = open && drawerMode();
    document.body.style.overflow = open && drawerMode() ? 'hidden' : '';
    if (open) document.getElementById('dismiss-contents').focus(); else lastOpener?.focus();
  }
  openers.forEach(button => button.addEventListener('click', () => {lastOpener=button;setDrawer(true);}));
  backdrop.addEventListener('click', () => setDrawer(false));
  document.getElementById('dismiss-contents').addEventListener('click', () => setDrawer(false));
  if (drawerMode()) sidebar.inert = true;
  matchMedia('(max-width: 760px)').addEventListener('change', () => {
    document.body.classList.remove('contents-open');openers.forEach(button=>button.setAttribute('aria-expanded','false'));backdrop.hidden=true;
    sidebar.inert=drawerMode();document.querySelector('.reading-shell').inert=false;document.body.style.overflow='';
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.body.classList.contains('contents-open')) setDrawer(false);
    if (e.key === 'Tab' && document.body.classList.contains('contents-open')) {
      const focusable = [...sidebar.querySelectorAll('button,a,input,summary')].filter(el => el.getClientRects().length);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {e.preventDefault();last.focus();}
      if (!e.shiftKey && document.activeElement === last) {e.preventDefault();first.focus();}
    }
    if (e.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {
      e.preventDefault();if(mobile())setDrawer(true);document.getElementById('contents-search').focus();
    }
  });
  document.getElementById('collapse-contents').addEventListener('click', () => sidebar.querySelectorAll('details').forEach(d => d.open = false));
  const active = sidebar.querySelector('[aria-current="page"]');
  if (active && state.position > 0) document.getElementById('contents-tree').scrollTop = Math.max(0, active.offsetTop - document.getElementById('contents-tree').offsetTop - document.getElementById('contents-tree').clientHeight * .30);
  const headingLinks = [...document.querySelectorAll('[data-heading]')];
  function revealHeading(id) {
    const node = document.getElementById(id); if (!node) return;
    for(let p=node.parentElement;p;p=p.parentElement) if(p.tagName==='DETAILS')p.open=true;
    return node;
  }
  headingLinks.forEach(a => a.addEventListener('click', e => {
    const node=revealHeading(a.dataset.heading);if(!node)return;e.preventDefault();
    if(mobile())setDrawer(false);
    history.replaceState(null,'','#'+encodeURIComponent(a.dataset.heading));node.tabIndex=-1;node.focus({preventScroll:true});node.scrollIntoView({block:'start'});
  }));
  if(location.hash) {try{const node=revealHeading(decodeURIComponent(location.hash.slice(1)));if(node)requestAnimationFrame(()=>node.scrollIntoView());}catch{/* An invalid old bookmark must not break the reader. */}}
  const sampleTabs=[...document.querySelectorAll('[data-sample-tab]')];
  const samplePanels=[...document.querySelectorAll('[data-sample-panel]')];
  function restartSampleAnimation(panel){
    if(!panel)return;
    panel.classList.remove('sample-animate');
    void panel.offsetWidth;
    panel.classList.add('sample-animate');
  }
  function showSample(name, moveFocus=false){
    sampleTabs.forEach(tab=>{
      const selected=tab.dataset.sampleTab===name;
      tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1;
      if(selected&&moveFocus)tab.focus();
    });
    samplePanels.forEach(panel=>{
      const selected=panel.dataset.samplePanel===name;
      panel.classList.toggle('active',selected);panel.setAttribute('aria-hidden',String(!selected));panel.inert=!selected;
    });
    restartSampleAnimation(samplePanels.find(panel=>panel.dataset.samplePanel===name));
  }
  sampleTabs.forEach((tab,index)=>{
    tab.addEventListener('click',()=>showSample(tab.dataset.sampleTab));
    tab.addEventListener('keydown',event=>{
      let target;
      if(event.key==='ArrowRight')target=(index+1)%sampleTabs.length;
      if(event.key==='ArrowLeft')target=(index-1+sampleTabs.length)%sampleTabs.length;
      if(event.key==='Home')target=0;
      if(event.key==='End')target=sampleTabs.length-1;
      if(target===undefined)return;
      event.preventDefault();showSample(sampleTabs[target].dataset.sampleTab,true);
    });
  });
  document.querySelectorAll('[data-sample-next]').forEach(button=>button.addEventListener('click',()=>showSample(button.dataset.sampleNext,true)));
  const observer = new IntersectionObserver(entries => {
    const hit=entries.find(e=>e.isIntersecting);if(!hit)return;
    headingLinks.forEach(a => a.classList.toggle('current-heading',a.dataset.heading===hit.target.id));
  },{rootMargin:'-110px 0px -60% 0px'});
  headingLinks.forEach(a=>{const node=document.getElementById(a.dataset.heading);if(node)observer.observe(node);});
  const progressBar=document.querySelector('.read-progress span');
  function updateScroll(){const max=document.documentElement.scrollHeight-innerHeight;progressBar.style.width=(max>0?Math.min(100,scrollY/max*100):0)+'%';}
  addEventListener('scroll',updateScroll,{passive:true});addEventListener('resize',updateScroll);updateScroll();
  const media=matchMedia('(prefers-reduced-motion: reduce)');
  const boolean = value => typeof value === 'boolean';
  let still=read('engineering-guide:still',media.matches,boolean);
  const motionButton=document.getElementById('motion-toggle');
  function applyMotion(){
    document.querySelectorAll('img[data-motion]').forEach(img=>{img.src=still?img.dataset.still:img.dataset.motion;});
    if(motionButton){motionButton.textContent=still?'Animations off':'Animations on';motionButton.setAttribute('aria-pressed',String(!still));}
  }
  motionButton?.addEventListener('click',()=>{still=!still;write('engineering-guide:still',still);applyMotion();});
  media.addEventListener('change',()=>{still=read('engineering-guide:still',media.matches,boolean);applyMotion();});applyMotion();
  document.querySelectorAll('.mer,.figwrap,.featured-diagram').forEach(figure=>{
    const img=figure.querySelector('img');if(!img)return;
    const toolbar=document.createElement('div');toolbar.className='visual-toolbar';const hint=document.createElement('span');hint.className='diagram-scroll-hint';hint.textContent='Wide diagram? Swipe to explore.';toolbar.append(hint);
    if(img.dataset.still){
      const toggle=document.createElement('button');
      const updateToggle=()=>{const showingStill=img.getAttribute('src')===img.dataset.still;toggle.textContent=showingStill?'Play animation':'Show still';toggle.setAttribute('aria-pressed',String(!showingStill));};
      toggle.addEventListener('click',()=>{img.src=img.getAttribute('src')===img.dataset.still?img.dataset.motion:img.dataset.still;updateToggle();});updateToggle();toolbar.append(toggle);
    }
    const zoom=document.createElement('button');zoom.textContent='Fit diagram';zoom.addEventListener('click',()=>{
      const fitted=img.dataset.fit==='true';img.dataset.fit=String(!fitted);img.style.maxWidth=fitted?'':'100%';img.style.minWidth=fitted?'':'0';zoom.textContent=fitted?'Fit diagram':'Actual size';
    });toolbar.append(zoom);figure.after(toolbar);
  });
  document.querySelectorAll('pre').forEach(pre=>{
    const code=pre.querySelector('code');if(!code)return;
    const wrapper=document.createElement('div');wrapper.className='code-example';
    const toolbar=document.createElement('div');toolbar.className='code-actions';
    const label=document.createElement('span');label.className='code-label';
    const language=[...code.classList].find(name=>name.startsWith('language-'))?.slice(9);
    label.textContent=language?`${language.toUpperCase()} EXAMPLE`:'CODE EXAMPLE';
    const button=document.createElement('button');button.type='button';button.className='copy-code';button.textContent='Copy code';button.setAttribute('aria-label',language?`Copy ${language} code`:'Copy code');
    button.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(code.textContent);button.textContent='Copied';}catch{button.textContent='Copy unavailable';}setTimeout(()=>button.textContent='Copy code',1800);});
    toolbar.append(label,button);pre.before(wrapper);wrapper.append(toolbar,pre);
  });
  const search=document.getElementById('contents-search'), results=document.getElementById('search-results'), tree=document.getElementById('contents-tree');
  let searchData, pending, searchRevision=0;
  search.addEventListener('input',()=>{
    clearTimeout(pending);const revision=++searchRevision;const query=search.value.trim().toLowerCase();
    if(!query){results.hidden=true;tree.hidden=false;return;}
    results.hidden=false;tree.hidden=true;results.replaceChildren();results.textContent='Searching…';
    pending=setTimeout(async()=>{
      try{
        if(!searchData){const response=await fetch(base+'search.json');if(!response.ok)throw Error();searchData=await response.json();}
        if(revision!==searchRevision)return;
        const words=query.split(/\s+/);const hits=searchData.map(p=>({p,score:words.every(w=>(p.title+' '+p.text).toLowerCase().includes(w))?words.reduce((s,w)=>s+(p.title.toLowerCase().includes(w)?10:1),0):0})).filter(x=>x.score).sort((a,b)=>b.score-a.score).slice(0,16);
        results.replaceChildren();
        if(!hits.length){results.textContent='No matching concepts. Try another term.';return;}
        hits.forEach(({p})=>{const a=document.createElement('a');a.href=p.url;a.textContent=p.title;const small=document.createElement('small');small.textContent=p.chapter;a.append(small);results.append(a);});
      }catch{if(revision===searchRevision)results.textContent='Search is unavailable. Clear the search to browse the contents.';}
    },140);
  });
  }
  main();
})();
