"""Mechanism-specific SVGs. Native SVG motion; no slideshow layout or JS.

Run with --frames DIR to render editable SVG checkpoints for visual review.
Colors/line weights follow the original assets/diagrams illustrations.
"""
from pathlib import Path
from html import escape
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/learning'
BG='#faf9f7'; INK='#1f2b24'; GREEN='#2f6f4e'; ORANGE='#c2703d'; GRAY='#ded9d1'; MUTED='#6d6459'; PALE='#eef2ef'
STATE=None; N=4

def el(tag, attrs, changes=None, content=''):
    a=dict(attrs); anim=''
    for name,values in (changes or {}).items():
        assert len(values)==N, (name,values,N)
        a[name]=values[-1 if STATE is None else STATE]
        if STATE is None:
            seq=list(values)+[values[0]]
            anim+=f'<animate attributeName="{name}" values="'+ ';'.join(escape(str(v),quote=True) for v in seq)+'" keyTimes="'+';'.join(str(i/N) for i in range(N+1))+'" calcMode="discrete" dur="12s" repeatCount="indefinite"/>'
    return '<'+tag+' '+ ' '.join(f'{k}="{escape(str(v),quote=True)}"' for k,v in a.items())+'>'+anim+content+'</'+tag+'>'
def txt(x,y,s,size=15,color=INK,anchor='start',changes=None):
    return el('text',{'x':x,'y':y,'font-size':size,'fill':color,'text-anchor':anchor},changes,escape(str(s)))
def box(x,y,w,h,label='',color=GREEN,fill=PALE,changes=None):
    return el('rect',{'x':x,'y':y,'width':w,'height':h,'rx':5,'fill':fill,'stroke':color,'stroke-width':1.5},changes)+(txt(x+w/2,y+h/2+5,label,14,INK if color==GRAY else color,'middle') if label else '')
def line(x,y,xx,yy,color=MUTED,arrow=False,changes=None):
    return el('line',{'x1':x,'y1':y,'x2':xx,'y2':yy,'stroke':color,'stroke-width':1.5,**({'marker-end':'url(#arrow)'} if arrow else {})},changes)
def dot(x,y,r=5,color=GREEN,changes=None):
    return el('circle',{'cx':x,'cy':y,'r':r,'fill':color},changes)
def packet(path,color=GREEN,begin=0):
    # Hide traveling marker in static checkpoints; topology remains complete.
    if STATE is not None:return ''
    return f'<circle r="4" fill="{color}"><animateMotion path="{path}" dur="3s" begin="{begin}s" repeatCount="indefinite"/></circle>'
def label_states(x,y,labels,size=16,color=INK):
    return ''.join(txt(x,y,s,size,color,changes={'opacity':[int(j==i) for j in range(N)]}) for i,s in enumerate(labels))
def caption(labels):return line(32,352,728,352,GRAY)+label_states(32,383,labels,16)
def array(values,x=56,y=118,step=72,w=58,active=None):
    s=''
    for i,v in enumerate(values):
        s+=txt(x+i*step+w/2,y-12,i,12,MUTED,'middle')
        colors=[PALE if i in z else BG for z in active] if active else None
        s+=box(x+i*step,y,w,52,changes={'fill':colors} if colors else None,color=GRAY,fill=BG)
        s+=txt(x+i*step+w/2,y+33,v,22,INK,'middle')
    return s

def maps():
    s=array([2,7,11,15],x=55,active=[{0},{1},{1},{1}])
    s+=txt(55,78,'target = 9',17)+txt(410,93,'VALUE → EARLIER INDEX',12,MUTED)
    s+=box(415,114,275,115,fill=BG,color=GRAY)+txt(440,150,'2 → 0',22,GREEN)
    s+=line(290,178,455,215,GREEN,True)+label_states(55,224,['Read 2: need 7','Read 7: need 2','2 is already in the map','Return indices (0, 1)'],18)
    s+=el('path',{'d':'M55 185 v12 h130 v-12','fill':'none','stroke':ORANGE,'stroke-width':3},{'opacity':[0,0,1,1]})
    s+=txt(55,280,'Lookup first. Insert only if no pair was found.',16)
    s+=caption(['Map starts empty; insert 2 at index 0.','The next value finds its complement in earlier work.','Two different indices; never reuse the current item.','One pass + remembered values: expected O(n).'])
    return s

