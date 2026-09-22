"""Rebuild editable SVG teaching animations and their static storyboards (stdlib only)."""
from pathlib import Path
from html import escape
import json
import textwrap

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'/'learning'
OUT.mkdir(parents=True,exist_ok=True)

def text(x,y,value,size=16,color='#26342e',anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>'

def lines(x,y,value,width=34,size=18,color='#26342e'):
    return ''.join(text(x,y+i*27,line,size,color) for i,line in enumerate(textwrap.wrap(value,width=width)))

def base(title,height,body,css=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {height}" width="760" height="{height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">Teaching timeline. States are illustrative, not measured latency. A still storyboard is linked beside this image.</desc>
<style>text{{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}} {css}</style>
<rect width="760" height="{height}" rx="14" fill="#faf9f7"/>
{text(28,32,'LEARN / PREDICT / EXPLAIN',11,'#706a61')}
{lines(28,65,title,56,22)}
{body}</svg>'''

def render(d):
    key=d['key'];title=d['title']
    css=''.join(f'.step{i}{{opacity:0;animation:s{i} 16s step-end infinite}} @keyframes s{i}{{0%,100%{{opacity:0}} {i*25}%,{i*25+24.99}%{{opacity:1}}}}' for i in range(4))
    # At 0%, step0 must be visible. Without animation the last frame is useful.
    css+=' .step3{opacity:1} @media(prefers-reduced-motion:reduce){.frame{animation:none!important;opacity:0}.step3{opacity:1}}'
    body=''
    for x,label,color in [(24,'WITHOUT THE MECHANISM','#a45134'),(392,'WITH THE MECHANISM','#27664c')]:
        body+=f'<rect x="{x}" y="104" width="344" height="270" rx="10" fill="white" stroke="#ddd8cf"/>'
        body+=text(x+18,133,label,12,color)
    for i in range(4):
        body+=f'<g class="frame step{i}">'
        for x,states,color in [(24,d['before'],'#a45134'),(392,d['after'],'#27664c')]:
            body+=text(x+18,172,f'STATE {i+1} / 4',13,color)
            body+=lines(x+18,213,states[i],29,20)
            for j in range(4):
                body+=f'<rect x="{x+18+j*77}" y="326" width="65" height="7" rx="3" fill="{color if j<=i else "#e8e4dd"}"/>'
            body+=text(x+18,359,'Cause → state change → observable result',11,'#706a61')
        body+='</g>'
    body+=lines(28,409,d['question'],92,15)
    (OUT/f'{key}-compare.svg').write_text(base(title,480,body,css))
    # Trace: arrows accumulate so the learner sees the causal sequence.
    css=''
    for i in range(4):
        css+=f'.event{i}{{animation:e{i} 16s step-end infinite}} @keyframes e{i}{{0%{{opacity:{1 if i==0 else .12}}} {i*25}%{{opacity:1}} 99.99%{{opacity:1}} 100%{{opacity:.12}}}}'
    css+=' @media(prefers-reduced-motion:reduce){.event{animation:none!important;opacity:1}}'
    body='<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#27664c"/></marker></defs>'
    xs=[125,380,635]
    for x,actor in zip(xs,d['actors']):
        body+=f'<rect x="{x-100}" y="102" width="200" height="42" rx="7" fill="#eef2ef" stroke="#b7c8bd"/>'
        body+=text(x,129,actor,16,anchor='middle')
        body+=f'<line x1="{x}" y1="144" x2="{x}" y2="450" stroke="#c9c4bb" stroke-dasharray="4 6"/>'
    for i,(a,b,label) in enumerate(d['messages']):
        y=195+i*73
        body+=f'<g class="event event{i}">'
        if a==b:
            body+=f'<path d="M{xs[a]},{y} h65 v23 h-65" fill="none" stroke="#27664c" stroke-width="2" marker-end="url(#arrow)"/>'
        else:
            body+=f'<line x1="{xs[a]}" y1="{y}" x2="{xs[b]}" y2="{y}" stroke="#27664c" stroke-width="2" marker-end="url(#arrow)"/>'
        body+=f'<rect x="48" y="{y-28}" width="664" height="25" rx="4" fill="#faf9f7"/>'
        body+=text(58,y-10,f'{i+1}. {label}',15)
        body+='</g>'
    body+=lines(28,492,d['question'],90,15)
    (OUT/f'{key}-trace.svg').write_text(base(title+' · implementation sequence',560,body,css))
    body=text(28,119,'STEP',12,'#706a61')+text(90,119,'WITHOUT',12,'#a45134')+text(416,119,'WITH',12,'#27664c')
    for i in range(4):
        y=150+i*108
        body+=f'<rect x="24" y="{y-10}" width="712" height="98" rx="7" fill="white" stroke="#e4dfd6"/>'
        body+=text(42,y+23,str(i+1),22)
        body+=lines(90,y+16,d['before'][i],29,16,'#85472f')
        body+=lines(416,y+16,d['after'][i],29,16,'#27664c')
    body+=lines(28,607,d['question'],91,15)
    (OUT/f'{key}-still.svg').write_text(base(title+' · all four states',675,body))

if __name__=='__main__':
    data=json.loads((ROOT/'scripts/learning_storyboards.json').read_text())
    for item in data:render(item)
    print(f'Rendered {len(data)*2} animations and {len(data)} still storyboards.')
