"""Native SVG motion studies: persistent topology, causal movement, readable stills.

No shared four-slide timeline. Each study owns its timing and choreography.
Run the renderer to regenerate animations and their explanatory static alternatives.
"""
from pathlib import Path
from html import escape
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/learning'
BG='#faf9f7'; INK='#1f2b24'; GREEN='#2f6f4e'; ORANGE='#c2703d'
GRAY='#ded9d1'; MUTED='#6d6459'; PALE='#eef2ef'
STILL=False
DURATION=8

def node(tag, attrs=None, body=''):
    return '<'+tag+''.join(f' {k}="{escape(str(v),quote=True)}"' for k,v in (attrs or {}).items())+'>'+body+'</'+tag+'>'
def tween(attr, stops, ease=False):
    """Per-element timing. Values at intermediate positions are real interpolation."""
    if STILL:return ''
    times,values=zip(*stops)
    attrs={'attributeName':attr,'values':';'.join(map(str,values)),
           'keyTimes':';'.join(map(str,times)),'dur':f'{DURATION}s','repeatCount':'indefinite',
           'calcMode':'spline' if ease else 'linear'}
    if ease:attrs['keySplines']=';'.join(['.42 0 .2 1']*(len(times)-1))
    return node('animate',attrs)
def text(x,y,label,size=15,color=INK,anchor='start',body=''):
    return node('text',{'x':x,'y':y,'font-size':size,'fill':color,'text-anchor':anchor},escape(str(label))+body)
def rect(x,y,w,h,color=GREEN,fill=PALE,body='',rx=5):
    return node('rect',{'x':x,'y':y,'width':w,'height':h,'rx':rx,'stroke':color,'stroke-width':1.5,'fill':fill},body)
def box(x,y,w,h,label,color=GREEN,fill=PALE):
    return rect(x,y,w,h,color,fill)+text(x+w/2,y+h/2+5,label,14,INK,'middle')
def path(d,color=GRAY,width=1.5,arrow=False,body='',dash=None):
    a={'d':d,'stroke':color,'stroke-width':width,'fill':'none','stroke-linecap':'round','stroke-linejoin':'round'}
    if arrow:a['marker-end']='url(#arrow)'
    if dash:a['stroke-dasharray']=dash
    return node('path',a,body)
def dot(x,y,r=5,color=GREEN,body=''):
    return node('circle',{'cx':x,'cy':y,'r':r,'fill':color},body)
def moving(body,points,stops=None,fade=None):
    """Move a whole object on a path; never animate transform as a generic attribute."""
    if STILL:return ''
    a={'path':points,'dur':f'{DURATION}s','repeatCount':'indefinite','calcMode':'linear'}
    if stops:
        a['keyTimes']=';'.join(str(t) for t,p in stops)
        a['keyPoints']=';'.join(str(p) for t,p in stops)
    return node('g',{},body+node('animateMotion',a)+(tween('opacity',fade) if fade else ''))
def pulse(points,color=GREEN,start=0,end=1,r=4):
    stops=[(0,0)]
    if start>0:stops.append((start,0))
    stops.append((end,1))
    if end<1:stops.append((1,1))
    fade=[(0,0 if start else 1)]
    if start>0:fade.extend([(max(.0001,start-.001),0),(start,1)])
    if end<1:fade.extend([(end-.001,1),(end,0),(1,0)])
    else:fade.append((1,1))
    return moving(dot(0,0,r,color),points,stops,fade)
def reveal(body,start,end=1):
    if STILL:return body
    stops=[(0,0),(start,0),(start+.025,1)]
    if end<1:stops.extend([(end-.025,1),(end,0),(1,0)])
    else:stops.append((1,1))
    return node('g',{},body+tween('opacity',stops))
def footer(a,b=''):
    return path('M32 350 H728')+text(32,379,a,15)+text(32,402,b,13,MUTED)
def heading(x,y,label,color=MUTED):return text(x,y,label,11,color)
def cells(vals,x=55,y=120,step=90,w=65):
    return ''.join(rect(x+i*step,y,w,48,GRAY,BG)+text(x+i*step+w/2,y+30,v,21,INK,'middle')+text(x+i*step+w/2,y-10,i,11,MUTED,'middle') for i,v in enumerate(vals))

def maps():
    s=heading(45,74,'TARGET 9 · LOOK UP BEFORE INSERTING')+cells([2,7,11,15],45,100,82,60)
    s+=box(475,95,230,155,'',GRAY,BG)+heading(496,119,'EARLIER VALUE → INDEX')
    s+=path('M75 151 V208 Q75 222 90 222 H510 V165',GREEN,1.5,True)
    s+=text(130,212,'insert 2 → 0',14,GREEN)
    s+=reveal(text(500,170,'2 → 0',23,GREEN),.25)
    s+=moving(text(0,5,'2',19,GREEN,'middle'),'M75 125 V222 H510 V165',[(0,0),(.04,0),(.28,1),(1,1)],[(0,1),(.28,1),(.3,0),(1,0)])
    s+=path('M157 151 V282 H665 V183',ORANGE,1.5,True)+text(215,275,'7 needs 2: one lookup',14,ORANGE)
    s+=pulse('M157 151 V282 H665 V183',ORANGE,.34,.65)
    s+=path('M475 185 H387 V320 H75 V170',GREEN,1.5,True)
    s+=pulse('M475 185 H387 V320 H75 V170',GREEN,.65,.92)
    s+=text(445,317,'return (0, 1)',19,GREEN)
    return s+footer('The second value finds work remembered from the first.','Expected O(n) time · O(n) space · lookup first prevents using one item twice.')

def window():
    s=cells(list('abba'),160,130,100,72)+heading(45,78,'LONGEST SUBSTRING WITH NO REPEATED CHARACTER')
    # Right admits the duplicate first; left then excludes the earlier b.
    xs=[(0,154),(.37,154),(.5,354),(.94,354),(1,154)]
    ws=[(0,84),(.12,84),(.25,184),(.31,184),(.37,284),(.5,84),(.61,84),(.75,184),(.94,184),(1,84)]
    s+=rect(354,121,184,66,GREEN,'none',tween('x',xs,True)+tween('width',ws,True))
    s+=text(360,229,'L',18,GREEN,body=tween('x',[(t,v+6) for t,v in xs],True))
    s+=text(510,253,'R',18,ORANGE,body=tween('x',[(0,210),(.12,210),(.25,310),(.31,310),(.37,410),(.61,410),(.75,510),(.94,510),(1,210)],True))
    s+=path('M292 111 Q342 67 392 111',ORANGE,1.5,True)+text(342,94,'duplicate b',13,ORANGE,'middle')
    s+=text(45,304,'left = max(left, last_seen[char] + 1)',20,GREEN)
    return s+footer('Extend right. On a duplicate, move left past its previous occurrence.','The final a was already outside the window. Best length stays 2. Loop reset is not an algorithm step.')