def window():
    s=array(list('abba'),x=160,step=100,w=72)
    s+=el('rect',{'x':154,'y':110,'width':84,'height':68,'rx':7,'fill':'none','stroke':GREEN,'stroke-width':3},{'x':[154,154,354,354],'width':[84,184,84,184]})
    s+=txt(160,225,'L',18,GREEN,changes={'x':[160,160,360,360]})+txt(210,250,'R',18,ORANGE,changes={'x':[210,310,410,510]})
    s+=label_states(60,302,['window: a   best: 1','window: ab   best: 2','window: b   best: 2','window: ba   best: 2'],20)
    s+=caption(['Start at the first a.','Extend right: no duplicate.','Second b: jump left past the first b.','Old a is outside the window. Left never moves backward.'])
    return s

def prefix():
    s=array([1,-1,1],x=48,active=[set(),{0},{0,1},{0,1,2}])
    s+=txt(48,79,'target = 1',17)+txt(370,84,'COUNT OF EARLIER PREFIXES',12,MUTED)
    for j,v in enumerate(['0','1']):
        s+=txt(385,139+j*64,v,20)
        s+=el('rect',{'x':425,'y':115+j*64,'height':35,'width':72,'fill':GREEN,'rx':4},{'width':([72,72,144,144] if j==0 else [0,72,72,144])})
    s+=label_states(590,139,['1','1','2','2'],20,GREEN)+label_states(590,203,['0','1','1','2'],20,GREEN)
    s+=label_states(48,235,['prefix = 0','prefix = 1','prefix = 0','prefix = 1'],20)
    s+=label_states(48,276,['matches = 0','matches = 1','matches = 1','matches = 3'],24,GREEN)
    s+=txt(370,287,'Bar length = number of earlier starts',15,MUTED)
    s+=caption(['Seed prefix 0 once: ranges may start at index 0.','Need prefix 0. One earlier start matches.','Need prefix -1. No match; store another prefix 0.','Need prefix 0 again. Two starts add two matches.'])
    return s

def binary():
    s=array([1,2,2,5,8,12],x=55,step=95,w=70)
    s+=txt(55,77,'First value ≥ 2     search interval [lo, hi)',17)
    s+=el('path',{'d':'M0 0 v12 H640 v-12','transform':'translate(50 184)','fill':'none','stroke':GREEN,'stroke-width':3},{'d':['M0 0 v12 H550 v-12','M0 0 v12 H265 v-12','M0 0 v12 H75 v-12','M95 0 v12 H95 v-12']})
    s+=el('path',{'d':'M185 203 l-8 12 h16 Z','fill':ORANGE},{'opacity':[0,0,0,1]})
    s+=label_states(55,255,['lo=0  hi=6  mid=3 → value 5','lo=0  hi=3  mid=1 → value 2','lo=0  hi=1  mid=0 → value 1','lo=1  hi=1 → answer index 1'],20)
    s+=txt(55,306,'Keep mid when it qualifies. The first match may be there.',16)
    return s+caption(['5 qualifies: set hi to 3.','2 qualifies: set hi to 1.','1 is too small: set lo to 1.','The search interval is empty; the insertion point remains.'])

def graph():
    nodes=[(110,100,'A'),(285,90,'B'),(285,240,'C'),(475,150,'D'),(645,235,'E')]
    s=''
    for a,b in [(0,1),(0,2),(1,3),(2,3),(3,4)]:
        x,y,_=nodes[a];xx,yy,_=nodes[b];s+=line(x,y,xx,yy,GRAY)
    visited=[{0},{0,1,2},{0,1,2,3},{0,1,2,3,4}]
    frontier=[{0},{1,2},{3},{4}]
    for i,(x,y,name) in enumerate(nodes):
        s+=el('circle',{'cx':x,'cy':y,'r':28,'stroke':GREEN,'stroke-width':2,'fill':BG},{'fill':[ORANGE if i in frontier[j] else (GREEN if i in v else BG) for j,v in enumerate(visited)]})
        s+=txt(x,y+6,name,20,anchor='middle',changes={'fill':[BG if i in v else INK for v in visited]})
    s+=txt(435,80,'orange: frontier   green: visited',13,MUTED)
    s+=label_states(45,316,['frontier: [A]    distance 0','frontier: [B, C]    distance 1','frontier: [D]    distance 2','frontier: [E]    distance 3'],18)
    return s+caption(['FIFO frontier starts at the source.','Visit all neighbors one edge away.','Both B and C reach D. Enqueue D only once.','Layers give shortest distance only for equal-cost edges.'])

