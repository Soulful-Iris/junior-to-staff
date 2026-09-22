#!/usr/bin/env python3
"""Acceptance checks for a complete, linear, content-preserving reader."""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get('SITE_OUT', ROOT/'site/out'))

def output_for(src):
    return OUT/(src[:-len('README.md')]+'index.html' if src.endswith('README.md') else src[:-3]+'.html')

def main():
    manifest = json.loads((OUT/'course.json').read_text())
    assets = json.loads((OUT/'reader-assets.json').read_text())
    for kind, item in assets.items():
        payload = (OUT/item['file']).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item['sha256']
        assert item['sha256'][:16] in item['file']
    pages={p['src']:p for p in manifest['pages']}
    sequence=manifest['sequence']
    assert len(sequence)==len(set(sequence))
    assert not any('assessor' in src for src in sequence), 'Answer keys entered candidate sequence'
    bank=json.loads((ROOT/'indexes/problem-bank.json').read_text())
    assert len(bank)==42 and all(p['path'] in sequence for p in bank)
    briefs=[p for p in sequence if '/projects/' in p and p.endswith('.md')]
    assert len(briefs)==40, f'Missing standalone briefs: {len(briefs)}'
    stages=list((ROOT/'projects/reading-list/stages').glob('*/README.md'))
    assert len(stages)==5 and all(str(p.relative_to(ROOT)) in sequence for p in stages)
    assert sequence.index(bank[0]['path'])==sequence.index('curriculum/01-code/02-data-structures-algorithms/lessons/01-maps.md')+1
    diagrams=set(); embedded=0; local_jumps=[]; previous_next=0
    for src,p in pages.items():
        soup=BeautifulSoup(output_for(src).read_text(),'html.parser')
        css = soup.find('link', rel='stylesheet')
        assert css and css['href'].endswith(assets['css']['file']), src
        assert css['integrity'] == assets['css']['integrity'], src
        inline = soup.find('style', id='reader-styles')
        assert inline and hashlib.sha256(inline.string.encode()).hexdigest() == assets['css']['sha256'], src
        js = soup.find('script', src=True)
        assert js and js['src'].endswith(assets['js']['file']), src
        assert js['integrity'] == assets['js']['integrity'], src
        article=soup.select_one('article.lesson-body');assert article,src
        toc=soup.select_one('nav[aria-label="Table of contents"]');assert toc,src
        assert len(toc.select('.toc-area:not(.reference-area)'))==4,src
        assert len(toc.select('.toc-area:not(.reference-area) .toc-chapter'))==17,src
        assert len(toc.select('[aria-current="page"]'))==1,src
        for link in soup.select('[data-heading]'):
            assert article.find(id=link['data-heading']), (src,link['data-heading'])
        for a in article.find_all('a',href=True):
            url=urlsplit(a['href'])
            if not url.scheme and not a.has_attr('data-start'):local_jumps.append((src,a['href']))
        for img in article.find_all('img'):
            if '/assets/mermaid/' in img.get('src',''):diagrams.add(Path(img['src']).name)
            assert img.get('alt'),src
            if img.get('data-still'):
                target = img['data-still']
                resting = OUT/target.lstrip('/') if target.startswith('/') else output_for(src).parent/target
                assert resting.is_file(),(src,target)
        for panel in article.select('figure.code-file'):
            original=ROOT/panel['data-source'];assert original.is_file(), original
            assert panel.code.get_text()==original.read_text(),original
            embedded+=1
        if src in sequence:
            i=sequence.index(src);nav=soup.select_one('.step-navigation');assert nav,src
            if i+1<len(sequence):
                link=nav.select_one('a.next-step');assert link and link['href'].endswith(pages[sequence[i+1]]['url']),src
                sticky=soup.select_one('.sticky-next')
                assert sticky and sticky['href']==link['href'] and sticky['data-complete']==src,src
            else:
                assert soup.select_one('.sticky-finish[data-finish]'),src
            if i>0:
                link=nav.select_one('a.previous-step');assert link and link['href'].endswith(pages[sequence[i-1]]['url']),src
                sticky=soup.select_one('.sticky-previous')
                assert sticky and sticky['href']==link['href'],src
            previous_next+=1
    assert not local_jumps,local_jumps[:10]
    assert len(diagrams)==387,len(diagrams)
    originals=list((ROOT/'assets').rglob('*.svg'))
    assert len(originals)==107
    for svg in originals:
        assert hashlib.sha256(svg.read_bytes()).digest()==hashlib.sha256((OUT/svg.relative_to(ROOT)).read_bytes()).digest(),svg
    print(f'PASS {len(pages)} pages: full 4-part / 17-chapter TOC, {previous_next-1} contiguous steps, all 42 problems and 5 project stages, no in-body lesson jumps.')
    print(f'PASS {embedded} exact inline files; all 107 original SVGs unchanged; all 387 Mermaid diagrams displayed; heading anchors resolve; assessor keys excluded from sequence.')

if __name__=='__main__':main()
