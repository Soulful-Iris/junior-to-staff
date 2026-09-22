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
        s+=path(f'M130 {y} H304 M430 {y} H615',GRAY,1.5,True)+box(304,y-22,126,44,'slot '+str(r+1),GRAY,BG)
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

SPECS=[
('map-lookup','Remember the complement',maps,8),('window-moves','A window that never moves backward',window,7),
('prefix-counts','Two boundaries, one prefix value',prefix,5),('binary-halving','Keep the first qualifying index',binary,7),
('bfs-frontier','A graph becomes distance layers',graph,6),('monotonic-stack','A warmer day empties the stack',stack,7),
('dp-choice','Candidates flow into a minimum',dp,6),('lru-order','Move the node, preserve its identity',lru,7),
('config-cohorts','Contain the configuration failure',config,8),('retry-tree','Retries multiply across layers',retries,5),
('rollout-capacity','Keep capacity above incoming demand',capacity,7),('version-projection','A late event meets a version guard',status,7),
('partition-skew','Route around a hot key',hotkeys,6),('worker-slots','Admission follows completion',workers,9),
('cache-coalescing','One load, six waiting callers',cache,6),('conditional-result','Duplicate delivery, one stored result',idem,7),
('direct-upload','Separate permission from bytes',upload,7),('browser-race','The older response arrives last',browser_race,7)]

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
        (OUT/(key+'.svg')).write_text(document(title,'<g class="moving">'+animated+'</g><g class="still">'+static+'</g>',desc)+'\n')
        (OUT/(key+'-still.svg')).write_text(document(title,static,desc)+'\n')
        manifest.append({'key':key,'title':title,'duration_seconds':duration,'motion':'continuous geometry and causal path traversal'})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Built {len(SPECS)} motion studies and {len(SPECS)} readable static alternatives.')
if __name__=='__main__':build()
