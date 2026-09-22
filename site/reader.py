"""Build the guided reading experience over the repository's existing material."""
from __future__ import annotations
import html
import hashlib
import base64
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
import course

E = html.escape
CODE_SUFFIXES = {'.py', '.ts', '.js', '.mjs', '.cjs', '.json', '.yaml', '.yml', '.sql', '.csv', '.txt', '.diff', '.sh'}
NAV_LABELS = {'curriculum', 'home', 'interview home', 'coding home', 'coding start', 'learning sequence', 'independent practice', 'all coding problems', 'ordered foundation route', 'next', 'static diagram', 'open motion study', 'read the completed still'}


def prepare_text(text):
    """Drop redundant movement furniture, preserving teaching and references."""
    lines = text.splitlines()
    out = []
    fenced = False
    for line in lines:
        if line.startswith('```'): fenced = not fenced
        if not fenced:
            if line.startswith(('Next chapter:', '[Curriculum]', '[Learning sequence]', '[Choose an independent assessment]', '[Coding start]', '[Ordered foundation route]', '[Interview home]')):
                continue
            if re.match(r'^\[(?:Contracts and solutions|Study method|Start here|How to study)\].* · ', line):
                continue
        out.append(line)
    return '\n'.join(out)


def local_target(b, page, href):
    url = urlsplit(href)
    if url.scheme or url.netloc or not url.path: return None
    path = unquote(url.path)
    target = (b.OUT / path.lstrip('/')) if path.startswith('/') else b.OUT / Path(b.dest_for(page['src'])).parent / path
    try: return target.resolve().relative_to(b.OUT.resolve()).as_posix()
    except ValueError: return None