def stack():
    s=array([73,74,71,75],x=50,step=90,w=65)
    s+=txt(475,76,'UNRESOLVED INDICES',12,MUTED)
    vals=[['0:73'],['1:74'],['1:74','2:71'],['3:75']]
    for k,label in enumerate(['0:73','1:74','2:71','3:75']):
        ys=[];ops=[]
        for v in vals:ys.append(290-v.index(label)*47 if label in v else 290);ops.append(int(label in v))
        s+=el('g',{}, {'opacity':ops,'transform':[f'translate(0 {y-290})' for y in ys]},box(500,252,135,40,label))
    s+=line(485,296,654,296,GREEN)+txt(52,242,'output wait distances',15,MUTED)
    s+=label_states(52,280,['[0, 0, 0, 0]','[1, 0, 0, 0]','[1, 0, 0, 0]','[1, 2, 1, 0]'],23)
    return s+caption(['73 waits for something warmer.','74 resolves 73. Pop once, then push index 1.','71 is colder, so both pending days remain.','75 resolves two pending days. Each index pops once.'])

def dp():
    s=txt(45,75,'coins = [1, 3, 4]    amount = 6',18)
    s+=txt(45,112,'GREEDY',12,ORANGE)+txt(425,112,'REMEMBER SUBPROBLEMS',12,GREEN)
    for i,v in enumerate([4,1,1]):s+=dot(80+i*83,170,26,ORANGE)+txt(80+i*83,178,v,23,BG,'middle')
    for i,v in enumerate([3,3]):s+=dot(475+i*90,170,26,GREEN)+txt(475+i*90,178,v,23,BG,'middle')
    s+=txt(48,224,'3 coins',19,ORANGE)+txt(447,224,'2 coins',19,GREEN)
    s+=txt(45,272,'dp[6] candidates:',16)
    s+=label_states(230,272,['1 + dp[5] = 3','1 + dp[3] = 2','1 + dp[2] = 3','min(3, 2, 3) = 2'],21,GREEN)
    s+=txt(45,315,'dp[0..5] = [0, 1, 2, 1, 1, 2]',17,MUTED)
    return s+caption(['Try the final coin 1.','Try the final coin 3: a better result.','Try the final coin 4; it does not improve the best.','Greedy misses a choice that the recurrence considers.'])

def lru():
    s=txt(45,80,'capacity = 2',18)+txt(105,125,'LEAST RECENT',12,MUTED)+txt(490,125,'MOST RECENT',12,GREEN)
    s+=line(235,190,505,190,GRAY,True)
    for name,xs,opacity,color in [('A',[100,100,485,100],[1,1,1,1],GREEN),('B',[485,485,100,100],[0,1,1,0],ORANGE),('C',[485]*4,[0,0,0,1],GREEN)]:
        s+=el('g',{}, {'transform':[f'translate({x-100} 0)' for x in xs],'opacity':opacity},box(100,160,145,60,name,color))
    s+=label_states(45,293,['put(A): [A]','put(B): [A, B]','get(A): [B, A]','put(C): evict B → [A, C]'],22)
    return s+caption(['First item occupies one entry.','New items join the most-recent end.','Reading A moves the same node; it does not add a slot.','Eviction removes the least-recent node, B.'])