def prefix():
    s=cells([1,-1,1],45,108,80,58)+heading(45,74,'TARGET 1 · FINAL PREFIX = 1')
    s+=path('M45 206 H700',GRAY)+text(45,237,'prefix boundaries',12,MUTED)
    for x,label in [(80,'0'),(250,'1'),(420,'0'),(590,'1')]:s+=dot(x,206,7,GREEN)+text(x,187,label,20,GREEN,'middle')
    s+=path('M80 214 Q80 293 335 293 Q590 293 590 214',GREEN,2)+path('M420 214 Q420 260 505 260 Q590 260 590 214',ORANGE,2)
    s+=pulse('M80 214 Q80 293 335 293 Q590 293 590 214',GREEN,.05,.75,5)
    s+=pulse('M420 214 Q420 260 505 260 Q590 260 590 214',ORANGE,.05,.75,5)
    s+=text(400,85,'count[0] = 2',23,GREEN)+text(400,117,'two earlier starts',15,MUTED)
    s+=text(520,328,'+2 matches here',18,GREEN)
    return s+footer('Equal prefix values can occur at different boundaries. Keep their count.','At the last element, [1, −1, 1] and [1] both sum to 1. Total matches over the array: 3.')

def binary():
    s=heading(45,74,'LOWER BOUND · FIRST VALUE ≥ 2')+cells([1,2,2,5,8,12],55,125,95,70)
    s+=rect(145,118,0,63,GREEN,'none',tween('x',[(0,48),(.53,48),(.7,143),(.94,143),(1,48)],True)+tween('width',[(0,560),(.08,560),(.27,275),(.34,275),(.52,85),(.57,85),(.7,0),(.94,0),(1,560)],True))
    s+=node('g',{},path('M0 0 l-7 12 h14 Z',ORANGE)+text(0,34,'mid',13,ORANGE,'middle')+node('animateMotion',{'path':'M375 187 H185 H90 H185','dur':f'{DURATION}s','repeatCount':'indefinite','calcMode':'linear','keyTimes':'0;.3;.55;.75;1','keyPoints':'0;.5;.75;1;1'}) if not STILL else path('M185 187 l-7 12 h14 Z',ORANGE))
    s+=text(55,276,'qualifies → hi = mid',19,GREEN)+text(400,276,'too small → lo = mid + 1',19,ORANGE)
    s+=text(55,320,'[0,6) → [0,3) → [0,1) → [1,1)',19)
    return s+footer('The interval contracts around the insertion point; duplicates stay eligible.','Answer: index 1. O(log n) comparisons · O(1) space. The rewind marks a new demonstration.')

def graph():
    ns=[(90,165,'A'),(270,98,'B'),(270,245,'C'),(460,165,'D'),(650,165,'E')]
    s=heading(40,69,'BREADTH FIRST · EACH EDGE HAS EQUAL COST')
    for a,b,start,end in [(0,1,.05,.27),(0,2,.05,.27),(1,3,.31,.55),(2,3,.31,.55),(3,4,.61,.83)]:
        x,y,_=ns[a];xx,yy,_=ns[b];p=f'M{x} {y} L{xx} {yy}';s+=path(p,GRAY,2)+pulse(p,GREEN,start,end,5)
    for i,(x,y,label) in enumerate(ns):
        t=[.01,.26,.26,.55,.83][i]
        s+=node('circle',{'cx':x,'cy':y,'r':25,'fill':BG,'stroke':GREEN,'stroke-width':2})
        s+=node('circle',{'cx':x,'cy':y,'r':31,'fill':'none','stroke':ORANGE,'stroke-width':2},tween('r',[(0,27),(t,27),(min(t+.1,.96),39),(1,39)])+tween('opacity',[(0,0),(t,0),(t+.01,1),(min(t+.12,.98),0),(1,0)]))
        s+=text(x,y+6,label,20,INK,'middle')+text(x,y+49,'d='+str([0,1,1,2,3][i]),13,GREEN,'middle')
    s+=text(40,319,'A  →  [B, C]  →  [D]  →  [E]',20,GREEN)
    return s+footer('Two edges discover D; only the first discovery enqueues it.','Mark visited at enqueue time. FIFO processes complete distance layers: O(V + E).')

def stack():
    s=heading(40,74,'DAILY TEMPERATURES · WAITING FOR A WARMER DAY')+cells([73,74,71,75],45,100,82,60)
    s+=heading(490,80,'PENDING STACK')+path('M480 115 V291 H690 V115',GREEN,2)
    s+=box(510,235,150,42,'day 1 · 74',GRAY,BG)+box(510,185,150,42,'day 2 · 71',GRAY,BG)
    s+=path('M321 148 C400 148 430 205 500 205',ORANGE,1.5,True)+pulse('M321 148 C400 148 430 205 500 205',ORANGE,.02,.22)
    s+=moving(box(-65,-20,130,40,'day 2 → wait 1'), 'M585 205 C690 190 675 313 555 313 H230',[(0,0),(.24,0),(.52,1),(1,1)],[(0,0),(.24,0),(.25,1),(.76,1),(.79,0),(1,0)])
    s+=moving(box(-65,-20,130,40,'day 1 → wait 2'), 'M585 255 C670 300 430 313 230 313',[(0,0),(.54,0),(.86,1),(1,1)],[(0,0),(.54,0),(.55,1),(.95,1),(1,0)])
    s+=text(45,216,'75 resolves 71, then 74',19,ORANGE)+text(45,249,'result: [1, 2, 1, 0]',19,GREEN)
    return s+footer('Pop from the top while the new temperature is warmer.','Each index enters and leaves once: O(n) time. Ghost slots show where the resolved nodes came from.')