def compose(b, page, have, by_dest):
    depth = len(Path(b.dest_for(page['src'])).parts) - 1
    text = prepare_text(page['text'])
    if page['kind'] == 'subject': text = b.strip_chapter_menus(text)
    raw, _ = b.render_body(text, have, depth)
    soup = BeautifulSoup(raw, 'html.parser')
    # Chapter/part overview lists are generated from the real teaching order.
    # Sources remain available in the reference shelf, not as link menus.
    for paragraph in list(soup.find_all('p')):
        links = paragraph.find_all('a')
        if not links: continue
        remainder = paragraph.get_text(' ', strip=True)
        for a in links: remainder = remainder.replace(a.get_text(' ', strip=True), '')
        if not re.sub(r'[\s·|.,:—–-]', '', remainder) and all(local_target(b, page, a.get('href', '')) is not None for a in links):
            # Code/fixtures are instructional; leave them for inline expansion.
            if not any(Path(urlsplit(a.get('href', '')).path).suffix in CODE_SUFFIXES for a in links):
                paragraph.decompose()
    embedded = set()
    code_tail = {}
    for a in list(soup.find_all('a')):
        href = a.get('href', '')
        target = local_target(b, page, href)
        if href.startswith('#'):
            # In-page movement belongs in the nested contents too.
            a.unwrap(); continue
        if target is None:
            a['target'] = '_blank'; a['rel'] = 'noopener noreferrer'; a['class'] = ['source-link']; continue
        disk = b.OUT / target
        suffix = disk.suffix
        label = a.get_text(' ', strip=True)
        if suffix in CODE_SUFFIXES and disk.is_file():
            if target in embedded:
                a.replace_with(soup.new_string(label + ' (shown in this lesson)')); continue
            embedded.add(target)
            content = disk.read_text(encoding='utf-8', errors='replace')
            panel = soup.new_tag('figure', attrs={'class': 'code-file', 'data-source': target})
            caption = soup.new_tag('figcaption'); caption.string = label + ' · ' + disk.name
            pre = soup.new_tag('pre'); code = soup.new_tag('code', attrs={'class': 'language-' + suffix.lstrip('.')}); code.string = content
            pre.append(code); panel.extend([caption, pre])
            # Preserve original paragraph semantics, then put complete code beside it.
            block = a.find_parent(['p', 'li', 'td']) or a
            if block.name == 'td': block = block.find_parent('table').parent
            if not a.find_parent('details'):
                enclosure = soup.new_tag('details', attrs={'class': 'inline-reference'})
                summary = soup.new_tag('summary'); summary.string = 'Inspect source · ' + disk.name
                enclosure.extend([summary, panel]); panel = enclosure
            anchor = code_tail.get(id(block), block)
            anchor.insert_after(panel)
            code_tail[id(block)] = panel
            a.replace_with(soup.new_string(label + ' (included below)'))
        elif suffix == '.svg':
            # Static alternatives are inline controls beside their animation.
            if '-still' in disk.stem or 'static' in label.lower():
                a.replace_with(soup.new_string(''))
            elif not soup.find('img', src=href):
                img = soup.new_tag('img', src=href, alt=label, loading='lazy')
                a.replace_with(img)
            else: a.unwrap()
        elif target in by_dest or target.endswith('/index.html') or suffix in ('.html', ''):
            target_page = by_dest.get(target) or by_dest.get(target.rstrip('/') + '/index.html')
            span = soup.new_tag('span', attrs={'class': 'concept-reference'})
            span.string = label
            if target_page and target_page.get('chapter') and target_page.get('chapter') != page.get('chapter'):
                span['title'] = f"Covered in chapter {target_page['chapter']}: {target_page.get('subject_title', '')}"
            a.replace_with(span)
        else:
            # Keep file downloads inside the left resources branch; reading never navigates away.
            a.unwrap()
    for p in list(soup.find_all('p')):
        if not p.get_text(strip=True) and not p.find(['img', 'code']): p.decompose()
        elif re.fullmatch(r'[\s·|.,]+', p.get_text()): p.decompose()
    # Content-addressed diagrams and original animated SVGs stay in their argument.
    for img in soup.find_all('img'):
        if not img.get('alt') or img.get('alt') == 'Diagram':
            heading = img.find_previous(['h2', 'h3', 'h1'])
            img['alt'] = 'Diagram: ' + (heading.get_text(' ', strip=True) if heading else page['title'])
        img['loading'] = 'lazy'
        img['decoding'] = 'async'
        src = img.get('src', '')
        asset = local_target(b, page, src)
        if asset in getattr(b, 'MOTION_STILLS', {}):
            img['data-motion'] = src
            img['data-still'] = '../' * depth + b.MOTION_STILLS[asset]
    # Real source links remain optional evidence at the end of the lesson.
    sources = []
    for a in list(soup.select('a.source-link')):
        url = a.get('href', '')
        if url not in [s[0] for s in sources]: sources.append((url, a.get_text(' ', strip=True)))
        span = soup.new_tag('span', attrs={'class': 'citation'}); span.string = a.get_text(' ', strip=True)
        a.replace_with(span)
    if sources:
        details = soup.new_tag('details', attrs={'class': 'sources'})
        summary = soup.new_tag('summary'); summary.string = f'Sources and further reading · {len(sources)}'; details.append(summary)
        ul = soup.new_tag('ul')
        for url, label in sources:
            li = soup.new_tag('li'); a = soup.new_tag('a', href=url, target='_blank', rel='noopener noreferrer'); a.string=label; li.append(a); ul.append(li)
        details.append(ul); soup.append(details)
    headings = []
    for heading in soup.find_all(['h2', 'h3']):
        if heading.get('id'): headings.append({'id': heading['id'], 'title': heading.get_text(' ', strip=True), 'level': int(heading.name[1])})
    page['headings'] = headings
    page['embedded'] = sorted(embedded)
    return str(soup)


def href(base, page): return base.rstrip('/') + page['url']