def config():
    s=txt(40,75,'ALL AT ONCE',12,ORANGE)+txt(430,75,'ONE COHORT FIRST',12,GREEN)
    for off in [0,385]:
        s+=box(105+off,92,130,42,'config v2')
        for j in range(6):
            x=60+off+(j%3)*89;y=182+(j//3)*76
            s+=line(170+off,134,x+30,y,GRAY)
            colors=([PALE,ORANGE,ORANGE,ORANGE] if off==0 else ([PALE,ORANGE,ORANGE,PALE] if j==0 else [PALE]*4))
            s+=box(x,y,63,42,changes={'fill':colors},fill=PALE,color=GRAY)
            s+=txt(x+31,y+27,str(j+1),16,INK,'middle')
        if off:s+=label_states(420,327,['6 cohorts on v1','1 exposed / 5 on v1','Health gate: stop','Restore canary to v1'],17,GREEN)
        else:s+=label_states(40,327,['6 cohorts on v1','6 exposed','All routes impaired','Broad recovery needed'],17,ORANGE)
    return s+caption(['Every cohort starts with a working configuration.','Same defect, different exposure boundary.','The canary gate prevents further distribution.','Rollback limits this failure; shared dependencies still matter.'])

def retries():
    s=txt(40,70,'THREE RETRY OWNERS',12,ORANGE)+txt(430,70,'ONE RETRY OWNER',12,GREEN)
    for off in [0,385]:
        for j,name in enumerate(['API','Service','Data client']):
            s+=box(95+off,92+j*73,160,36,name,ORANGE if off==0 else GREEN)
            count=(3**(j+1) if off==0 else (1 if j<2 else 3))
            for k in range(count):
                x1=106+off+k*135/max(1,count-1); x2=85+off+k*155/max(1,count-1)
                s+=line(x1,128+j*73,x2,160+j*73,ORANGE if off==0 else GREEN)
                if k<9:s+=packet(f'M{x1} {128+j*73} L{x2} {160+j*73}',ORANGE if off==0 else GREEN,k*.11)
        s+=txt(170+off,337,'up to 27 leaf calls' if off==0 else 'up to 3 leaf calls',19,ORANGE if off==0 else GREEN,'middle')
    return s+caption(['Each layer permits three total attempts in the left design.','A retry creates more downstream retries.','On the right, only the data-client layer repeats the call.','Bounds are per logical request; also bound aggregate retry load.'])

def capacity():
    s=txt(42,76,'STOP TWO FIRST',12,ORANGE)+txt(425,76,'START REPLACEMENTS FIRST',12,GREEN)
    for off in [0,385]:
        for i in range(12):
            x=45+off+(i%4)*76;y=100+(i//4)*55
            ops=([int(i<10),int(i<8),int(i<8),int(i<10)] if off==0 else [int(i<10),1,1,int(i<10)])
            s+=el('g',{}, {'opacity':ops},box(x,y,61,38,str(i+1),GREEN))
        s+=txt(45+off,285,'incoming: 850 req/s',17)
        widths=([240,192,192,240] if off==0 else [240,288,288,240])
        s+=el('rect',{'x':42+off,'y':310,'height':15,'width':280,'fill':GREEN},{'width':widths,'fill':[GREEN,ORANGE if off==0 else GREEN,ORANGE if off==0 else GREEN,GREEN]})
        s+=line(246+off,302,246+off,334,INK)
    return s+caption(['Each toy task sustains 100 req/s. Ten provide 1,000 req/s.','Eight tasks provide 800 req/s: below the 850 req/s demand.','Surge keeps capacity, only if downstream budgets also fit.','A 60-second deficit leaves 3,000 requests to drain.'])

def status():
    s=box(45,100,170,54,'job result: done')+box(295,100,180,54,'completion log')+box(545,100,165,54,'status view')
    s+=line(215,127,295,127,GREEN,True)+line(475,127,545,127,GREEN,True)
    s+=packet('M220 127 H290',GREEN)
    s+=txt(45,205,'EVENTS ARRIVE',12,MUTED)+txt(475,205,'STORED STATE',12,MUTED)
    s+=label_states(45,250,['running / v2','completed / v3','running / v2','completed / v3'],22)
    s+=label_states(475,250,['running / v2','completed / v3','completed / v3','completed / v3'],22,GREEN)
    s+=line(290,244,447,244,GRAY,True)
    s+=label_states(45,318,['Apply newer event','Apply newer event','Reject stale event','Duplicate: no change'],18,ORANGE)
    return s+caption(['Status is a projection; result storage is a separate boundary.','A newer version advances the projection.','A delayed event cannot overwrite a newer version.','Same version with different payload is a conflict, not a no-op.'])

def hotkeys():
    s=txt(40,75,'ONE HOT KEY',12,ORANGE)+txt(425,75,'FOUR LOGICAL BUCKETS',12,GREEN)
    for off in [0,385]:
        for i in range(4):
            x=50+off+i*76
            s+=box(x,107,52,185,fill=BG,color=GRAY)
            vals=([0,50,100,150] if off==0 and i==0 else ([0]*4 if off==0 else [0,12.5,25,37.5]))
            s+=el('rect',{'x':x+8,'y':282,'width':36,'height':0,'fill':ORANGE if off==0 else GREEN},{'height':vals,'y':[282-v for v in vals]})
            s+=line(x,222,x+52,222,ORANGE)
            s+=txt(x+26,317,chr(65+i),15,MUTED,'middle')
        s+=txt(45+off,96,'250 / 0 / 0 / 0' if off==0 else '62.5 / 62.5 / 62.5 / 62.5',14)
    return s+caption(['Bars grow to arrival rates. Orange line: capacity 100 units/s.','Averages hide one overloaded partition and three idle ones.','Independent writes can spread; strictly ordered work may not.','Logical DynamoDB keys do not guarantee physical placement.'])

def workers():
    s=txt(45,80,'WAITING',12,MUTED)+txt(290,80,'THREE ACTIVE SLOTS',12,GREEN)+txt(580,80,'COMPLETED',12,MUTED)
    for j in range(3):s+=box(300,105+j*68,145,48,'slot '+str(j+1),fill=BG,color=GRAY)
    for j in range(9):
        batch=j//3;row=j%3
        xs=[];ys=[]
        for step in range(4):
            xs.append(75 if step<batch else (354 if step==batch else 605))
            ys.append(122+j*22 if step<batch else (129+row*68 if step==batch else 121+j*22))
        s+=dot(xs[-1],ys[-1],9,GREEN,{'cx':xs,'cy':ys})
    s+=line(139,214,279,214,GRAY,True)+line(455,214,558,214,GRAY,True)
    return s+caption(['Jobs 1–3 occupy the three slots; six wait.','Only completion releases slots for jobs 4–6.','Jobs 7–9 start. Active work never exceeds three.','All nine finish. Concurrency is distinct from requests per second.'])

def cache():
    s=txt(40,75,'SIX INDEPENDENT MISSES',12,ORANGE)+txt(425,75,'ONE SHARED IN-FLIGHT LOAD',12,GREEN)
    for off in [0,385]:
        for j in range(6):
            x=55+off+j*51;s+=dot(x,110,10,ORANGE if off==0 else GREEN)
            xx=x if off==0 else 180+off
            s+=line(x,123,xx,207,GRAY)
            if off==0:s+=packet(f'M{x} 125 V282',ORANGE,j*.2)
        s+=box(40+off,212,300,40,'cache miss' if off==0 else 'shared promise',fill=BG,color=GRAY)
        for j in range(6 if off==0 else 1):
            x=55+off+j*51 if off==0 else 180+off
            s+=line(x,252,x,285,ORANGE if off==0 else GREEN,True)
            if off:s+=packet(f'M{x} 125 V282',GREEN)
        s+=box(40+off,285,300,44,'DB: 6 reads' if off==0 else 'DB: 1 read')
    return s+caption(['All callers ask for the same missing key.','Independent loads duplicate work at the database.','One loader shares its result with local waiters.','A process-local promise does not coordinate other processes.'])

def idem():
    s=box(40,95,145,45,'delivery A')+box(40,210,145,45,'retry of A')+box(320,135,185,70,'conditional write')+box(580,135,130,70,'one result')
    s+=line(185,118,320,153,GREEN,True)+line(185,232,320,188,ORANGE,True)+line(505,170,580,170,GREEN,True)
    s+=packet('M190 118 L315 153',GREEN)+packet('M190 232 L315 188',ORANGE,1)
    s+=label_states(45,309,['First attempt: result key absent','Atomic insert commits the result','Acknowledgement lost; same job redelivered','Same ID and payload: return prior success'],18)
    return s+caption(['Identity belongs to the logical job, not each delivery.','Only the first conditional insert can create this result item.','Two deliveries can race; the store decides the winner.','External email or payment needs its own idempotency protocol.'])

def upload():
    s=box(50,115,165,55,'browser')+box(480,72,195,55,'API: authorize')+box(480,247,195,65,'S3: object bytes')
    s+=el('path',{'d':'M215 128 L480 99','stroke':GREEN,'stroke-width':1.5,'fill':'none','marker-end':'url(#arrow)'})
    s+=el('path',{'d':'M480 120 L215 153','stroke':GREEN,'stroke-width':1.5,'fill':'none','marker-end':'url(#arrow)'})
    s+=el('path',{'d':'M132 170 V278 H480','stroke':ORANGE,'stroke-width':5,'fill':'none','marker-end':'url(#arrow)'})
    s+=txt(270,89,'small metadata',14,GREEN)+txt(259,163,'scoped upload capability',14,GREEN)+txt(170,263,'large bytes bypass API',16,ORANGE)
    s+=packet('M220 128 L470 100',GREEN)+packet('M132 180 V278 H470',ORANGE)
    return s+caption(['The API checks user permission and chooses an object key.','The browser receives a short-lived upload capability.','Bytes go directly to S3; the API is not a file proxy.','Finalize only after checking the uploaded object and ownership.'])

def browser_race():
    s=txt(45,80,'REQUEST',12,MUTED)+txt(300,80,'TIME →',12,MUTED)
    s+=txt(40,145,'cat',20,ORANGE)+txt(40,225,'car',20,GREEN)
    s+=line(130,140,660,140,ORANGE,True)+line(270,220,455,220,GREEN,True)
    s+=txt(130,120,'start 1',13,MUTED)+txt(270,200,'start 2',13,MUTED)
    s+=txt(480,223,'response 2 arrives first',15,GREEN)
    s+=txt(495,122,'response 1 arrives late',15,ORANGE)
    s+=el('line',{'x1':130,'x2':130,'y1':95,'y2':246,'stroke':INK,'stroke-width':2},{'x1':[130,270,455,660],'x2':[130,270,455,660]})
    s+=box(40,280,675,48,fill=BG,color=GRAY)
    s+=label_states(62,311,['UI: loading cat · generation 1','UI: loading car · generation 2','UI: car · accepted generation 2','UI: car · reject obsolete generation 1'],18)
    return s+caption(['Each search gets an increasing generation.','New intent supersedes the old request.','Commit the result only if its generation is current.','Abort saves work when supported; the generation guard is essential.'])

SPECS=[('map-lookup','Remember the complement',maps),('window-moves','A window that never moves backward',window),('prefix-counts','One prefix can represent several starts',prefix),('binary-halving','Keep the first qualifying index',binary),('bfs-frontier','A graph becomes distance layers',graph),('monotonic-stack','Resolve only what the new value proves',stack),('dp-choice','Greedy versus a recurrence',dp),('lru-order','A read changes eviction order',lru),('config-cohorts','Same defect, different blast radius',config),('retry-tree','Retry ownership changes the call tree',retries),('rollout-capacity','Correct code still needs deployment headroom',capacity),('version-projection','A late event must not rewrite the present',status),('partition-skew','Unused capacity beside a hot partition',hotkeys),('worker-slots','A completion releases one slot',workers),('cache-coalescing','One miss, one local loader',cache),('conditional-result','Duplicate delivery, one stored result',idem),('direct-upload','Separate permission from the byte stream',upload),('browser-race','The older response arrives last',browser_race)]

def document(title,body):
 return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 420" width="760" height="420" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(title)}. Logical teaching states; not measured production timing. See adjacent lesson for the invariant and static alternative.</desc><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7" fill="{MUTED}"/></marker></defs><style>text{{font-family:ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif}}.still{{display:none}}@media(prefers-reduced-motion:reduce){{.moving{{display:none}}.still{{display:inline}}}}@media print{{.moving{{display:none}}.still{{display:inline}}}}</style><rect width="760" height="420" rx="10" fill="{BG}"/>{txt(32,35,title.upper(),16,MUTED)}{body}</svg>'''

def build():
 global STATE
 OUT.mkdir(exist_ok=True,parents=True)
 frames=Path(sys.argv[sys.argv.index('--frames')+1]) if '--frames' in sys.argv else None
 if frames:frames.mkdir(exist_ok=True,parents=True)
 for key,title,draw in SPECS:
    STATE=None;moving=draw()
    STATE=N-1;still=draw()
    (OUT/(key+'.svg')).write_text(document(title,'<g class="moving">'+moving+'</g><g class="still">'+still+'</g>'))
    (OUT/(key+'-still.svg')).write_text(document(title,still))
    if frames:
      for i in range(N):
        STATE=i;(frames/f'{key}-{i}.svg').write_text(document(title,draw()))
 STATE=None
 (OUT/'manifest.json').write_text(json.dumps([{'key':k,'title':t,'states':N} for k,t,_ in SPECS],indent=2)+'\n')
 print(f'Built {len(SPECS)} mechanism animations and {len(SPECS)} static diagrams.')
if __name__=='__main__':build()