def dp():
    s=heading(40,73,'COINS [1, 3, 4] · AMOUNT 6')
    s+=heading(45,110,'GREEDY',ORANGE)+text(45,152,'4 + 1 + 1',26,ORANGE)+text(45,188,'3 coins',17,ORANGE)
    for y,label,v in [(105,'1 + dp[5]',3),(186,'1 + dp[3]',2),(267,'1 + dp[2]',3)]:
        s+=box(320,y,165,46,label)+path(f'M485 {y+23} C535 {y+23} 520 209 585 209',GREEN if v==2 else GRAY,2)
        s+=pulse(f'M485 {y+23} C535 {y+23} 520 209 585 209',GREEN if v==2 else ORANGE, {105:.03,186:.3,267:.57}[y],{105:.27,186:.54,267:.81}[y])
        s+=text(500,y+14,v,14,GREEN if v==2 else MUTED)
    s+=box(585,181,125,56,'min = 2')+text(590,268,'3 + 3',24,GREEN)
    return s+footer('Evaluate every valid last coin, then keep the smallest candidate.','The recurrence exposes a choice greedy misses. O(amount × coin types) time; O(amount) space.')

def lru():
    s=heading(40,73,'CAPACITY 2 · START WITH [A, B], THEN get(A)')
    s+=heading(92,108,'LEAST RECENT')+heading(510,108,'MOST RECENT',GREEN)
    s+=path('M210 187 H510',GRAY,2,True)+path('M585 216 V285 H155 V216',GRAY,1.5,True)
    s+=moving(box(-60,-23,120,46,'A',GREEN),'M150 187 C150 87 580 87 580 187',[(0,0),(.1,0),(.52,1),(1,1)])
    s+=moving(box(-60,-23,120,46,'B',ORANGE),'M580 187 H150',[(0,0),(.15,0),(.52,1),(1,1)])
    if STILL:s+=box(90,164,120,46,'B',ORANGE)+box(520,164,120,46,'A')
    s+=text(45,321,'Next put(C): evict B, then append C.',20)
    return s+footer('Move the existing A node to the most-recent end. No new slot is added.','A hash map locates the node; a doubly linked list unlinks and appends it in O(1).')

