"""Geometric animations for array windows, cache fan-out, and worker capacity."""
from render_learning import OUT, base, text, lines

CSS=''.join(f'.f{i}{{opacity:0;animation:f{i} 16s step-end infinite}} @keyframes f{i}{{0%,100%{{opacity:0}} {i*25}%,{i*25+24.99}%{{opacity:1}}}}' for i in range(4))+' .f3{opacity:1} @media(prefers-reduced-motion:reduce){.frame{animation:none!important;opacity:0}.f3{opacity:1}}'

def save(key,title,body):
    (OUT/f'{key}-mechanism.svg').write_text(base(title,500,body,CSS))

body=''
for stage,(left,right) in enumerate([(0,0),(0,1),(2,2),(2,3)]):
    body+=f'<g class="frame f{stage}">'
    body+=text(32,123,f'READ {stage+1} / 4',13,'#706a61')
    for i,char in enumerate('abba'):
        x=170+i*110
        active=left<=i<=right
        body+=f'<rect x="{x}" y="172" width="84" height="76" rx="9" fill="{"#e3efe7" if active else "#f1ede6"}" stroke="{"#27664c" if active else "#c7c0b5"}" stroke-width="2"/>'
        body+=text(x+42,218,char,30,anchor='middle')+text(x+42,157,str(i),15,'#706a61','middle')
    body+=f'<path d="M{170+left*110},268 v13 H{254+right*110} v-13" stroke="#27664c" stroke-width="3" fill="none"/>'
    body+=text(170+left*110,310,f'left = {left}',17)+text(254+right*110,340,f'right = {right}',17,anchor='end')
    caption=['The first character starts a unique window.','No repetition: extend right, keep left.','Second b repeats: left jumps past the old b.','Old a is outside the window; left must stay at 2.'][stage]
    body+=lines(32,390,caption,76,20)
    body+=text(32,459,f'Current length = {right-left+1}     Best length = {1 if stage==0 else 2}',17)
    body+='</g>'
save('sliding-window','Watch the window move through a b b a',body)

body=''
for stage in range(4):
    body+=f'<g class="frame f{stage}">'
    for x,mode,color in [(25,'UNBOUNDED START','#a45134'),(395,'THREE WORKERS','#27664c')]:
        body+=text(x+10,124,mode,14,color)
        active=set(range(12)) if mode.startswith('UNBOUNDED') else set(range(stage*3,min(12,stage*3+3)))
        done=set() if mode.startswith('UNBOUNDED') else set(range(stage*3))
        for j in range(12):
            xx=x+10+(j%4)*77; yy=159+(j//4)*67
            status='RUN' if j in active else ('DONE' if j in done else 'WAIT')
            fill=color if j in active else ('#dce9e0' if j in done else '#eee9e0')
            ink='white' if j in active else '#3e5146'
            body+=f'<rect x="{xx}" y="{yy}" width="65" height="51" rx="6" fill="{fill}"/>'
            body+=text(xx+32,yy+20,f'job {j+1}',12,ink,'middle')+text(xx+32,yy+39,status,12,ink,'middle')
        body+=text(x+10,389,'12 active / capacity 3' if mode.startswith('UNBOUNDED') else f'3 active / {9-stage*3} waiting',18,color)
    body+=lines(32,438,'Completion frees a slot; queued work starts only when a worker is available.',83,17)
    body+='</g>'
save('bounded-workers','Concurrency is a resource budget',body)

body=''
for stage in range(4):
    body+=f'<g class="frame f{stage}">'
    for x,mode,color in [(25,'INDEPENDENT MISSES','#a45134'),(395,'ONE SHARED LOAD','#27664c')]:
        body+=text(x+10,125,mode,14,color)
        for j in range(6):
            xx=x+26+j*50
            body+=f'<circle cx="{xx}" cy="175" r="13" fill="{color}"/>'
            if stage>=1:
                dest=x+152 if mode.startswith('ONE') else xx
                body+=f'<line x1="{xx}" y1="189" x2="{dest}" y2="252" stroke="{color}" stroke-width="2"/>'
        body+=f'<rect x="{x+15}" y="253" width="300" height="43" rx="6" fill="#eee9e0" stroke="#b5afa4"/>'
        body+=text(x+165,280,'Expired key' if stage<2 else ('In-flight promise' if mode.startswith('ONE') else 'Every caller loads'),16,anchor='middle')
        if stage>=2:
            for j in (range(1) if mode.startswith('ONE') else range(6)):
                xx=x+152 if mode.startswith('ONE') else x+26+j*50
                body+=f'<line x1="{xx}" y1="296" x2="{xx}" y2="350" stroke="{color}" stroke-width="3"/>'
        body+=f'<rect x="{x+15}" y="350" width="300" height="48" rx="6" fill="#eef2ef" stroke="#8ea996"/>'
        body+=text(x+165,380,'Database: '+('0 calls' if stage<2 else ('1 call' if mode.startswith('ONE') else '6 calls')),18,anchor='middle')
    captions=['Six requests arrive for the same key.','All observe a miss. Electing a loader is the crucial step.','Without coordination, the database repeats identical work.','A successful shared load fills the cache and releases waiters.']
    body+=lines(32,442,captions[stage],83,17)
    body+='</g>'
save('cache','A cache miss can become a traffic multiplier',body)
print('Rendered 3 geometric mechanism animations.')