def toc(pages, sequence, current, base):
    def link(p, label=None, css=''):
        on = p['src'] == current['src']
        return f'<a class="toc-link {css}{" active" if on else ""}" href="{href(base,p)}" data-page="{E(p["src"])}" {"aria-current=\"page\"" if on else ""}>{E(label or p["title"])}</a>'
    result = [f'<a class="identity" href="{base}" aria-label="The Engineering Guide home"><span class="identity-mark" aria-hidden="true">e<span>∕</span></span><span>The Engineering Guide<small>LEARN. BUILD. REASON.</small></span></a>',
              '<div class="search-box"><span aria-hidden="true">⌕</span><label class="sr-only" for="contents-search">Search the curriculum</label><input id="contents-search" type="search" placeholder="Find a concept…" autocomplete="off"><kbd>/</kbd></div><div id="search-results" hidden aria-live="polite"></div>',
              '<div class="contents-label">TABLE OF CONTENTS <button id="collapse-contents" aria-label="Collapse all chapters">−</button></div><div id="contents-tree">', link(pages[0], 'Overview', 'overview')]
    for group in [p for p in sequence if p['kind']=='group']:
        result.append(f'<section class="toc-area"><h2><span>{group["gnum"]:02}</span>{E(group["title"])}</h2>')
        result.append(link(group, 'Part introduction', 'part-intro'))
        for chapter in [p for p in sequence if p['kind']=='subject' and p['group']==group['group']]:
            active = current.get('chapter') == chapter['chapter']
            result.append(f'<details class="toc-chapter" {"open" if active else ""}><summary><span class="chapter-number">{chapter["chapter"]:02}</span><span>{E(chapter["title"])}</span><span class="chevron" aria-hidden="true">›</span></summary><div class="toc-lessons">')
            result.append(link(chapter, 'Chapter introduction'))
            last = None
            for step in [p for p in sequence if p.get('chapter')==chapter['chapter'] and p.get('sub')]:
                section = step.get('section', 'Learn')
                if section != last:
                    result.append(f'<div class="toc-section">{E(section)}</div>'); last=section
                result.append(link(step, f'{step["sub"]:02}  {step["title"]}'))
                if current['src']==step['src'] and step.get('headings'):
                    result.append('<ol class="toc-headings">')
                    for h in step['headings']:
                        result.append(f'<li class="depth-{h["level"]}"><a href="#{E(h["id"])}" data-heading="{E(h["id"])}">{E(h["title"])}</a></li>')
                    result.append('</ol>')
            result.append('</div></details>')
        result.append('</section>')
    members={p['src'] for p in sequence}
    extra=[p for p in pages if p['src'] not in members]
    result.append('<section class="toc-area reference-area"><h2>REFERENCE SHELF</h2><p class="shelf-note">Indexes, assessment keys & source notes</p>')
    for title, predicate in [
        ('Concept references & indexes',lambda p:p['src'].startswith(('curriculum/','indexes/','projects/'))),
        ('Assessment & study guides',lambda p:p['src'].startswith('practice/')),
        ('Research & repository notes',lambda p:p['src'].startswith(('docs/','scripts/'))),
    ]:
        items=[p for p in extra if predicate(p)]
        opened=any(p['src']==current['src'] for p in items)
        result.append(f'<details class="toc-chapter" {"open" if opened else ""}><summary><span>{title}</span><span class="chevron">›</span></summary><div class="toc-lessons">')
        result.extend(link(p) for p in items); result.append('</div></details>')
    result.append(f'<a class="toc-link" href="{base}gallery/">Visual reference</a>')
    result.append('</section></div><div class="rail-footer"><span class="status-dot"></span>YOUR PLACE IS SAVED ON THIS DEVICE<button id="reset-progress">Reset progress</button></div>')
    return ''.join(result)