def config():
    s=heading(40,72,'BROAD ROLLOUT',ORANGE)+heading(420,72,'CANARY + HEALTH GATE',GREEN)
    for off in [0,380]:
        s+=box(105+off,95,130,40,'config v2')
        for i in range(6):
            x=65+off+(i%3)*90;y=207+(i//3)*73
            p=f'M{170+off} 135 L{x+25} {y}'
            s+=path(p,GRAY)
            if off==0 or i==0:s+=pulse(p,ORANGE,.03,.29+i*.035)
            color=ORANGE if off==0 or i==0 else GREEN
            s+=rect(x,y,53,38,color,BG)+text(x+26,y+25,i+1,16,INK,'middle')
            if color==ORANGE:s+=reveal(path(f'M{x+8} {y+6} l37 26 M{x+45} {y+6} l-37 26',ORANGE,2),.31+i*.035,.79 if off else .97)
        if off:
            s+=path('M470 207 C404 185 425 129 477 116',GREEN,1.5,True)+pulse('M470 207 C404 185 425 129 477 116',GREEN,.62,.84)
            s+=text(545,166,'STOP',13,ORANGE)+text(417,334,'rollback 1 · preserve 5',16,GREEN)
        else:s+=text(40,334,'6 exposed · broad recovery',16,ORANGE)
    return s+footer('The same defective configuration meets a different distribution boundary.','The health signal must stop promotion. Shared dependencies can still cross cohort boundaries.')

def retries():
    s=heading(40,72,'RETRIES AT THREE LAYERS',ORANGE)+heading(435,72,'ONE RETRY OWNER',GREEN)
    for off in [0,385]:
        for y,label in [(97,'API'),(177,'service'),(257,'data client')]:s+=box(110+off,y,135,34,label,ORANGE if not off else GREEN)
        for level in range(3):
            count=3**(level+1) if not off else (3 if level==2 else 1)
            for k in range(count):
                x=70+off+210*(k+.5)/count
                p=f'M{177+off} {131+level*80} Q{x} {143+level*80} {x} {160+level*80}'
                s+=path(p,ORANGE if not off else GREEN,.8)
                s+=pulse(p,ORANGE if not off else GREEN,.02+level*.28+k*.001,.26+level*.28+k*.001,2.6)
        s+=text(177+off,338,'up to 27 calls' if not off else 'up to 3 calls',20,ORANGE if not off else GREEN,'middle')
    return s+footer('Three total attempts at each layer can multiply into 3 × 3 × 3 leaf calls.','Assign retry ownership; bound attempts and elapsed time. Jitter limits synchronized retries.')

def capacity():
    s=heading(40,72,'STOP TWO BEFORE STARTING',ORANGE)+heading(425,72,'START TWO BEFORE STOPPING',GREEN)
    for off in [0,385]:
        for i in range(12):
            x=45+off+(i%4)*76;y=99+(i//4)*48
            s+=rect(x,y,59,31,GRAY,BG)
            if i<8:s+=rect(x,y,59,31,GREEN,PALE)
            else:
                stops=([(0,1),(.18,1),(.28,0),(.75,0),(.87,1),(1,1)] if not off and i<10 else [(0,0),(1,0)] if not off else [(0,int(i<10)),(.12,int(i<10)),(.26,1),(.72,1),(.86,int(i<10)),(1,int(i<10))])
                s+=node('g',{'opacity':int(i<10)},rect(x,y,59,31,GREEN,PALE)+tween('opacity',stops))
        s+=heading(45+off,266,'CAPACITY · DEMAND 850 REQ/S')
        widths=[(0,240),(.18,240),(.3,192 if not off else 288),(.7,192 if not off else 288),(.87,240),(1,240)]
        s+=rect(42+off,282,240,17,GREEN,PALE,tween('width',widths,True))
        s+=path(f'M{246+off} 273 V311',ORANGE,2)
        s+=text(45+off,333,'1,000 → 800 → 1,000' if not off else '1,000 → 1,200 → 1,000',17,GREEN)
    return s+footer('Correct code can still overload the service during replacement.','Toy budget: 100 req/s per task. An 800 req/s fleet builds a 50 req/s backlog at this demand.')

def status():
    s=heading(40,72,'THE RESULT AND ITS STATUS VIEW ARE SEPARATE BOUNDARIES')
    s+=box(40,101,155,48,'result: done')+box(289,101,166,48,'completion log')+box(550,101,170,48,'status view')
    s+=path('M195 125 H289 M455 125 H550',GRAY,2,True)+pulse('M195 125 H289',GREEN,.01,.2)
    s+=path('M365 149 V200 H634 V149',GREEN,1.5,True)+pulse('M365 149 V200 H634 V149',GREEN,.22,.57)
    s+=text(410,190,'completed · v3',15,GREEN)
    s+=path('M180 268 H590 V222',ORANGE,1.5,True)+pulse('M180 268 H590 V222',ORANGE,.59,.88)
    s+=text(42,274,'late v2',17,ORANGE)+path('M578 220 l24 16 M602 220 l-24 16',ORANGE,2)
    s+=text(40,326,'Apply only when incoming version > stored version.',20,GREEN)
    return s+footer('The completion advances the view. The later arrival of v2 does not undo it.','A repeated version is a no-op only when its payload agrees; disagreement is a conflict.')

def hotkeys():
    s=heading(40,73,'ONE HOT KEY',ORANGE)+heading(425,73,'FOUR INDEPENDENT BUCKETS',GREEN)
    for off in [0,385]:
        for i in range(4):
            x=52+off+i*76;h=150 if not off and i==0 else 0 if not off else 37.5
            s+=rect(x,165,51,146,GRAY,BG)
            s+=rect(x+7,305-h,37,h,ORANGE if not off else GREEN,ORANGE if not off else GREEN,
                tween('height',[(0,0),(.12,0),(.72,h),(.95,h),(1,0)])+tween('y',[(0,305),(.12,305),(.72,305-h),(.95,305-h),(1,305)]),0)
            s+=path(f'M{x} 245 h51',INK,1.5)+text(x+25,337,chr(65+i),13,MUTED,'middle')
            if h:
                for j in range(3):s+=pulse(f'M{80+off+j*85} 99 Q{x+25} 113 {x+25} 153',ORANGE if not off else GREEN,j*.17,.45+j*.17,3)
        s+=text(45+off,96,'250 / 0 / 0 / 0' if not off else '62.5 each',15)
    return s+footer('Route independent writes across keys; one hot key cannot use its idle neighbors.','Bars grow to arrival rates, not stored bytes. Black line = 100 units/s; logical ≠ physical partition.')

def workers():
    s=heading(40,72,'WAITING')+heading(295,72,'THREE ACTIVE SLOTS',GREEN)+heading(590,72,'DONE')
    for r in range(3):
        y=122+r*74
        s+=path(f'M130 {y} H304 M430 {y} H615',GRAY,1.5,True)+box(304,y-22,126,44,'',GRAY,BG)+text(311,y+5,'slot '+str(r+1),12,MUTED)
        for batch in range(3):
            y0=111+r*74+batch*17;end=.29+batch*.3;start=batch*.3
            body=dot(0,0,9,GREEN)+text(0,4,1+r+batch*3,10,BG,'middle')
            from math import hypot
            first=hypot(365-(60+batch*24),y-y0); fraction=first/(first+262+batch*22)
            s+=moving(body,f'M{60+batch*24} {y0} L365 {y} H{627+batch*22}',[(0,0)]+([(start,0)] if start else [])+[(start+.1,fraction),(start+.19,fraction),(end,1)]+([(1,1)] if end<1 else []))
    if STILL:
        for j in range(9):s+=dot(627+(j%3)*22,119+(j//3)*74,8,GREEN)
    return s+footer('A job travels into a slot, runs there, then leaves before the next admission.','Nine jobs, at most three executing. Concurrency is a resource limit, not a requests-per-second limit.')

def cache():
    s=heading(40,73,'INDEPENDENT MISSES',ORANGE)+heading(425,73,'ONE SHARED IN-FLIGHT LOAD',GREEN)
    for off in [0,385]:
        for j in range(6):
            x=55+off+j*51;s+=dot(x,110,6,ORANGE if not off else GREEN)
            p=f'M{x} 116 L{180+off if off else x} 215'
            s+=path(p,GRAY)+pulse(p,GREEN if off else ORANGE,.02,.3)
        s+=box(40+off,215,300,38,'independent loaders' if not off else 'shared promise',GRAY,BG)
        for j in range(1 if off else 6):
            x=180+off if off else 55+j*51
            p=f'M{x} 253 V288';s+=path(p,GRAY)+pulse(p,GREEN if off else ORANGE,.32,.5)
        s+=box(40+off,288,300,39,'DB: 6 reads' if not off else 'DB: 1 read')
        if off:
            s+=pulse(f'M{180+off} 288 V253',GREEN,.52,.64)
            for j in range(6):s+=pulse(f'M{180+off} 215 L{55+off+j*51} 116',GREEN,.67,.94)
    return s+footer('Six callers converge on one loader; its result fans back out to all waiters.','This promise coordinates one process. Cross-process stampedes need a separate strategy.')

def idem():
    s=heading(40,73,'SAME LOGICAL JOB · TWO DELIVERIES')
    s+=box(40,105,140,42,'delivery A')+box(40,229,140,42,'retry of A',ORANGE)
    s+=box(335,151,164,58,'insert if absent')+box(592,151,124,58,'one result')
    for p in ['M180 126 L335 166','M180 250 L335 194','M499 180 H592']:s+=path(p,GRAY,1.5,True)
    s+=pulse('M180 126 L335 166',GREEN,.03,.24)+pulse('M499 180 H592',GREEN,.28,.45)
    s+=pulse('M180 250 L335 194',ORANGE,.51,.73)
    s+=path('M417 209 V305 H110 V278',GREEN,1.5,True)+pulse('M417 209 V305 H110 V278',GREEN,.75,.98)
    s+=text(439,286,'return prior success',15,GREEN)+text(340,130,'atomic boundary',13,MUTED)
    return s+footer('The store admits one insert. A matching retry receives the saved result.','Reuse the logical job ID and verify its payload. External side effects need their own protocol.')

def upload():
    s=heading(40,73,'CONTROL PLANE: PERMISSION · DATA PLANE: BYTES')
    s+=box(45,133,147,55,'browser')+box(498,90,202,51,'API: authorize')+box(498,270,202,54,'S3: object')
    s+=path('M192 144 L498 110',GREEN,1.5,True)+path('M498 133 L192 173',GREEN,1.5,True)
    s+=path('M118 188 V297 H498',ORANGE,4,True)
    s+=pulse('M192 144 L498 110',GREEN,.01,.16)+pulse('M498 133 L192 173',GREEN,.18,.36)
    for i in range(5):s+=pulse('M118 188 V297 H498',ORANGE,.38+i*.075,.67+i*.075,5)
    s+=text(255,108,'metadata',14,GREEN)+text(240,183,'scoped, expiring permission',14,GREEN)+text(166,282,'large bytes bypass the API',16,ORANGE)
    return s+footer('Authorize first, return upload permission, then send the byte stream to S3.','Finalize only after checking the uploaded object and ownership. Arrow thickness distinguishes bytes.')

def browser_race():
    s=heading(40,72,'NEWER INTENT WINS · RESPONSES CAN ARRIVE OUT OF ORDER')
    s+=text(40,128,'cat · v1',16,ORANGE)+text(40,226,'car · v2',16,GREEN)
    s+=path('M155 124 H650',ORANGE,1.5,True)+path('M285 222 H465',GREEN,1.5,True)
    s+=pulse('M155 124 H650',ORANGE,.02,.8,6)+pulse('M285 222 H465',GREEN,.24,.5,6)
    s+=path('M465 228 V300 H355',GREEN,1.5,True)+pulse('M465 228 V300 H355',GREEN,.5,.64)
    s+=box(135,278,220,46,'UI: car · generation 2')
    s+=path('M650 130 V300 H502',ORANGE,1.5,True)+pulse('M650 130 V300 H502',ORANGE,.81,.96)
    s+=path('M491 287 l20 26 M511 287 l-20 26',ORANGE,2)+text(526,333,'reject obsolete v1',14,ORANGE)
    s+=text(308,205,'arrives first',14,GREEN)+text(496,108,'arrives last',14,ORANGE)
    return s+footer('Commit a response only if its generation still matches the current request.','Aborting obsolete work can save resources; the generation guard protects the UI either way.')

def expiry():
    s=heading(40,72,'SAME EXPIRY → ONE SPIKE',ORANGE)+heading(425,72,'JITTER → SPREAD REFRESH WORK',GREEN)
    for off in [0,385]:
        for i in range(6):
            y=105+i*32;end=260 if not off else 140+i*30
            s+=text(40+off,y+5,'k'+str(i+1),12,MUTED)
            s+=path(f'M{75+off} {y} H{end+off}',GRAY,7)
            s+=dot(end+off,y,4,ORANGE if not off else GREEN)
        s+=path(f'M{75+off} 310 H{335+off}',GRAY,1,True)
        if not off:p=f'M{75+off} 304 H{239+off} Q{256+off} 218 {263+off} 300 H{332+off}'
        else:p=f'M{75+off} 304 Q{140+off} 304 {155+off} 293 T{205+off} 293 T{255+off} 293 T{330+off} 304'
        s+=path(p,ORANGE if not off else GREEN,2)
        s+=path(f'M{75+off} 88 V316',INK,1,body=tween('d',[(0,f'M{75+off} 88 V316'),(1,f'M{335+off} 88 V316')]))
    return s+footer('Equal TTLs synchronize misses. Randomized expiry spreads their arrival times.','Jitter does not reduce total refresh work. Pair it with coalescing, stale policy, and a load budget.')

def backpressure():
    s=heading(40,73,'UNBOUNDED BUFFER',ORANGE)+heading(425,73,'BOUNDED ADMISSION',GREEN)
    for off in [0,385]:
        ident='reservoir'+str(off)+('s' if STILL else 'm')
        s+=node('defs',{},node('clipPath',{'id':ident},rect(95+off,140,165,156,GRAY,BG)))
        h=148 if not off else 70
        waves=node('path',{'d':f'M{80+off} 0 Q{120+off} -10 {160+off} 0 T{240+off} 0 T{300+off} 0 V180 H{80+off} Z','fill':ORANGE if not off else GREEN,'transform':f'translate(0 {296-h})'},'' if STILL else node('animateTransform',{'attributeName':'transform','type':'translate','values':f'0 296;0 {296-h};0 {296-h};0 296','keyTimes':'0;.65;.93;1','dur':f'{DURATION}s','repeatCount':'indefinite'}))
        s+=node('g',{'clip-path':f'url(#{ident})'},waves)+rect(95+off,140,165,156,GRAY,'none')
        s+=path(f'M{177+off} 100 V132',GRAY,2,True)+path(f'M{177+off} 298 V330',GREEN,2,True)
        for i in range(3):s+=pulse(f'M{147+off+i*30} 93 V137',ORANGE if not off else GREEN,i*.12,.3+i*.12)
        s+=text(95+off,126,'arrival > service',15)+text(100+off,316,'queue',13,MUTED)
        if off:s+=path(f'M{260+off} 176 H{325+off} V116',ORANGE,2,True)+text(657,100,'429 / 503',12,ORANGE)
        else:s+=text(42,332,'memory and wait time grow',15,ORANGE)
    return s+footer('A queue stores a rate mismatch. A bound forces an explicit overload response.','Choose reject, defer, or shed. Watch age as well as depth; autoscaling cannot erase startup delay.')

def breaker():
    s=heading(40,74,'STOP SPENDING REQUESTS ON A FAILING DEPENDENCY')
    s+=box(40,137,136,51,'caller')+box(562,137,155,51,'dependency')
    s+=path('M176 162 H330 M410 162 H562',GRAY,2)
    s+=dot(330,162,5,INK)+dot(410,162,5,INK)
    s+=node('g',{'transform':'rotate(-42 330 162)'},path('M330 162 H410',ORANGE,4)+(node('animateTransform',{'attributeName':'transform','type':'rotate','values':'0 330 162;0 330 162;-42 330 162;-42 330 162;0 330 162;0 330 162','keyTimes':'0;.2;.3;.62;.72;1','dur':f'{DURATION}s','repeatCount':'indefinite'}) if not STILL else ''))
    s+=pulse('M176 162 H562',ORANGE,.02,.17)
    for i in range(3):s+=pulse('M176 162 H315 Q325 162 325 190 V259 H176',ORANGE,.32+i*.06,.51+i*.06)
    s+=path('M315 162 Q325 162 325 190 V259 H176',GRAY,1.5,True)+text(45,282,'fail fast while open',16,ORANGE)
    s+=pulse('M176 162 H562',GREEN,.73,.85)+pulse('M562 177 H420',GREEN,.86,.96)
    s+=text(410,246,'one probe after cooldown',16,GREEN)
    s+=text(43,328,'closed  →  open  →  half-open probe  →  closed if healthy',18)
    return s+footer('An open circuit blocks normal calls. A bounded probe tests recovery.','Thresholds, cooldown, and fallback are policy. A failed probe reopens the circuit.')

def replication():
    s=heading(40,74,'ASYNC REPLICA · A WRITE ACK DOES NOT MEAN EVERY READER HAS IT')
    for y,label,last in [(123,'PRIMARY',8),(247,'REPLICA',7)]:
        s+=heading(40,y,label,GREEN if last==8 else ORANGE)
        for j in range(5):s+=box(200+j*91,y-25,75,42,'v'+str(4+j),GRAY,BG)
    s+=rect(561,95,76,48,GREEN,'none')+text(40,157,'acknowledge v8',15,GREEN)
    s+=path('M600 140 C710 145 710 220 600 222',GREEN,2,True)+pulse('M600 140 C710 145 710 220 600 222',GREEN,.4,.88,6)
    s+=node('g',{},rect(562,220,75,42,GRAY,BG)+text(599,247,'pending',12,ORANGE,'middle')+tween('opacity',[(0,1),(.86,1),(.9,0),(1,0)]))
    s+=path('M300 292 H518 V270',ORANGE,1.5,True)+pulse('M300 292 H518 V270',ORANGE,.15,.35)
    s+=text(42,311,'immediate read can see v7',18,ORANGE)
    return s+footer('Replication catches up later; route freshness-sensitive reads deliberately.','Options include primary reads or a version watermark. Availability and latency tradeoffs remain.')

def outbox():
    s=heading(40,73,'ONE DATABASE TRANSACTION · TWO RECORDS')
    s+=rect(55,98,320,206,GREEN,'none')+box(85,121,255,49,'business row')+box(85,231,255,49,'outbox event')
    s+=path('M211 170 V231',GRAY,2,True)+pulse('M211 170 V231',GREEN,.08,.28)
    s+=path('M60 105 V296 H365 V105 Z',GREEN,3,body=tween('stroke-dashoffset',[(0,1020),(.3,0),(1,0)]),dash='1020')
    s+=box(440,224,112,49,'relay')+box(615,224,108,49,'broker')
    s+=path('M340 255 H440 M552 249 H615',GRAY,2,True)+pulse('M340 255 H440',GREEN,.34,.5)+pulse('M552 249 H615',GREEN,.51,.66)
    s+=path('M670 273 V315 H493 V278',ORANGE,1.5,True)+pulse('M493 249 H615',ORANGE,.77,.93)
    s+=text(427,125,'crash after publish?',16,ORANGE)+text(427,153,'relay may publish again',14,MUTED)
    return s+footer('Commit the business change and its event together; publish after commit.','The relay can duplicate events. Consumers still need idempotency; the outbox closes the lost-event gap.')

def deadline():
    s=heading(40,73,'PARENT DEADLINE 300 ms · PASS REMAINING TIME TO CHILDREN')
    for y,label,start,w,color in [(125,'request',0,600,GREEN),(201,'auth',0,100,GRAY),(277,'database',100,500,ORANGE)]:
        s+=text(40,y,label,15,color if color!=GRAY else MUTED)+rect(138+start,y-24,w,34,GRAY,BG)
        stops=[(0,0),(.14,w),(1,w)] if label=='auth' else [(0,0),(.14,0),(.83,w),(1,w)] if label=='database' else [(0,0),(.83,w),(1,w)]
        s+=rect(138+start,y-24,w,34,color,color,tween('width',stops),2)
    s+=path('M738 91 V318',ORANGE,2)+text(738,337,'300 ms',13,ORANGE,'end')
    s+=text(245,183,'auth spent 50 ms',14,MUTED)+text(340,244,'at most 250 ms remain',15,ORANGE)
    return s+footer('A child inherits the remaining budget, not a fresh full timeout.','Reserve reply/cleanup time too. Cancellation is cooperative; downstream work may outlive the caller.')

def token_bucket():
    s=heading(40,74,'BURST CAPACITY AND REFILL RATE ARE DIFFERENT LIMITS')
    s+=node('circle',{'cx':153,'cy':185,'r':67,'fill':'none','stroke':GRAY,'stroke-width':12})
    s+=node('circle',{'cx':153,'cy':185,'r':67,'fill':'none','stroke':GREEN,'stroke-width':12,'stroke-dasharray':'421','stroke-dashoffset':105,'transform':'rotate(-90 153 185)'},tween('stroke-dashoffset',[(0,421),(.65,0),(.93,0),(1,421)]))
    s+=text(153,183,'refill',19,GREEN,'middle')+text(153,207,'tokens / sec',13,MUTED,'middle')
    s+=box(310,115,166,143,'',GRAY,BG)+heading(320,102,'BUCKET CAPACITY: 4')
    for j in range(4):
        s+=node('circle',{'cx':336+j*37,'cy':181,'r':11,'fill':BG,'stroke':GRAY,'stroke-width':1.5})
        if not STILL:s+=dot(336+j*37,181,11,GREEN,tween('opacity',[(0,1),(.119+j*.09,1),(.12+j*.09,0),(1,0)]))
        s+=pulse(f'M{336+j*37} 181 Q{510+j*15} 181 624 259',GREEN,.12+j*.09,.37+j*.09,7)
    s+=box(546,270,168,46,'admitted requests')+path('M476 127 H624 V198',ORANGE,1.5,True)
    s+=text(504,105,'no token → reject',15,ORANGE)+pulse('M476 127 H624 V198',ORANGE,.72,.94)
    return s+footer('A token pays for admission. A burst can use stored tokens, then refill limits arrivals.','Ghost tokens mark bucket slots. Distributed enforcement needs atomic accounting and a clock policy.')

def pool():
    s=heading(40,74,'MANY REQUESTS SHARE A SMALL CONNECTION BUDGET')
    for j in range(6):s+=box(40,95+j*37,118,29,'request '+str(j+1),GRAY,BG)
    for j in range(2):
        y=150+j*111;s+=box(309,y-25,150,50,'connection '+str(j+1))+path(f'M459 {y} L635 207',GRAY,2,True)
        for b in range(3):
            r=j+b*2;p=f'M158 {109+r*37} L309 {y} H459 L635 207';s+=path(f'M158 {109+r*37} L309 {y}',GRAY,1)+pulse(p,GREEN,.02+b*.3,.25+b*.3,5)
    s+=box(635,171,84,70,'DB')+text(222,324,'acquire → use → release in finally',18,GREEN)
    return s+footer('Bound connections and the wait to acquire one. Always release a checked-out resource.','Per-process pools add up across replicas; pool size × replica count must fit the database budget.')

def traffic_shift():
    s=heading(40,73,'SHIFT TRAFFIC ONLY AFTER THE NEW FLEET IS READY')
    s+=box(45,158,147,58,'router')+box(510,103,194,58,'blue · old')+box(510,249,194,58,'green · new')
    top='M192 180 C350 180 340 132 510 132';bottom='M192 196 C350 196 340 278 510 278'
    s+=path(top,GRAY,1)+path(bottom,GRAY,1)
    s+=path(top,ORANGE,6,body=tween('stroke-width',[(0,8),(.2,8),(.8,1),(1,1)]))
    s+=path(bottom,GREEN,6,body=tween('stroke-width',[(0,1),(.2,1),(.8,8),(1,8)]))
    for i in range(3):s+=pulse(top,ORANGE,.03+i*.11,.25+i*.11)+pulse(bottom,GREEN,.5+i*.1,.73+i*.1)
    s+=text(294,105,'drain old work',16,ORANGE)+text(289,325,'increase new admissions',16,GREEN)
    return s+footer('Traffic share moves from blue to green; existing requests still need time to finish.','Health checks are necessary, not sufficient. Observe errors and latency; retain a rollback route.')

def waterfall():
    s=heading(40,74,'SERIAL: 600 ms',ORANGE)+heading(425,74,'INDEPENDENT PARALLEL: 200 ms',GREEN)
    for off in [0,385]:
        ident='sweep'+str(off)+('s' if STILL else 'm')
        s+=node('defs',{},node('clipPath',{'id':ident},rect(90+off,93,260,225,GRAY,BG,tween('width',[(0,0),(.85,260),(1,260)]))))
        bars=''
        for j,label in enumerate(['A','B','C']):
            y=123+j*65;s+=text(40+off,y+5,label,15)
            x=90+off+(j*80 if not off else 0);bars+=rect(x,y-17,80,34,GREEN if off else ORANGE,PALE)
        s+=node('g',{'clip-path':f'url(#{ident})'},bars)
        s+=path(f'M{90+off} 308 H{350+off}',GRAY,1.5,True)+text(90+off,334,'time →',12,MUTED)
    return s+footer('Start independent I/O together; total wait approaches the slowest call.','Dependent operations stay ordered. Bound fan-out and handle partial failure; concurrency has a cost.')

def heap_sift():
    s=heading(40,73,'MIN HEAP · AFTER REMOVING THE ROOT, REPAIR ONE BRANCH')
    points=[(375,112),(220,213),(530,213),(125,306),(310,306)]
    for a,b in [(0,1),(0,2),(1,3),(1,4)]:s+=path(f'M{points[a][0]} {points[a][1]} L{points[b][0]} {points[b][1]}',GRAY,2)
    for x,y in points:s+=node('circle',{'cx':x,'cy':y,'r':25,'fill':BG,'stroke':GRAY,'stroke-width':1.5})
    s+=moving(dot(0,0,22,ORANGE)+text(0,7,'9',21,BG,'middle'),'M375 112 L220 213 L125 306',[(0,0),(.12,0),(.44,.5828),(.53,.5828),(.84,1),(1,1)])
    s+=moving(text(0,7,'4',21,GREEN,'middle'),'M220 213 Q255 100 375 112',[(0,0),(.12,0),(.44,1),(1,1)])
    s+=moving(text(0,7,'7',21,GREEN,'middle'),'M125 306 Q105 225 220 213',[(0,0),(.53,0),(.84,1),(1,1)])
    s+=text(530,220,'6',21,INK,'middle')+text(310,313,'8',21,INK,'middle')
    if STILL:s+=text(375,119,'4',21,GREEN,'middle')+text(220,220,'7',21,GREEN,'middle')+text(125,313,'9',21,ORANGE,'middle')
    return s+footer('Swap with the smaller child until the parent is no larger than its children.','One path through a complete binary tree: O(log n). A heap orders parents, not all siblings.')

def trie():
    s=heading(40,74,'PREFIX "ca" · SHARED CHARACTERS SHARE A PATH')
    pts=[(90,180,'root'),(235,180,'c'),(385,180,'a'),(560,110,'r'),(560,263,'t'),(685,110,'d')]
    for a,b in [(0,1),(1,2),(2,3),(2,4),(3,5)]:
        x,y,_=pts[a];xx,yy,_=pts[b];s+=path(f'M{x} {y} L{xx} {yy}',GRAY,2)
    s+=path('M90 180 H385',GREEN,4,body=tween('stroke-dashoffset',[(0,295),(.4,0),(1,0)]),dash='295')
    for x,y,label in pts:s+=dot(x,y,24,GREEN if label in ['c','a'] else GRAY)+text(x,y+5,label,15,BG if label in ['c','a'] else INK,'middle')
    s+=pulse('M385 180 L560 110 H685',GREEN,.42,.85)+pulse('M385 180 L560 263',ORANGE,.42,.85)
    s+=text(600,263,'cat',16,ORANGE)+text(620,80,'car / card',16,GREEN)
    return s+footer('Walk the prefix once, then explore descendants for matching words.','Mark word endings explicitly: car is a word even though card continues. Work includes output size.')

def backtrack():
    s=heading(40,74,'SUBSETS OF [A, B] · ONE WORKING PATH, COPIED AT LEAVES')
    pts=[(380,107,'[]'),(215,204,'[A]'),(550,204,'[]'),(100,300,'[A,B]'),(295,300,'[A]'),(475,300,'[B]'),(660,300,'[]')]
    for a,b in [(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)]:
        x,y,_=pts[a];xx,yy,_=pts[b];s+=path(f'M{x} {y} L{xx} {yy}',GRAY,1.5)
    for x,y,label in pts:s+=box(x-40,y-17,80,34,label,GRAY,BG)
    route='M380 107 L215 204 L100 300 L215 204 L295 300 L215 204 L380 107 L550 204 L475 300 L550 204 L660 300 L550 204 L380 107'
    s+=pulse(route,GREEN,0,1,6)+text(55,117,'down: choose',14,GREEN)+text(55,146,'up: undo',14,ORANGE)
    return s+footer('Depth-first traversal returns to a choice point before trying the next branch.','Append → recurse → pop. Copy at a leaf; otherwise every saved answer may alias the same list.')

def intervals():
    s=heading(40,74,'SORT BY START · MERGE OVERLAPPING CLOSED INTERVALS')
    for j,(lo,hi) in enumerate([(1,4),(3,6),(8,10)]):
        y=121+j*57;x=85+lo*52;w=(hi-lo)*52
        s+=path(f'M{x} {y} H{x+w}',GREEN if j<2 else ORANGE,12)+text(x,y-16,f'[{lo}, {hi}]',14)
    s+=path('M130 306 H690',GRAY,1.5,True)
    s+=rect(137,276,260,21,GREEN,PALE,tween('width',[(0,156),(.2,156),(.65,260),(1,260)]),2)+rect(501,276,104,21,ORANGE,PALE)
    s+=path('M293 134 V271',GRAY,1,True)+path('M397 188 V271',GRAY,1,True)
    s+=text(167,335,'[1, 6]',16,GREEN)+text(521,335,'[8, 10]',16,ORANGE)
    return s+footer('Extend the current end to max(end, next.end); a gap starts another interval.','O(n log n) for sorting, O(n) for the scan. Half-open intervals need an explicit touching policy.')

def index_tree():
    s=heading(40,74,'INDEX SEEK · PRUNE RANGES BEFORE READING ROWS')
    s+=box(285,92,185,45,'separator: 40')
    for x,label in [(75,'keys < 40'),(495,'keys ≥ 40')]:s+=box(x,192,185,45,label,GRAY,BG)
    s+=path('M335 137 L167 192 M422 137 L587 192',GRAY,2)
    for i in range(6):
        x=52+i*116;s+=box(x,290,98,36,str(i*10)+'–'+str(i*10+9),GRAY,BG)
        s+=path(f'M{167 if i<4 else 587} 237 L{x+49} 290',GRAY)
    s+=pulse('M377 112 L587 213 L565 307',GREEN,.05,.78,6)
    s+=text(495,160,'seek key 44',18,GREEN)
    return s+footer('Separators rule out unrelated ranges; the leaf locates the matching entry.','Schematic range tree, not a specific engine page layout. Index order must match the query shape.')

def bulkhead():
    s=heading(40,73,'ONE SHARED POOL',ORANGE)+heading(425,73,'SEPARATE RESOURCE BUDGETS',GREEN)
    for off in [0,385]:
        s+=rect(64+off,117,260,185,GRAY,BG)
        if off:s+=path(f'M{194+off} 117 V302',INK,3)
        for j in range(12):
            x=95+off+(j%4)*62;y=143+(j//4)*62
            c=ORANGE if not off or j%4<2 else GREEN
            s+=dot(x,y,14,c, tween('r',[(0,5),(.3,14),(.9,14),(1,5)]))
        s+=text(65+off,329,'slow A consumes all slots' if not off else 'slow A      healthy B',16,ORANGE if not off else GREEN)
    return s+footer('A bulkhead reserves capacity so one slow dependency cannot occupy every slot.','Isolation trades some utilization for containment. Shared databases and CPU can still couple the pools.')

EXTRA_SPECS=[('cache-expiry','Expiry jitter spreads the refresh wave',expiry,7),('backpressure','A buffer is a reservoir, not capacity',backpressure,7),('circuit-breaker','A circuit opens, then probes recovery',breaker,8),('replication-lag','Acknowledged here, not visible everywhere',replication,7),('transaction-outbox','Close the commit-to-publish gap',outbox,7),('deadline-budget',"Children spend the parent's remaining budget",deadline,6),('token-bucket','Store burst credit, refill over time',token_bucket,7),('connection-pool','Lease connections within a fixed budget',pool,8),('traffic-shift','Move admissions, drain existing work',traffic_shift,7),('io-waterfall','Independent work can share the wait',waterfall,6),('heap-sift','Repair the heap along one branch',heap_sift,7),('trie-prefix','One prefix opens several completions',trie,6),('backtracking','Choose, explore, undo, try the next branch',backtrack,10),('merge-intervals','Overlap extends the current interval',intervals,6),('index-seek','A separator eliminates a whole range',index_tree,5),('bulkhead','Contain the slow neighbor',bulkhead,6)]

SPECS=[
('map-lookup','Remember the complement',maps,8),('window-moves','A window that never moves backward',window,7),
('prefix-counts','Two boundaries, one prefix value',prefix,5),('binary-halving','Keep the first qualifying index',binary,7),
('bfs-frontier','A graph becomes distance layers',graph,6),('monotonic-stack','A warmer day empties the stack',stack,7),
('dp-choice','Candidates flow into a minimum',dp,6),('lru-order','Move the node, preserve its identity',lru,7),
('config-cohorts','Contain the configuration failure',config,8),('retry-tree','Retries multiply across layers',retries,5),
('rollout-capacity','Keep capacity above incoming demand',capacity,7),('version-projection','A late event meets a version guard',status,7),
('partition-skew','Route around a hot key',hotkeys,6),('worker-slots','Admission follows completion',workers,9),
('cache-coalescing','One load, six waiting callers',cache,6),('conditional-result','Duplicate delivery, one stored result',idem,7),
('direct-upload','Separate permission from bytes',upload,7),('browser-race','The older response arrives last',browser_race,7)] + EXTRA_SPECS

def document(title,body,description):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 420" width="760" height="420" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0 0 L7 3.5 L0 7" fill="{MUTED}"/></marker></defs><style>text{{font-family:ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif}}.still{{display:none}}@media(prefers-reduced-motion:reduce){{.moving{{display:none}}.still{{display:inline}}}}@media print{{.moving{{display:none}}.still{{display:inline}}}}</style><rect width="760" height="420" rx="10" fill="{BG}"/>{text(32,35,title.upper(),16,MUTED)}{body}</svg>'''

def build():
    global STILL,DURATION
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for key,title,draw,duration in SPECS:
        DURATION=duration;STILL=False;animated=draw();STILL=True;static=draw()
        # Full static explanation plus separately authored choreography, no rotating captions.
        import re
        labels=' '.join(re.findall(r'<text[^>]*>([^<]+)',static))
        desc=labels+' Motion timing is illustrative, not a production measurement. The loop restart is not a system event.'
        (OUT/(key+'.svg')).write_text(document(title,'<g class="moving">'+animated+'</g><g class="still">'+static+'</g>',desc).replace('><','>\n<')+'\n')
        (OUT/(key+'-still.svg')).write_text(document(title,static,desc).replace('><','>\n<')+'\n')
        manifest.append({'key':key,'title':title,'duration_seconds':duration,'motion':'continuous geometry and causal path traversal'})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    gallery='# Motion gallery\n\nPersistent diagrams with purposeful motion. Every animation has a readable static alternative. Timing is illustrative.\n\n[Learning paths](../../README.md) · [Draw the architecture](../../paths/interviews/architecture/whiteboard.md) · [Coding route](../../paths/interviews/coding/README.md)\n\n'
    gallery+=' | Concept | Motion | Static |\n|---|---|---|\n'
    for item in manifest:
        k=item['key']; title=item['title']
        gallery+=f'| {title} | [Play]({k}.svg) | [Still]({k}-still.svg) |\n'
    for item in manifest:
        k=item['key']; title=item['title']
        gallery+=f'\n## {title}\n\n![{title}]({k}.svg)\n\n[Open animation]({k}.svg) · [Static diagram]({k}-still.svg)\n'
    (OUT/'README.md').write_text(gallery)

    print(f'Built {len(SPECS)} motion studies and {len(SPECS)} readable static alternatives.')
if __name__=='__main__':build()
