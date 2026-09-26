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
import content_checks
import lock
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'codefield'))
import starter as codefield_starter  # noqa: E402
import tips as codefield_tips  # noqa: E402

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


def frame_practice(soup, page):
    """Present contracts and examples without hiding canonical source content."""
    source = page['src']
    problem = '/problems/' in source and source.endswith('.md')
    project = '/projects/' in source or source.startswith('projects/reading-list/stages/')
    foundation = '/lessons/' in source and '/02-data-structures-algorithms/' in source
    if not (problem or project or foundation):
        return
    if problem or project:
        brief = soup.find('blockquote')
        if brief:
            panel = soup.new_tag('section', attrs={'class': 'task-brief', 'aria-label': 'Project brief' if project else 'Problem brief'})
            label = soup.new_tag('div', attrs={'class': 'task-label'})
            label.string = 'YOUR PROJECT' if project else 'THE PROBLEM'
            brief.wrap(panel)
            panel.insert(0, label)
    # Input/output examples are stacked pairs on small screens. Comparison,
    # trace, and contract tables remain tables: their columns are meaningful.
    for table in list(soup.find_all('table')):
        headers = [th.get_text(' ', strip=True) for th in table.select('thead th')]
        if not headers or len(headers) < 2:
            continue
        expected = next((i for i, value in enumerate(headers)
                         if value.lower().startswith(('expected', 'required result',
                                                     'required decision', 'visible result',
                                                     'observable result'))), None)
        if expected is None:
            continue
        case_column = len(headers) > 2 and headers[0].lower() in {'case', 'example', 'request'}
        if not (case_column or foundation or problem):
            continue
        input_column = 1 if case_column else 0
        if expected == input_column:
            continue
        cards = soup.new_tag('div', attrs={'class': 'example-cards', 'role': 'list', 'aria-label': 'Inputs and expected results'})
        for number, row in enumerate(table.select('tbody tr'), 1):
            cells = row.find_all('td', recursive=False)
            if len(cells) != len(headers):
                raise ValueError(f'Malformed example row in {source}')
            card = soup.new_tag('section', attrs={'class': 'example-card', 'role': 'listitem'})
            title = soup.new_tag('h4', attrs={'class': 'example-title'})
            title.string = f'{number:02} · ' + (cells[0].get_text(' ', strip=True) if case_column else 'Try this input')
            card.append(title)
            pair = soup.new_tag('dl', attrs={'class': 'example-pair'})
            for index, label in [(input_column, 'Input / starting state'), (expected, 'Expected result')]:
                item = soup.new_tag('div', attrs={'class': 'example-value'})
                term = soup.new_tag('dt'); term.string = label
                value = soup.new_tag('dd')
                for child in list(cells[index].contents): value.append(child.extract())
                item.extend([term, value]); pair.append(item)
            card.append(pair)
            remaining = [i for i in range(len(cells)) if i not in {input_column, expected} and not (case_column and i == 0)]
            for index in remaining:
                note = soup.new_tag('p', attrs={'class': 'example-reason'})
                label = soup.new_tag('strong'); label.string = headers[index] + ': '
                note.append(label)
                for child in list(cells[index].contents): note.append(child.extract())
                card.append(note)
            cards.append(card)
        enclosure = table.parent if 'tablewrap' in table.parent.get('class', []) else table
        enclosure.replace_with(cards)
    if problem:
        heading = next((h for h in soup.find_all('h2') if h.get_text(strip=True) == 'The tool before the challenge'), None)
        if heading:
            refresher = soup.new_tag('details', attrs={'class': 'concept-refresher'})
            summary = soup.new_tag('summary'); summary.string = 'Optional refresher · the underlying tool'
            refresher.append(summary)
            heading.insert_before(refresher)
            node = heading.next_sibling
            while node is not None and getattr(node, 'name', None) not in {'h2', 'h3'}:
                following = node.next_sibling
                refresher.append(node.extract())
                node = following
            heading.decompose()


def mount_codefield(b, soup, page, depth):
    """Give a coding problem a field to write and run the answer in.

    Only where the page has a "Write this:" block AND the problem ships its own
    test_solution.py, and never on a sealed page. The static block stays in the
    HTML, for phones and for readers without JavaScript; codefield.js hides it
    when it mounts on a desktop. The starter is that same block, so the field
    can never disagree with the question printed above it.
    """
    src = page['src']
    if '/problems/' not in src or not src.endswith('README.md') or lock.is_locked(page):
        return
    tests = b.ROOT / Path(src).parent / 'test_solution.py'
    if not tests.is_file() or not getattr(b, 'CODEFIELD', None):
        return
    start = codefield_starter.starter_for(page['text'])
    label = next((p for p in soup.find_all('p') if p.get_text(' ', strip=True) == 'Write this:'), None)
    pre = label.find_next_sibling('pre') if label else None
    if not start or pre is None:
        return
    wrap = soup.new_tag('div', attrs={'class': 'codefield-wrap'})
    static = soup.new_tag('div', attrs={'class': 'codefield-static'})
    pre.insert_before(wrap)
    static.append(pre.extract())
    up = '../' * depth
    mount = soup.new_tag('section', attrs={'class': 'codefield', 'hidden': '',
                                           'data-worker': up + b.CODEFIELD['worker']['file'],
                                           'data-harness': up + b.CODEFIELD['harness']['file']})
    data = soup.new_tag('script', attrs={'type': 'application/json'})
    # tips.json beside the README: what the page can say when the reader asks
    # for a tip, chosen by what went wrong. Checked by site/codefield/test_tips.py.
    data.string = json.dumps({'id': Path(src).parent.name, 'starter': start['code'],
                              'given': start['given'], 'tests': tests.read_text(),
                              'tips': codefield_tips.load(tests.parent)},
                             ensure_ascii=True).replace('<', '\\u003c')
    mount.append(data)
    wrap.extend([static, mount])
    page['codefield'] = True