def overview(b, sequence, base):
    return f'''<header class="home-hero"><div class="eyebrow"><span class="status-dot"></span> A PRACTICAL SOFTWARE ENGINEERING CURRICULUM</div>
<h1>Build the judgment.<br><em>Then write the code.</em></h1>
<p class="hero-lede">Understand the problem. Make the trade-offs. Build something that holds up.<br class="desktop-only"> One guided journey from your first correct solution to systems you can defend.</p>
<div class="hero-actions"><a class="primary-button" data-start href="{href(base,sequence[1])}">Start learning <span aria-hidden="true">↗</span></a><span>One sequence. Deeper questions at every step.</span></div>
<div class="hero-stats"><div><strong>17</strong><span>engineering chapters</span></div><div><strong>42</strong><span>coding problems</span></div><div><strong>45</strong><span>project briefs</span></div></div></header>
<section class="home-mechanism"><div class="section-label">01 / THE WAY YOU’LL LEARN</div><div class="section-heading"><h2>See the system.<br>Understand the consequences.</h2><p>Follow requests through boxes and boundaries. Predict what breaks, change the design, and see why the fix works.</p></div><figure class="featured-diagram"><figcaption><span class="diagram-label">INSIDE A REQUEST</span><span>Trace it before you build it</span></figcaption><img src="{base}assets/diagrams/request-lifecycle.svg" data-motion="{base}assets/diagrams/request-lifecycle.svg" data-still="{base}assets/resting/diagrams/request-lifecycle.svg" alt="An animated request moving through client, API, service, and database boundaries"><div class="diagram-caption">The diagrams belong to the explanation. You’ll meet them exactly where the concept needs them.</div></figure></section>
<section class="journey-section"><div class="section-label">02 / THE JOURNEY</div><h2>From correct code<br>to decisions that last.</h2><div class="journey-grid">{''.join(f'<div class="journey-card"><span class="journey-number">0{i}</span><div><h3>{E(name)}</h3><p>{E(desc)}</p><span class="journey-meta">{detail}</span></div></div>' for i,(name,desc,detail) in enumerate([
('Write correct code','Clarify a problem. Work with AI deliberately. Choose a data structure and defend its invariant.','Problem solving · Algorithms'),
('Build a complete application','Follow state from a browser to an API and database. Test behavior and enforce ownership.','Backend · Data · Frontend · Testing · Security'),
('Design, ship, and operate','Design under constraints. Release safely, observe the system, and recover when it fails.','System design · CI/CD · AWS · Reliability'),
('Scale and evolve','Handle more load, evaluate AI, migrate live systems, and make decisions across teams.','Scale · Performance · AI systems · Technical decisions')],1))}</div></section>
<section class="learning-contract"><div class="section-label">03 / EVERY LESSON HAS A JOB</div><h2>Start with a problem.<br>Leave with a reason.</h2><ol><li><span>01</span><div><h3>Understand the situation</h3><p>A concrete brief, examples, expected behavior, and the boundary of the problem.</p></div></li><li><span>02</span><div><h3>Trace it. Build it. Check it.</h3><p>Visual explanations, a baseline, implementation details, and tests in the same reading flow.</p></div></li><li><span>03</span><div><h3>Change the requirement</h3><p>Follow-ups deepen the same problem into senior and staff-level reasoning.</p></div></li></ol><p class="quiet-note">Use Next to follow the sequence. The contents on the left are always available when you want to revisit a concept. Reference answers remain closed until you choose to inspect them.</p></section>'''


def intro(b, page, sequence):
    if page['kind']=='group':
        children=[p for p in sequence if p['kind']=='subject' and p['group']==page['group']]
        description=b.GROUPS[page['group']][2]
    else:
        children=[p for p in sequence if p.get('chapter')==page.get('chapter') and p.get('sub')]
        description=page.get('blurb') or page['summary']
    return f'<h1>{E(page["title"])}</h1><p class="chapter-lede">{E(description)}</p><div class="chapter-contract"><span class="section-label">THE WORK AHEAD</span><p>Move through the steps in order. Each explanation leads into its exercise; implementation, diagrams, and deeper questions stay with the problem they explain.</p></div><ol class="chapter-outline">'+''.join(f'<li><span>{i:02}</span><div><h2>{E(p["title"])}</h2><p>{E(p.get("blurb") or p.get("section") or "Learn, apply, and explain")}</p></div></li>' for i,p in enumerate(children,1))+'</ol>'


def shell(b, page, body, pages, sequence, base):
    position=page.get('position')
    prev=sequence[position-1] if position is not None and position>0 else None
    nxt=sequence[position+1] if position is not None and position+1<len(sequence) else None
    is_home=page['kind']=='home'
    subtitle = 'Curriculum overview' if is_home else (f'PART {page.get("gnum", "")} / {page.get("subject_title") or page.get("group_title")}' if page.get('group') else 'REFERENCE SHELF')
    meta= 'THE ENGINEERING GUIDE' if is_home else (f'CHAPTER {page["chapter"]:02} · STEP {page["sub"]:02} OF {page["step_count"]:02}' if page.get('sub') else f'PART {page["gnum"]:02}' if page['kind']=='group' else f'CHAPTER {page["chapter"]:02}' if page.get('chapter') else 'SUPPORTING MATERIAL')
    nav=''
    if position is not None:
        previous=(f'<a class="previous-step" href="{href(base,prev)}"><span>← PREVIOUS</span><strong>{E(prev["title"])}</strong></a>' if prev else '<span></span>')
        nextlink=(f'<a class="next-step" data-complete="{E(page["src"])}" href="{href(base,nxt)}"><span>{"BEGIN THE JOURNEY" if is_home else "NEXT STEP"} →</span><strong>{E(nxt["title"])}</strong></a>' if nxt else '<div class="course-end"><span>YOU’VE REACHED THE END</span><strong>Return to a difficult problem. Explain it again, without the reference.</strong><button data-finish>Mark final step complete</button></div>')
        nav=f'<nav class="step-navigation" aria-label="Lesson sequence">{previous}{nextlink}</nav>'
    top_note = '<div class="reader-meta"><span>'+meta+'</span><span>'+('READ · BUILD · REASON' if is_home else E(b.KINDS.get(page['kind'],('Lesson',''))[1] or 'GUIDED READING'))+'</span></div>'
    if is_home: body=overview(b,sequence,base)
    elif page['kind'] in ('group','subject'): body=intro(b,page,sequence)
    current=json.dumps({'src':page['src'],'url':href(base,page),'title':page['title'],'position':position,'total':len(sequence)},ensure_ascii=True).replace('<','\\u003c')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(page['title'])} · The Engineering Guide</title><meta name="description" content="{E(page['summary'][:180])}"><meta name="color-scheme" content="light"><link rel="stylesheet" href="{base}{b.READER_ASSETS['css']['file']}" integrity="{b.READER_ASSETS['css']['integrity']}" crossorigin="anonymous"><style id="reader-styles">{b.READER_CSS}</style></head>
