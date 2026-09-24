(() => {
  'use strict';
  const state = JSON.parse(document.getElementById('page-state').textContent);
  const base = window.SITE_BASE || '/';
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
    progress.last = {url: state.url, title: state.title}; write(key, progress);
  }
  document.querySelectorAll('[data-page]').forEach(a => {
    if (progress.completed.includes(a.dataset.page)) a.classList.add('completed');
  });
  const starts = [...document.querySelectorAll('[data-start]')];
  if (starts.length && progress.last && typeof progress.last.url === 'string' && progress.last.url.startsWith(base) && !progress.last.url.startsWith('//')) {
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
  function replaySample(panel){
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
    replaySample(samplePanels.find(panel=>panel.dataset.samplePanel===name));
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
  document.querySelectorAll('[data-replay-sample]').forEach(button=>button.addEventListener('click',()=>replaySample(button.closest('[data-sample-panel]'))));
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
})();