def build_codefield(b):
    """Bundle the code field for this release (content-hashed, like reader-js)."""
    r = subprocess.run(['node', str(b.ROOT / 'site/tools/build-codefield.mjs'), str(b.OUT)],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise SystemExit('code field bundle failed:\n' + r.stderr[-3000:])
    return json.loads(r.stdout)


def compose(b, page, have, by_dest):
    depth = len(Path(b.dest_for(page['src'])).parts) - 1
    text = prepare_text(page['text'])
    if page['kind'] == 'subject': text = b.strip_chapter_menus(text)
    raw, _ = b.render_body(text, have, depth)
    soup = BeautifulSoup(raw, 'html.parser')
    page['expected_mermaid'] = [Path(i['src']).name for i in soup.select('img[src]') if '/assets/mermaid/' in i['src']]
    page['source_images'] = sorted({local_target(b, page, i['src']) for i in soup.select('img[src]') if local_target(b, page, i['src'])})
    page['expected_code'] = sorted({local_target(b, page, a['href']) for a in soup.select('a[href]') if Path(urlsplit(a['href']).path).suffix in CODE_SUFFIXES and local_target(b, page, a['href'])})
    # Chapter/part overview lists are generated from the real teaching order.
    # Sources remain available in the reference shelf, not as link menus.
    for paragraph in list(soup.find_all('p')):
        links = paragraph.find_all('a')
        if not links: continue
        remainder = paragraph.get_text(' ', strip=True)
        for a in links: remainder = remainder.replace(a.get_text(' ', strip=True), '')
        if not re.sub(r'[\s·|.,:—–-]', '', remainder) and all(local_target(b, page, a.get('href', '')) is not None for a in links):
            # Code/fixtures are instructional; leave them for inline expansion.
            if page['src'] != 'companies/README.md' and all(a.get_text(' ', strip=True).lower() in NAV_LABELS for a in links):
                paragraph.decompose()
    embedded = set()
    code_tail = {}
    for a in list(soup.find_all('a')):
        href = a.get('href', '')
        target = local_target(b, page, href)
        if href.startswith('#'):
            a['class'] = ['context-link']; continue
        if target is None:
            a['target'] = '_blank'; a['rel'] = 'noopener noreferrer'
            a['class'] = ['project-source'] if href.startswith('https://github.com/Soulful-Iris/junior-to-staff') else ['source-link']
            continue
        disk = b.OUT / target
        suffix = disk.suffix
        label = a.get_text(' ', strip=True)
        if suffix in CODE_SUFFIXES and not disk.is_file():
            raise ValueError(f"Missing linked code: {page['src']} -> {href}")
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
                summary = soup.new_tag('summary'); summary.string = 'Read the supplied code · ' + disk.name
                enclosure.extend([summary, panel]); panel = enclosure
            anchor = code_tail.get(id(block), block)
            anchor.insert_after(panel)
            code_tail[id(block)] = panel
            a['download'] = disk.name
            a['class'] = ['code-download']
            a.string = label + ' (download file, source below)'
        elif suffix == '.svg':
            # Static alternatives are inline controls beside their animation.
            if '-still' in disk.stem or 'static' in label.lower():
                a.replace_with(soup.new_string(''))
            elif not soup.find('img', src=href):
                img = soup.new_tag('img', src=href, alt=label, loading='lazy')
                a.replace_with(img)
            else: a.unwrap()
        elif page['src'] == 'companies/README.md' and target in by_dest and target.startswith('companies/'):
            a['class'] = list(set(a.get('class', [])) | {'studio-link'})
        else:
            target_page = by_dest.get(target) or by_dest.get(target.rstrip('/') + '/index.html')
            if not target_page and disk.is_dir():
                a['href'] = 'https://github.com/Soulful-Iris/junior-to-staff/tree/main/' + target
                a['class'] = ['project-source']
            elif target_page or disk.is_file():
                a['class'] = ['context-link']
            else:
                raise ValueError(f"Missing published reference: {page['src']} -> {href}")
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
    frame_practice(soup, page)
    mount_codefield(b, soup, page, depth)
    headings = []
    for heading in soup.find_all(['h2', 'h3']):
        if heading.get('id'): headings.append({'id': heading['id'], 'title': heading.get_text(' ', strip=True), 'level': int(heading.name[1])})
    page['headings'] = headings
    page['embedded'] = sorted(embedded)
    return str(soup)


def href(base, page): return base.rstrip('/') + page['url']


def part_label(page):
    return page.get('part_label') or f'PART {chr(64 + page["gnum"])}'


def toc(pages, sequence, current, base):
    def link(p, label=None, css='', lesson=False):
        on = p['src'] == current['src']
        content = E(label or p['title'])
        if lesson:
            index = f'T{p["track_no"]}.{p["sub"]:02}' if p.get('track_no') else f'{p["chapter"]}.{p["sub"]:02}'
            content = (f'<span class="lesson-index" aria-label="Chapter {p["chapter"]}, lesson {p["sub"]}">'
                       f'{index}</span><span class="lesson-title">{content}</span>')
            css += ' numbered-lesson'
        return f'<a class="toc-link {css}{" active" if on else ""}" href="{href(base,p)}" data-page="{E(p["src"])}" {"aria-current=\"page\"" if on else ""}>{content}</a>'
    result = [f'<a class="identity" href="{base}" aria-label="The Engineering Guide home"><span class="identity-mark" aria-hidden="true">e<span>∕</span></span><span>The Engineering Guide<small>LEARN. BUILD. REASON.</small></span></a>',
              '<div class="search-box"><span aria-hidden="true">⌕</span><label class="sr-only" for="contents-search">Search the curriculum</label><input id="contents-search" type="search" placeholder="Find a concept…" autocomplete="off"><kbd>/</kbd></div><div id="search-results" hidden aria-live="polite"></div>',
              '<div class="contents-label">TABLE OF CONTENTS <button id="collapse-contents" aria-label="Collapse all chapters">−</button></div><div id="contents-tree">', link(pages[0], 'Overview', 'overview')]
    for group in [p for p in sequence if p['kind']=='group' and p['group']!='crowdstrike']:
        result.append(f'<section class="toc-area part-{group["gnum"]}"><div class="toc-part-heading"><span class="part-label">{E(part_label(group))}</span><span class="part-title">{E(group["title"])}</span></div>')
        result.append(link(group, 'Part introduction', 'part-intro'))
        for chapter in [p for p in sequence if p['kind']=='subject' and p['group']==group['group']]:
            active = current.get('chapter') == chapter['chapter']
            result.append(f'<details class="toc-chapter" {"open" if active else ""}><summary><span class="chapter-number"><small>CH</small> {chapter["chapter"]:02}</span><span class="chapter-title">{E(chapter["title"])}</span><span class="chevron" aria-hidden="true">›</span></summary><div class="toc-lessons">')
            result.append(link(chapter, 'Chapter introduction'))
            last = None
            for step in [p for p in sequence if p.get('chapter')==chapter['chapter'] and p.get('sub')]:
                section = step.get('section', 'Learn')
                if section != last:
                    result.append(f'<div class="toc-section">{E(section)}</div>'); last=section
                result.append(link(step, lesson=True))
                if current['src']==step['src'] and step.get('headings'):
                    result.append('<div class="toc-page-label">ON THIS PAGE</div><ol class="toc-headings">')
                    for h in step['headings']:
                        result.append(f'<li class="depth-{h["level"]}"><a href="#{E(h["id"])}" data-heading="{E(h["id"])}">{E(h["title"])}</a></li>')
                    result.append('</ol>')
            result.append('</div></details>')
        result.append('</section>')
    members={p['src'] for p in sequence}
    extra=[p for p in pages if p['src'] not in members and not p['src'].startswith('companies/')]
    result.append('<section class="toc-area reference-area"><div class="toc-part-heading">REFERENCE SHELF</div><p class="shelf-note">Indexes, assessment keys & source notes</p>')
    for title, predicate in [
        ('Concept references & indexes',lambda p:p['src'].startswith(('curriculum/','indexes/','projects/','examples/'))),
        ('Assessment & study guides',lambda p:p['src'].startswith('practice/')),
        ('Research & repository notes',lambda p:p['src'].startswith(('docs/','scripts/'))),
    ]:
        items=[p for p in extra if predicate(p)]
        opened=any(p['src']==current['src'] for p in items)
        result.append(f'<details class="toc-chapter" {"open" if opened else ""}><summary><span>{title}</span><span class="chevron">›</span></summary><div class="toc-lessons">')
        result.extend(link(p) for p in items); result.append('</div></details>')
    result.append(f'<a class="toc-link" href="{base}gallery/">Visual reference</a>')
    studio=[p for p in sequence if p['src'].startswith('companies/')]
    result.append('</section><section class="toc-area company-area"><div class="toc-part-heading"><span class="part-label">OPTIONAL STUDIO</span><span class="part-title">Company interview practice</span></div>')
    result.append(link(studio[0], 'Start here · the interview room', 'part-intro'))
    for p in studio[1:]:
        active = current['src'] == p['src']
        result.append(f'<details class="toc-chapter" {"open" if active else ""}><summary><span>{E(p["title"])}</span><span class="chevron">›</span></summary><div class="toc-lessons">')
        result.append(link(p, 'Open company rehearsal'))
        if active and p.get('headings'):
            result.append('<div class="toc-page-label">ON THIS PAGE</div><ol class="toc-headings">')
            for h in p['headings']:
                result.append(f'<li class="depth-{h["level"]}"><a href="#{E(h["id"])}" data-heading="{E(h["id"])}">{E(h["title"])}</a></li>')
            result.append('</ol>')
        result.append('</div></details>')
    # The CrowdStrike track: its own area under the studio, with T-numbering.
    # Published sealed: the plain HTML carries a blurred placeholder and ciphertext.
    track_group = next((p for p in sequence if p['kind']=='group' and p['group']=='crowdstrike'), None)
    if track_group:
        track = ['<div class="toc-part-heading"><span class="part-label">ITS OWN LEAGUE</span><span class="part-title">CrowdStrike track</span></div>']
        track.append(link(track_group, 'Start here · the track', 'part-intro'))
        for chapter in [p for p in sequence if p['kind']=='subject' and p['group']=='crowdstrike']:
            active = current.get('chapter') == chapter['chapter']
            track.append(f'<details class="toc-chapter" {"open" if active else ""}><summary><span class="chapter-number"><small>T</small> {chapter["track_no"]}</span><span class="chapter-title">{E(chapter["title"])}</span><span class="chevron" aria-hidden="true">›</span></summary><div class="toc-lessons">')
            track.append(link(chapter, 'Chapter introduction'))
            last = None
            for step in [p for p in sequence if p.get('chapter')==chapter['chapter'] and p.get('sub')]:
                section = step.get('section', 'Learn')
                if section != last:
                    track.append(f'<div class="toc-section">{E(section)}</div>'); last=section
                track.append(link(step, lesson=True))
                if current['src']==step['src'] and step.get('headings'):
                    track.append('<div class="toc-page-label">ON THIS PAGE</div><ol class="toc-headings">')
                    for h in step['headings']:
                        track.append(f'<li class="depth-{h["level"]}"><a href="#{E(h["id"])}" data-heading="{E(h["id"])}">{E(h["title"])}</a></li>')
                    track.append('</ol>')
            track.append('</div></details>')
        result.append('</section><section class="toc-area track-area part-7">')
        result.append(lock.widget(lock.seal_cached(''.join(track)), 'replace', lock.RAIL_VEIL, 'lock-rail'))
    result.append('</section></div><div class="rail-footer"><span class="status-dot"></span>YOUR PLACE IS SAVED ON THIS DEVICE<button id="reset-progress">Reset progress</button></div>')
    return ''.join(result)


def overview(b, sequence, base):
    start = sequence[1]
    algorithm_preview = next(p for p in sequence if p['src'] == 'curriculum/01-code/02-data-structures-algorithms/problems/05-minimum-covering-window/README.md')
    design_preview = next(p for p in sequence if p['src'] == 'curriculum/03-production/01-system-design/problems/checkout-payment.md')
    aws_preview = next(p for p in sequence if p['src'] == 'curriculum/03-production/03-infrastructure/README.md')
    interview = next(p for p in sequence if p['src'] == 'companies/README.md')
    ai_part = next(p for p in sequence if p['kind'] == 'group' and p['group'] == 'ai-specialization')
    cs_part = next(p for p in sequence if p['kind'] == 'group' and p['group'] == 'crowdstrike')
    parts = [
        ('A', 'code', 'Coding and problem solving', 'Choose the state, solve the problem, and review AI-assisted changes.', 'Algorithms · Coding · Review'),
        ('B', 'applications', 'Production applications', 'Connect browser, API, database, tests, and access boundaries.', 'Backend · Data · Frontend · Security'),
        ('C', 'design', 'System design and scale', 'Design from requirements, then reason about capacity, performance, and cost.', 'Architecture · Scale · Cost'),
        ('D', 'operations', 'Production operations', 'Provision, deploy, observe, and recover a running application.', 'AWS · Delivery · Reliability'),
        ('E', 'evolution', 'System evolution and leadership', 'Migrate live systems and make decisions other teams can execute.', 'Migrations · Technical leadership'),
    ]
    group_pages = {p['group']: p for p in sequence if p['kind'] == 'group'}
    cs_card = lock.widget(lock.seal_cached(
        f'<a href="{href(base,cs_part)}"><span>CROWDSTRIKE TRACK</span><strong>Senior cloud backend loop</strong>'
        '<small>Preparation, reported coding problems, and the architecture they publish.</small></a>'),
        'replace', lock.CARD_VEIL, 'lock-card')
    journey = ''.join(
        f'<a class="journey-card" href="{href(base,group_pages[group])}"><span class="journey-number">{label}</span>'
        f'<div><h3>{E(name)} <span aria-hidden="true">&#8599;</span></h3><p>{E(desc)}</p><span class="journey-meta">{E(detail)}</span></div></a>'
        for label, group, name, desc, detail in parts
    )
    return f'''<header class="home-hero"><div class="eyebrow"><span class="status-dot"></span> A PRACTICAL SOFTWARE ENGINEERING CURRICULUM</div>
<h1>Build the judgment.<br><em>Then write the code.</em></h1>
<p class="hero-lede">Start with code. End with systems you can defend.</p>
<div class="hero-actions"><a class="primary-button" data-start href="{href(base,start)}">Start with Part A <span aria-hidden="true">&#8599;</span></a><a class="sample-link" href="#sample-lesson">See a sample lesson <span aria-hidden="true">&#8595;</span></a><span data-resume-label>New here? Start at the beginning.</span></div>
<div class="hero-promises" aria-label="What you will practice"><span>Solve unfamiliar problems</span><span>Build production systems</span><span>Defend design decisions</span></div></header>
<section class="home-mechanism" id="sample-lesson"><div class="section-label">TRY A PROBLEM</div><div class="section-heading"><h2>Pick a problem.<br>See it click.</h2><p>Each one starts with a question. The visual makes the answer easier to reason about.</p></div>
<div class="sample-showcase" data-sample-tabs>
<div class="sample-tabs" role="tablist" aria-label="Choose a sample problem"><button id="sample-tab-algorithm" role="tab" aria-selected="true" aria-controls="sample-algorithm" data-sample-tab="algorithm"><span>01</span>Data structures</button><button id="sample-tab-design" role="tab" aria-selected="false" aria-controls="sample-design" data-sample-tab="design" tabindex="-1"><span>02</span>Design / architecture</button><button id="sample-tab-aws" role="tab" aria-selected="false" aria-controls="sample-aws" data-sample-tab="aws" tabindex="-1"><span>03</span>Real-world AWS</button></div>
<div class="sample-stage">
<article class="sample-panel active sample-animate" id="sample-algorithm" role="tabpanel" aria-labelledby="sample-tab-algorithm" aria-hidden="false" data-sample-panel="algorithm">
<div class="sample-panel-grid"><div class="sample-problem"><span class="sample-kicker">SLIDING WINDOW</span><h3>What is the shortest substring containing A, B, and C?</h3><div class="sample-given"><code>ADOBECODEBANC</code><span>needs</span><code>A · B · C</code></div><div class="sample-answer"><span>ANSWER</span><strong>BANC</strong><p>Expand until the window has every needed letter. Then shrink it until removing one would break the match.</p></div></div>
<div class="window-demo" role="group" aria-label="A slow six-step sliding-window explanation with visible i and j pointers. The j pointer reads characters as the window expands. The i pointer removes characters as the window shrinks. A Counter hash map updates whenever A, B or C enters or leaves. The shortest valid window is BANC."><div class="visual-title"><span>EXPAND, CHECK, THEN SHRINK</span><small>32-second walkthrough</small></div><div class="window-story" aria-hidden="true"><section class="story-one"><b>1 · EXPAND j</b><strong>Move j right until the window has A, B, and C.</strong></section><section class="story-two"><b>2 · FIRST COMPLETE WINDOW</b><strong><code>ADOBEC</code> has all three. Save length 6.</strong></section><section class="story-three"><b>3 · SHRINK i</b><strong>Move i past A and the window becomes incomplete.</strong></section><section class="story-four"><b>4 · EXPAND j AGAIN</b><strong>Keep reading until A returns. The extra B is okay.</strong></section><section class="story-five"><b>5 · MOVE BOTH EDGES</b><strong>Move i until C is lost. Move j until C returns.</strong></section><section class="story-six"><b>6 · SHRINK i TO THE BEST</b><strong>Move past O, D, and E. Stop at <code>BANC</code>.</strong></section></div><div class="window-animation-grid"><div class="window-track-column"><div class="window-scan-track"><div class="letter-row"><b class="target-letter">A</b><b>D</b><b>O</b><b class="target-letter">B</b><b>E</b><b class="target-letter">C</b><b>O</b><b>D</b><b>E</b><b class="target-letter">B</b><b class="target-letter">A</b><b>N</b><b class="target-letter">C</b></div><i class="window-frame" aria-hidden="true"></i></div><div class="index-rail" aria-hidden="true"><span class="index-pointer pointer-i"><b>i</b></span><span class="index-pointer pointer-j"><b>j</b></span></div></div><aside class="counter-demo" aria-hidden="true"><header><span>COUNTER HASH MAP</span><small>changes only when A, B, or C crosses an edge</small></header><div class="counter-head"><span>letter</span><span>need</span><span>in window</span></div><div class="counter-states"><section class="counter-state count-one"><div><b>A</b><i>1</i><strong>1</strong></div><div class="missing"><b>B</b><i>1</i><strong>0</strong></div><div class="missing"><b>C</b><i>1</i><strong>0</strong></div><p>Missing <b>B, C</b></p></section><section class="counter-state count-two"><div><b>A</b><i>1</i><strong>1</strong></div><div><b>B</b><i>1</i><strong>1</strong></div><div class="missing"><b>C</b><i>1</i><strong>0</strong></div><p>Missing <b>C</b></p></section><section class="counter-state count-three"><div><b>A</b><i>1</i><strong>1</strong></div><div><b>B</b><i>1</i><strong>1</strong></div><div><b>C</b><i>1</i><strong>1</strong></div><p class="complete">Complete ✓</p></section><section class="counter-state count-four"><div class="missing"><b>A</b><i>1</i><strong>0</strong></div><div><b>B</b><i>1</i><strong>1</strong></div><div><b>C</b><i>1</i><strong>1</strong></div><p>Missing <b>A</b></p></section><section class="counter-state count-five"><div class="missing"><b>A</b><i>1</i><strong>0</strong></div><div class="extra"><b>B</b><i>1</i><strong>2</strong></div><div><b>C</b><i>1</i><strong>1</strong></div><p>Missing <b>A</b> · extra B</p></section><section class="counter-state count-six"><div><b>A</b><i>1</i><strong>1</strong></div><div class="extra"><b>B</b><i>1</i><strong>2</strong></div><div><b>C</b><i>1</i><strong>1</strong></div><p class="complete">Complete · extra B is okay</p></section><section class="counter-state count-seven"><div><b>A</b><i>1</i><strong>1</strong></div><div><b>B</b><i>1</i><strong>1</strong></div><div><b>C</b><i>1</i><strong>1</strong></div><p class="complete">Complete ✓</p></section><section class="counter-state count-eight"><div><b>A</b><i>1</i><strong>1</strong></div><div><b>B</b><i>1</i><strong>1</strong></div><div class="missing"><b>C</b><i>1</i><strong>0</strong></div><p>Missing <b>C</b></p></section><section class="counter-state count-nine"><div><b>A</b><i>1</i><strong>1</strong></div><div><b>B</b><i>1</i><strong>1</strong></div><div><b>C</b><i>1</i><strong>1</strong></div><p class="complete">C returns · complete</p></section><section class="counter-state count-ten"><div><b>A</b><i>1</i><strong>1</strong></div><div><b>B</b><i>1</i><strong>1</strong></div><div><b>C</b><i>1</i><strong>1</strong></div><p class="complete">Complete · best length 4</p></section></div></aside></div><p>Watch j add characters and i remove them. The Counter changes only when a required letter crosses an edge.</p></div></div>
<footer class="sample-panel-footer"><a href="{href(base,algorithm_preview)}">Work the full algorithm <span aria-hidden="true">&#8599;</span></a><button data-sample-next="design">Next: architecture <span aria-hidden="true">&#8594;</span></button></footer></article>
<article class="sample-panel" id="sample-design" role="tabpanel" aria-labelledby="sample-tab-design" aria-hidden="true" inert data-sample-panel="design">
<div class="sample-panel-grid"><div class="sample-problem"><span class="sample-kicker">DESIGN FOR RETRIES</span><h3>The card was charged, but the reply was lost. What should a retry do?</h3><div class="sample-given"><code>order-42</code><span>times out, then retries</span></div><div class="sample-answer"><span>ANSWER</span><strong>Reuse the same payment identity</strong><p>Look up the original attempt and return its result. A timeout means “unknown,” not “charge again.”</p></div></div>
<div class="payment-demo" role="group" aria-label="The first request charges the payment provider but loses its reply. The retry reuses order 42 and returns the recorded charge instead of charging again"><div class="visual-title"><span>ONE PURCHASE, ONE IDENTITY</span><small>animated event sequence</small></div><div class="payment-route first-attempt"><i>01</i><span>Checkout<br><small>order-42</small></span><b aria-hidden="true">→</b><span>Payment provider</span><strong>$42 charged</strong><u class="payment-packet" aria-hidden="true"></u></div><div class="lost-reply"><span aria-hidden="true">×</span> reply lost</div><div class="payment-route retry"><i>02</i><span>Retry<br><small>order-42</small></span><b aria-hidden="true">→</b><span class="payment-record">Attempt already recorded<br><small>charge ch_91</small></span><strong>Return result</strong><u class="payment-packet" aria-hidden="true"></u></div><div class="no-second-charge"><span aria-hidden="true">✓</span> No second provider call</div></div></div>
<footer class="sample-panel-footer"><a href="{href(base,design_preview)}">Open the checkout design <span aria-hidden="true">&#8599;</span></a><button data-sample-next="aws">Next: AWS <span aria-hidden="true">&#8594;</span></button></footer></article>
<article class="sample-panel" id="sample-aws" role="tabpanel" aria-labelledby="sample-tab-aws" aria-hidden="true" inert data-sample-panel="aws">
<div class="sample-panel-grid"><div class="sample-problem"><span class="sample-kicker">SURVIVE AN AZ FAILURE</span><h3>One Availability Zone goes down. How does the API stay online?</h3><div class="sample-given"><code>us-east-1a</code><span>is unavailable</span></div><div class="sample-answer"><span>ANSWER</span><strong>Route around the failure</strong><p>Run the service across zones. The load balancer sends traffic only to healthy targets, while the database fails over to its standby.</p></div></div>
<div class="aws-demo" role="group" aria-label="An Application Load Balancer stops routing to the failed task in Availability Zone A and keeps routing to a healthy task in Availability Zone B while an RDS Multi-AZ standby takes over"><div class="visual-title"><span>TRAFFIC AFTER THE FAILURE</span><small>animated failover</small></div><div class="aws-entry"><span>Users</span><b aria-hidden="true">→</b><strong>Application Load Balancer</strong><i class="aws-entry-packet" aria-hidden="true"></i></div><div class="aws-zones"><section class="failed"><header>AZ A <span>offline</span></header><div>ECS task <b>×</b></div><small>Removed by health check</small><i class="zone-packet" aria-hidden="true"></i></section><section class="healthy"><header>AZ B <span>healthy</span></header><div>ECS task <b>✓</b></div><small>Receives new traffic</small><i class="zone-packet" aria-hidden="true"></i></section></div><div class="aws-database"><span>RDS primary</span><b aria-hidden="true">⇢</b><span>Multi-AZ standby</span><strong>Failover</strong><i class="database-packet" aria-hidden="true"></i></div></div></div>
<footer class="sample-panel-footer"><a href="{href(base,aws_preview)}">Explore AWS infrastructure <span aria-hidden="true">&#8599;</span></a><button data-sample-next="algorithm">Back to algorithm <span aria-hidden="true">&#8634;</span></button></footer></article>
</div></div></section>
<section class="journey-section"><div class="section-label">THE CORE JOURNEY</div><h2>Choose a part,<br>or follow the full path.</h2><div class="journey-grid">{journey}</div></section>
<section class="optional-paths" aria-label="Optional learning paths"><a href="{href(base,ai_part)}"><span>OPTIONAL SPECIALIZATION</span><strong>AI systems</strong><small>Evaluation, budgets, permissions, and controlled actions.</small></a><a href="{href(base,interview)}"><span>OPTIONAL STUDIO</span><strong>Company interview practice</strong><small>Rehearse coding and design conversations under interview pressure.</small></a>{cs_card}</section>
<section class="home-finish"><div><span class="section-label">READY WHEN YOU ARE</span><h2>Start at the beginning.<br>Or browse for what you need.</h2></div><div><a class="primary-button" data-start href="{href(base,start)}">Start with Part A <span aria-hidden="true">&#8599;</span></a><button class="browse-button" data-open-contents aria-controls="sidebar" aria-expanded="false">Browse the curriculum</button><p data-resume-label>Progress stays on this device.</p></div></section>'''


def intro(b, page, sequence, base, authored):
    if page['kind']=='group':
        children=[p for p in sequence if p['kind']=='subject' and p['group']==page['group']]
        description=b.GROUPS[page['group']][2]
    else:
        children=[p for p in sequence if p.get('chapter')==page.get('chapter') and p.get('sub')]
        description=page.get('blurb') or page['summary']
    context_soup = BeautifulSoup(authored, 'html.parser')
    context = context_soup.select_one('.chapter-context')
    context_html = str(context) if context else ''
    page['headings'] = [
        {'id': h['id'], 'title': h.get_text(' ', strip=True), 'level': int(h.name[1])}
        for h in (context.find_all(['h2', 'h3']) if context else []) if h.get('id')
    ]
    rows=[]
    for child in children:
        if child.get('track_no'):
            number = f'T {child["track_no"]}' if page['kind']=='group' else f'T{child["track_no"]}.{child["sub"]:02}'
        else:
            number = f'CH {child["chapter"]:02}' if page['kind']=='group' else f'{child["chapter"]}.{child["sub"]:02}'
        rows.append(f'<li><span class="outline-index">{number}</span><div><h2><a href="{E(href(base,child))}">{E(child["title"])}</a></h2><p>{E(child.get("blurb") or child.get("section") or "Worked explanation and practice")}</p></div></li>')
    return (f'<h1>{E(page["title"])}</h1><p class="chapter-lede">{E(description)}</p>'+context_html+
            '<div class="chapter-contract"><span class="section-label">CHOOSE YOUR NEXT LESSON</span>'
            '<p>Parts group related chapters. Each lesson has a chapter.lesson address, such as 4.07. '
            'Open a title below, or use Next to follow the reading sequence. Within a lesson, On this page lists its sections.</p></div>'
            '<ol class="chapter-outline">'+''.join(rows)+'</ol>')


def shell(b, page, body, pages, sequence, base):
    position=page.get('position')
    prev=sequence[position-1] if position is not None and position>0 else None
    nxt=sequence[position+1] if position is not None and position+1<len(sequence) else None
    is_home=page['kind']=='home'
    is_locked_shell=page['kind']=='locked'
    # Public pages count only the public sequence; the track ends it, sealed.
    if nxt is not None and lock.is_locked(nxt) and not lock.is_locked(page): nxt=None
    total=len(sequence) if lock.is_locked(page) else len([p for p in sequence if not lock.is_locked(p)])
    subtitle = 'Curriculum overview' if is_home else 'PRIVATE TRACK' if is_locked_shell else ('COMPANY INTERVIEW STUDIO' if page['kind']=='company' else f'{part_label(page)} / {page.get("subject_title") or page.get("group_title")}' if page.get('group') else 'REFERENCE SHELF')
    if is_locked_shell:
        meta = 'LOCKED · PASSWORD REQUIRED'
    elif page.get('group') == 'crowdstrike':
        meta = (f'LESSON T{page["track_no"]}.{page["sub"]:02} · {page["sub"]} OF {page["step_count"]} IN CHAPTER' if page.get('sub')
                else 'CROWDSTRIKE TRACK · ITS OWN LEAGUE' if page['kind']=='group'
                else f'TRACK CHAPTER T{page["track_no"]}')
    else:
        meta= 'THE ENGINEERING GUIDE' if is_home else ('SENIOR SWE · COMPANY REHEARSAL' if page['kind']=='company' else f'LESSON {page["chapter"]}.{page["sub"]:02} · {page["sub"]} OF {page["step_count"]} IN CHAPTER' if page.get('sub') else part_label(page) if page['kind']=='group' else f'CHAPTER {page["chapter"]:02}' if page.get('chapter') else 'SUPPORTING MATERIAL')
    nav=''
    if position is not None and not is_home:
        previous=(f'<a class="previous-step" href="{href(base,prev)}"><span>← PREVIOUS</span><strong>{E(prev["title"])}</strong></a>' if prev else '<span></span>')
        nextlink=(f'<a class="next-step" data-complete="{E(page["src"])}" href="{href(base,nxt)}"><span>{"BEGIN THE JOURNEY" if is_home else "NEXT STEP"} →</span><strong>{E(nxt["title"])}</strong></a>' if nxt else '<div class="course-end"><span>YOU’VE REACHED THE END</span><strong>Return to a difficult problem. Explain it again, without the reference.</strong><button data-finish>Mark final step complete</button></div>')
        nav=f'<nav class="step-navigation" aria-label="Lesson sequence">{previous}{nextlink}</nav>'
    sticky_nav = ''
    if position is not None and not is_home:
        sticky_previous = (f'<a class="sticky-previous" href="{href(base,prev)}" '
                           f'aria-label="Previous: {E(prev["title"])}" title="{E(prev["title"])}">'
                           '<span aria-hidden="true">←</span> Previous</a>' if prev else
                           '<span class="sticky-disabled" aria-disabled="true">← Previous</span>')
        sticky_next = (f'<a class="sticky-next" data-complete="{E(page["src"])}" href="{href(base,nxt)}" '
                       f'aria-label="Next: {E(nxt["title"])}" title="{E(nxt["title"])}">'
                       'Next <span aria-hidden="true">→</span></a>' if nxt else
                       '<button class="sticky-finish" data-finish aria-label="Mark final step complete">Finish ✓</button>')
        sticky_nav = f'<nav class="sticky-sequence" aria-label="Sticky lesson sequence">{sticky_previous}{sticky_next}</nav>'
    top_note = '<div class="reader-meta"><span>'+meta+'</span><span>'+('READ · BUILD · REASON' if is_home else 'UNLOCK TO READ' if is_locked_shell else E(b.KINDS.get(page['kind'],('Lesson',''))[1] or 'GUIDED READING'))+'</span></div>'
    if is_home: body=overview(b,sequence,base)
    elif page['kind'] in ('group','subject'): body=intro(b,page,sequence,base,body)
    current=json.dumps({'src':page['src'],'url':href(base,page),'title':page['title'],'position':position,'total':total,'private':lock.is_locked(page)},ensure_ascii=True).replace('<','\\u003c')
    robots = '<meta name="robots" content="noindex,nofollow">' if is_locked_shell else ''
    # Hide lock forms until the saved unlock has been tried, so an unlocked reader never sees them flash.
    lock_check = '<script>if(/(?:^|;\\s*)j2s_track=/.test(document.cookie))document.documentElement.classList.add("lock-checking")</script>'
    mobile_location = (f'<span class="mobile-location"><span class="mobile-page-title" title="{E(page["title"])}">'
                       f'{"The Engineering Guide" if is_home else E(page["title"])}</span>'
                       f'<span class="mobile-page-position">{"Guided curriculum" if is_home else meta}</span></span>')
    browse_label = 'Browse curriculum' if is_home else 'Contents'
    motion_control = '' if is_home else '<button id="motion-toggle" aria-pressed="false">Animations on</button>'
    cf = getattr(b, 'CODEFIELD', None)
    codefield_js = (f'<script type="module" src="{base}{cf["js"]["file"]}" integrity="{cf["js"]["integrity"]}" '
                    'crossorigin="anonymous"></script>') if cf and page.get('codefield') else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(page['title'])} · The Engineering Guide</title><meta name="description" content="{E(page['summary'][:180])}"><meta name="color-scheme" content="light">{robots}{lock_check}<link rel="stylesheet" href="{base}{b.READER_ASSETS['css']['file']}" integrity="{b.READER_ASSETS['css']['integrity']}" crossorigin="anonymous"><style id="reader-styles">{b.READER_CSS}</style></head>