<body class="{'home' if is_home else 'lesson'}"><a class="skip-link" href="#reading">Skip to lesson</a><div class="mobile-bar"><button id="open-contents" aria-expanded="false" aria-controls="sidebar">☰ <span>Contents</span></button><span>The Engineering Guide</span></div><button class="drawer-backdrop" id="close-contents" aria-label="Close contents" tabindex="-1" hidden></button><aside class="sidebar" id="sidebar"><button class="mobile-close" id="dismiss-contents" aria-label="Close contents">×</button><nav aria-label="Table of contents">{toc(pages,sequence,page,base)}</nav></aside>
<noscript><style>.search-box,#motion-toggle,.mobile-bar button{{display:none}}@media(max-width:760px){{.sidebar{{position:relative;transform:none;width:100%;height:65vh;box-shadow:none}}.mobile-close{{display:none}}}}</style></noscript><div class="reading-shell"><header class="reading-bar"><span>{E(subtitle)}</span><div class="reading-controls"><span id="saved-progress">{f'Step {position} of {len(sequence)-1}' if position else 'Your guided curriculum'}</span><button id="motion-toggle" aria-pressed="false">Motion on</button></div></header><div class="read-progress" aria-hidden="true"><span></span></div><main id="reading" tabindex="-1">{top_note}<article class="lesson-body">{body}</article>{nav}<footer class="page-footer"><span>THE ENGINEERING GUIDE</span><span>Understanding, through practice.</span></footer></main></div><script id="page-state" type="application/json">{current}</script><script>window.SITE_BASE={json.dumps(base)};</script><script src="{base}{b.READER_ASSETS['js']['file']}" integrity="{b.READER_ASSETS['js']['integrity']}" crossorigin="anonymous" defer></script></body></html>'''


