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
    problem_sources={p['path'] for p in bank}
    assert len(bank)==42 and all(p['path'] in sequence for p in bank)
    briefs=[p for p in sequence if '/projects/' in p and p.endswith('.md')]
    assert len(briefs)==40, f'Missing standalone briefs: {len(briefs)}'
    stages=list((ROOT/'projects/reading-list/stages').glob('*/README.md'))
    assert len(stages)==5 and all(str(p.relative_to(ROOT)) in sequence for p in stages)
    design_practice={
        '03-production/01-system-design': ('api-quota','ticket-inventory','realtime-chat','social-feed','video-processing','checkout-payment'),
        '03-production/04-observability': ('slow-request',),
        '03-production/05-reliability': ('durable-jobs',),
        '04-scale-and-evolution/01-data-at-scale': ('document-search','trending-counts'),
        '04-scale-and-evolution/03-ai-systems': ('personalized-ranking',),
        '04-scale-and-evolution/04-migrations': ('regional-failover',),
    }
    for chapter, names in design_practice.items():
        introduction=f'curriculum/{chapter}/README.md'
        for name in names:
            source=f'curriculum/{chapter}/problems/{name}.md'
            assert source in sequence and sequence.index(introduction)<sequence.index(source), source
            article=BeautifulSoup(output_for(source).read_text(),'html.parser').select_one('article.lesson-body')
            assert len(article.select('img[src*="/assets/design-practice/"]')) >= 2, source
            assert article.select_one('.task-brief blockquote'), source
            assert len(article.select('.example-card')) >= 3, source
            words=article.get_text(' ',strip=True)
            assert 'Senior follow-up' in words and 'Staff follow-up' in words,source
    foundations=[p for p in sequence if '/02-data-structures-algorithms/lessons/' in p]
    assert len(foundations)==23
    assert max(map(sequence.index,foundations)) < min(sequence.index(p['path']) for p in bank)
    assert sequence[sequence.index(foundations[-1])+1]=='curriculum/01-code/03-coding-practice/README.md'
    project_sources={str(p.relative_to(ROOT)) for p in (ROOT/'curriculum').rglob('*.md') if '/projects/' in p.as_posix()}
    project_sources|={str(p.relative_to(ROOT)) for p in (ROOT/'projects/reading-list/stages').rglob('README.md')}
    assert len(project_sources)==45
    expected_product_pages={
        'curriculum/02-applications/01-backend/projects/a-public-form.md',
        'curriculum/02-applications/02-databases/projects/a-receipt-tracker.md',
        'curriculum/02-applications/03-frontend/projects/a-shared-reading-list.md',
        'curriculum/02-applications/05-security/projects/a-shift-schedule.md',
        'projects/reading-list/stages/01-it-works/README.md',
    }
    diagrams=set(); embedded=0; local_jumps=[]; previous_next=0; rehearsed=0; framed=0; product_visuals=0
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
        if src in problem_sources:
            heading=next((h for h in article.find_all('h2') if h.get_text(strip=True)=='What the interviewer expects'),None)
            assert heading,src
            scenario=next((h for h in article.find_all('h3') if h.get_text(strip=True)=='Test-case scenarios to settle before coding'),None)
            assert scenario and len(scenario.find_next('div',class_='example-cards').select('.example-card'))>=6,src
            assert article.select_one('.task-brief blockquote'),src
            assert article.select_one('details.concept-refresher:not([open])'),src
            for card in article.select('.example-card'):
                assert len(card.select('.example-pair dt'))==2 and len(card.select('.example-pair dd'))==2,src
            rehearsed+=1
        if src in project_sources:
            assert article.select_one('.task-brief blockquote') and len(article.select('.example-card'))>=3,src
            heading=next((h for h in article.find_all('h2') if h.get_text(strip=True)=='What you are expected to hand over'),None)
            assert heading,src
            gates=next((h for h in article.find_all('h3') if h.get_text(strip=True)=='How the review conversation gets harder'),None)
            assert gates and gates.find_next('table') and len(gates.find_next('table').select('tr'))-1==6,src
            framed+=1
            if src in expected_product_pages:
                assert article.select_one('img[src*="/assets/product/"]'),src
                product_visuals+=1
        toc=soup.select_one('nav[aria-label="Table of contents"]');assert toc,src
        assert len(toc.select('.toc-area:not(.reference-area):not(.company-area)'))==4,src
        assert len(toc.select('.toc-area:not(.reference-area):not(.company-area) .toc-chapter'))==18,src
        assert len(toc.select('.company-area .toc-chapter'))==5,src
        assert len(toc.select('[aria-current="page"]'))==1,src
        for link in soup.select('[data-heading]'):
            assert article.find(id=link['data-heading']), (src,link['data-heading'])
        for a in article.find_all('a',href=True):
            url=urlsplit(a['href'])
            if not url.scheme and not a.has_attr('data-start'):
                if src=='companies/README.md' and 'studio-link' in a.get('class',[]):
                    assert a['href'].endswith('.html'),(src,a['href'])
                else:local_jumps.append((src,a['href']))
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
    assert len(diagrams)>=398,len(diagrams)
    company_sources=[f'companies/{name}.md' for name in ('openai','reddit','meta','databricks','observe')]
    assert sequence[-6:]==['companies/README.md']+company_sources
    for src in company_sources:
        article=BeautifulSoup(output_for(src).read_text(),'html.parser').select_one('article.lesson-body')
        assert len(article.select('.tablewrap'))>=3 and article.find('img',src=lambda s:s and '/assets/companies/' in s),src
        assert len(article.select('.mer'))>=2,src
        tables=article.select('.tablewrap table')
        assert len(tables[0].select('tbody tr'))==8 and len(tables[1].select('tbody tr'))==5,src
        assert all(article.find('h2',string=lambda t:t and name in t.lower()) for name in ('room','coding bench','design board','niche mock')),src
    assert rehearsed==42 and framed==45 and product_visuals==5,(rehearsed,framed,product_visuals)
    originals=list((ROOT/'assets').rglob('*.svg'))
    # This includes the four expected-product mockups added for UI project
    # briefs. Every source visual is copied byte-identically into the site.
    assert len(originals)>=134
    for svg in originals:
        assert hashlib.sha256(svg.read_bytes()).digest()==hashlib.sha256((OUT/svg.relative_to(ROOT)).read_bytes()).digest(),svg
    print(f'PASS {len(pages)} pages: full 4-part / 18-chapter TOC, 23 foundations before practice, {previous_next-1} contiguous steps, all 42 problems and 5 project stages, no in-body lesson jumps.')
    print('PASS 42 interview expectation blocks, 45 project deliverables with six review gates, and 5 expected-product placements.')
    print(f'PASS {embedded} exact inline files; all {len(originals)} source SVGs copied byte-identically; {len(diagrams)} Mermaid diagrams displayed; heading anchors resolve; assessor keys excluded from sequence.')

if __name__=='__main__':main()