<body class="{'home' if is_home else 'lesson'}{' company-page' if page['kind']=='company' else ''}"><a class="skip-link" href="#reading">{'Skip to overview' if is_home else 'Skip to lesson'}</a><div class="mobile-bar"><button id="open-contents" data-open-contents aria-expanded="false" aria-controls="sidebar">☰ <span>{browse_label}</span></button>{mobile_location}</div><button class="drawer-backdrop" id="close-contents" aria-label="Close contents" tabindex="-1" hidden></button><aside class="sidebar" id="sidebar"><button class="mobile-close" id="dismiss-contents" aria-label="Close contents">×</button><nav aria-label="Table of contents">{toc(pages,sequence,page,base)}</nav></aside>
<noscript><style>.search-box,#motion-toggle,.mobile-bar button{{display:none}}@media(max-width:760px){{.sidebar{{position:relative;transform:none;width:100%;height:65vh;box-shadow:none}}.mobile-close{{display:none}}}}</style></noscript><div class="reading-shell"><header class="reading-bar{' has-sequence' if sticky_nav else ''}"><span>{E(subtitle)}</span><div class="reading-controls">{sticky_nav}<span id="saved-progress">{f'Step {position} of {total-1}' if position else 'Your guided curriculum'}</span>{motion_control}</div></header><div class="read-progress" aria-hidden="true"><span></span></div><main id="reading" tabindex="-1">{top_note}<article class="lesson-body">{body}</article>{nav}<footer class="page-footer"><span>THE ENGINEERING GUIDE</span><span>Understanding, through practice.</span></footer></main></div><script id="page-state" type="application/json">{current}</script><script>window.SITE_BASE={json.dumps(base)};</script><script src="{base}{b.READER_ASSETS['js']['file']}" integrity="{b.READER_ASSETS['js']['integrity']}" crossorigin="anonymous" defer></script>{codefield_js}</body></html>'''