def build(b):
    base=os.environ.get('SITE_BASE','/')
    if not base.startswith('/') or not base.endswith('/'): raise ValueError('SITE_BASE must be an absolute path ending in /')
    b.CHAPTER_BLURBS.update(b.chapter_blurbs())
    pages=b.collect(); sequence=course.organize(pages)
    blocks=b.mermaid_blocks(pages); have=b.render_mermaid(blocks)
    if set(blocks)!=have: raise RuntimeError('Missing diagrams: refusing an incomplete site build')
    if b.OUT.exists(): shutil.rmtree(b.OUT)
    b.OUT.mkdir(parents=True)
    shutil.copytree(b.ROOT/'assets',b.OUT/'assets')
    b.MOTION_STILLS = {}
    for original in (b.ROOT/'assets').rglob('*.svg'):
        source = original.read_text()
        if not re.search(r'<animate|<set\b|@keyframes', source): continue
        asset = original.relative_to(b.ROOT).as_posix()
        authored = original.with_name(original.stem + '-still.svg')
        if authored.exists():
            b.MOTION_STILLS[asset] = authored.relative_to(b.ROOT).as_posix()
        else:
            # Original boxes and labels are preserved; moving overlays rest.
            tree = ET.fromstring(source)
            for parent in tree.iter():
                for child in list(parent):
                    tag = child.tag.split('}')[-1]
                    if tag == 'animateMotion':
                        start = re.match(r'M\s*([-+\d.]+)[ ,]+([-+\d.]+)', child.get('path',''))
                        if start:
                            parent.set('transform', (parent.get('transform','') + f' translate({start[1]} {start[2]})').strip())
                    if tag in ('animate','animateMotion','animateTransform','set'):
                        parent.remove(child)
            style = ET.SubElement(tree, '{http://www.w3.org/2000/svg}style')
            style.text = '*{animation:none!important;transition:none!important}'
            resting = 'assets/resting/' + original.relative_to(b.ROOT/'assets').as_posix()
            dest = b.OUT/resting; dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(ET.tostring(tree,encoding='unicode'))
            b.MOTION_STILLS[asset] = resting
    (b.OUT/'assets/mermaid').mkdir(exist_ok=True)
    for h in have: shutil.copy(b.MERMAID_CACHE/f'{h}.svg',b.OUT/'assets/mermaid'/f'{h}.svg')
    shutil.copytree(b.ROOT/'site/fonts',b.OUT/'fonts')
    # Bind each HTML release to exact assets. The inline copy also keeps the
    # layout intact if a stylesheet request fails or a stale proxy returns it.
    b.READER_CSS = (b.ROOT/'site/style.css').read_text().replace('url(fonts/', f'url({base}fonts/')
    assert '</style' not in b.READER_CSS.lower()
    b.READER_ASSETS = {}
    for kind, text in [('css', b.READER_CSS), ('js', (b.ROOT/'site/app.js').read_text())]:
        payload = text.encode()
        digest = hashlib.sha256(payload).digest()
        filename = f'reader-{kind}.{digest.hex()[:16]}.{kind}'
        (b.OUT/filename).write_bytes(payload)
        b.READER_ASSETS[kind] = {'file': filename, 'sha256': digest.hex(),
                                'integrity': 'sha256-' + base64.b64encode(digest).decode()}
    (b.OUT/'reader-assets.json').write_text(json.dumps(b.READER_ASSETS, indent=2))
    # Keep the old endpoints for existing bookmarks, but never reference them
    # from new HTML: old HTML and new styles must not share a cache identity.
    for filename in ('style.css','app.js'): shutil.copy(b.ROOT/'site'/filename,b.OUT/filename)
    for folder in ('curriculum','projects','practice','docs','scripts','indexes'):
        for f in (b.ROOT/folder).rglob('*'):
            if not f.is_file() or f.suffix=='.md' or {'node_modules','__pycache__'} & set(f.parts): continue
            rel=f.relative_to(b.ROOT); dest=b.OUT/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy(f,dest)
    by_dest={b.dest_for(p['src']):p for p in pages}
    bodies={p['src']:compose(b,p,have,by_dest) for p in pages}
    # Preserve old URLs while all reading movement uses the one sequence.
    for p in pages:
        out=b.OUT/b.dest_for(p['src']);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(shell(b,p,bodies[p['src']],pages,sequence,base))
    # Old gallery bookmarks remain usable; every visual retains its lesson context.
    gallery=b.OUT/'gallery';gallery.mkdir(exist_ok=True)
    items=[]
    for p in pages:
        s=BeautifulSoup(bodies[p['src']],'html.parser')
        for img in s.find_all('img'):
            src=local_target(b,p,img.get('src',''))
            if src:items.append(f'<figure><img loading="lazy" src="{base}{src}" alt="{E(img.get("alt",""))}"><figcaption>{E(p["title"])}</figcaption></figure>')
    gp={'src':'gallery/README.md','url':'/gallery/','kind':'index','title':'Visual reference','summary':'Every teaching visual, preserved in context.'}
    (gallery/'index.html').write_text(shell(b,gp,'<h1>Visual reference</h1><div class="visual-gallery">'+''.join(items)+'</div>',pages,sequence,base))
    records=[{k:p.get(k) for k in ('src','title','url','kind','chapter','sub','section','position','headings','embedded')} for p in pages]
    (b.OUT/'course.json').write_text(json.dumps({'sequence':[p['src'] for p in sequence],'pages':records},separators=(',',':')))
    (b.OUT/'search.json').write_text(json.dumps([{'title':p['title'],'url':href(base,p),'chapter':p.get('subject_title','Reference'),'text':b.prose_of(p['text'])} for p in pages],separators=(',',':')))
    print(f'Built {len(pages)} pages, {len(sequence)-1} guided steps, {len(have)} diagrams; full TOC and inline code.')
    return 0