def locked_shell(b, page, full_html, pages, sequence, base):
    """The page as published: chrome, a blurred placeholder, and the sealed page."""
    ghost = {'kind': 'locked', 'title': 'Private track', 'src': 'private-track', 'url': '/', 'position': None,
             'summary': 'A private track on this site. A password opens it on this device.'}
    body = lock.widget(lock.seal(full_html), 'page', lock.PAGE_VEIL, 'lock-page')
    return shell(b, ghost, body, pages, sequence, base)


def build(b):
    base=os.environ.get('SITE_BASE','/')
    if not base.startswith('/') or not base.endswith('/'): raise ValueError('SITE_BASE must be an absolute path ending in /')
    pages=b.collect()
    source_refs = content_checks.source_references(b.ROOT, pages); sequence=course.organize(pages)
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
    b.CODEFIELD = build_codefield(b)
    # Keep the old endpoints for existing bookmarks, but never reference them
    # from new HTML: old HTML and new styles must not share a cache identity.
    for filename in ('style.css','app.js'): shutil.copy(b.ROOT/'site'/filename,b.OUT/filename)
    for folder in ('curriculum','projects','practice','docs','scripts','indexes','companies','examples/ai-systems','examples/link-watcher','examples/architecture-starts','examples/reading-list-starter'):
        for f in (b.ROOT/folder).rglob('*'):
            if not f.is_file() or f.suffix=='.md' or {'node_modules','__pycache__'} & set(f.parts): continue
            if folder in {'examples/ai-systems', 'examples/link-watcher', 'examples/architecture-starts', 'examples/reading-list-starter'} and (f.suffix not in {'.py', '.json', '.txt'} or any(part.startswith('.') for part in f.relative_to(b.ROOT/folder).parts)): continue
            rel=f.relative_to(b.ROOT); dest=b.OUT/rel; dest.parent.mkdir(parents=True,exist_ok=True)
            if folder=='indexes' and f.suffix=='.json': dest.write_text(lock.redact_json(f.read_text()))
            else: shutil.copy(f,dest)
    resources = sorted(p.relative_to(b.OUT).as_posix() for p in b.OUT.rglob('*.html'))
    by_dest={b.dest_for(p['src']):p for p in pages}
    bodies={p['src']:(lock.evidence_tags(compose(b,p,have,by_dest)) if lock.is_locked(p) else lock.redact_html(compose(b,p,have,by_dest))) for p in pages}
    public=[p for p in pages if not lock.is_locked(p)]
    for p in public:
        p['headings']=[h for h in (p.get('headings') or []) if not lock.mentions(h['id']+' '+h['title'])]
    # Preserve old URLs while all reading movement uses the one sequence.
    for p in pages:
        out=b.OUT/b.dest_for(p['src']);out.parent.mkdir(parents=True,exist_ok=True)
        html=shell(b,p,bodies[p['src']],pages,sequence,base)
        out.write_text(locked_shell(b,p,html,pages,sequence,base) if lock.is_locked(p) else html)
    # Old gallery bookmarks remain usable; every visual retains its lesson context.
    gallery=b.OUT/'gallery';gallery.mkdir(exist_ok=True)
    items=[]
    for p in public:
        s=BeautifulSoup(bodies[p['src']],'html.parser')
        for img in s.find_all('img'):
            src=local_target(b,p,img.get('src',''))
            if src:items.append(f'<figure><img loading="lazy" src="{base}{src}" alt="{E(img.get("alt",""))}"><figcaption>{E(p["title"])}</figcaption></figure>')
    gp={'src':'gallery/README.md','url':'/gallery/','kind':'index','title':'Visual reference','summary':'Every teaching visual, preserved in context.'}
    (gallery/'index.html').write_text(shell(b,gp,'<h1>Visual reference</h1><div class="visual-gallery">'+''.join(items)+'</div>',pages,sequence,base))
    records=[{k:p.get(k) for k in ('src','title','url','kind','chapter','sub','section','position','headings','embedded')} for p in public]
    (b.OUT/'course.json').write_text(json.dumps({'sequence':[p['src'] for p in sequence if not lock.is_locked(p)],'pages':records},separators=(',',':')))
    (b.OUT/'search.json').write_text(json.dumps([{'title':p['title'],'url':href(base,p),'chapter':p.get('subject_title','Reference'),'text':lock.redact_text(b.prose_of(p['text']))} for p in public],separators=(',',':')))
    inventory = {'schema': 1, 'renderer': b.renderer_inputs(), 'pages': {}, 'assets': {}, 'resource_html': resources}
    for p in pages:
        inventory['pages'][p['src']] = {
            'output': b.dest_for(p['src']), 'source_sha256': hashlib.sha256(p['text'].encode()).hexdigest(),
            'presentation': 'generated-overview' if p['src'] == 'README.md' or p['kind'] in ('group', 'subject') else 'authored-lesson',
            'mermaid': p['expected_mermaid'], 'source_images': p['source_images'],
            'code_inclusions': p['expected_code'], 'references': source_refs[p['src']], 'locked': lock.is_locked(p)}
    for file in (b.OUT/'assets').rglob('*'):
        if file.is_file(): inventory['assets'][file.relative_to(b.OUT).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    content_checks.validate(b.OUT, inventory)
    # The published inventory names nothing sealed; the full one was checked above.
    published = dict(inventory, pages={k: dict(v, references=[r for r in v['references'] if not lock.mentions(json.dumps(r))])
                                       for k, v in inventory['pages'].items() if not v['locked']},
                     assets={k: v for k, v in inventory['assets'].items() if not lock.mentions(k)})
    (b.OUT/'content-inventory.json').write_text(json.dumps(published, indent=2) + '\n')
    print(f'Built {len(pages)} pages, {len(sequence)-1} guided steps, {len(have)} diagrams; full TOC and inline code.')
    return 0
