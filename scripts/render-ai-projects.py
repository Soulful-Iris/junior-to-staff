#!/usr/bin/env python3
"""Authored explanatory SVGs. Motion traces work; every diagram has a readable still."""
from html import escape
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'ai-projects'
OUT.mkdir(parents=True, exist_ok=True)
INK, GREEN, ORANGE, MUTED = '#203e34', '#297456', '#b6653f', '#65776d'


def label(x, y, value, size=18, color=INK, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(value)}</text>'


def box(x,y,w,h,title,role='',bad=False):
    color=ORANGE if bad else GREEN
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{"#fff1e8" if bad else "#eef6ee"}" stroke="{color}" stroke-width="1.6"/>'
    lines=textwrap.wrap(title,width=max(12,int(w/10)))
    for i,line in enumerate(lines):s+=label(x+w/2,y+29+i*22,line,17,anchor='middle',weight=600)
    if role:s+=label(x+w/2,y+h-17,role,14,MUTED,'middle')
    return s


def arrow(x,y,xx,yy,bad=False):
    color=ORANGE if bad else GREEN
    return f'<path d="M{x} {y} L{xx} {yy}" fill="none" stroke="{color}" stroke-width="2.5" marker-end="url(#{"bad" if bad else "good"})"/>'


def svg(name,title,subtitle,body,animate=False):
    contents=f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 960 640" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc><defs>'
    for name_,color in [('good',GREEN),('bad',ORANGE)]:
        contents+=f'<marker id="{name_}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{color}"/></marker>'
    contents+='</defs><style>text{font-family:system-ui,-apple-system,Segoe UI,sans-serif} .pulse{offset-rotate:0deg} @media(prefers-reduced-motion:reduce){.moving{display:none}}</style><rect x="1" y="1" width="958" height="638" rx="22" fill="#fcfcf8" stroke="#d5dfd2"/>'
    contents+=label(38,46,'AI SYSTEMS / BUILD • OBSERVE • EXPLAIN',13,MUTED,weight=600)+label(38,87,title,28,weight=650)
    for i,line in enumerate(textwrap.wrap(subtitle,100)):contents+=label(38,120+i*20,line,15,MUTED)
    contents+=body+'</svg>'
    (OUT/f'{name}.svg').write_text(contents)
    if animate:
        import re
        still=re.sub(r'<g class="moving">.*?</g>','',contents,flags=re.S)
        (OUT/f'{name}-still.svg').write_text(still)


SCENES={
 'assistant':{
  'title':'Evidence desk',
  'services':[('AWS CLI','trusted operator'),('AWS Lambda','request handler'),('Amazon Bedrock','citation selection'),('Amazon DynamoDB','current catalog + ACL'),('Amazon S3','source object storage'),('Lambda validation','final authorization check')],
  'edges':[(0,1),(1,2),(1,3),(3,4),(2,5),(3,5)],
  'before':['Retrieve all documents','Model sees payroll','A filter hides final words'],
  'after':['Read current permissions','Retrieve authorized text','Recheck catalog revision'],
  'rows':[('Question','Refunds within how many days?'),('Status','ANSWERED'),('Citation','refund-policy'),('Source excerpt','Refunds are available within 30 days.'),('After revocation','NO_EVIDENCE • no excerpt')],
  'states':['INGESTED','AUTHORIZED','SELECTED','RECHECKED','DISPLAYED'],
  'fail':'Revision changes during inference → SOURCE_CHANGED',
  'steps':['query + verified scope','authorized candidates','model chooses citation IDs','revision check + excerpts'],
 },
 'agent':{
  'title':'Approval desk',
  'services':[('AWS CLI','operator + approver'),('AWS Lambda','proposal handler'),('Amazon Bedrock','action proposal'),('Amazon DynamoDB','order + pending proposal'),('Lambda approval','digest + balance checks'),('Amazon DynamoDB','atomic sandbox receipt')],
  'edges':[(0,1),(1,2),(2,3),(0,4),(3,4),(4,5)],
  'before':['Model requests a refund','Execute immediately','Retry changes balance twice'],
  'after':['Store a bounded proposal','Approve its exact digest','Commit balance + receipt'],
  'rows':[('Order','order-17 • paid USD 50.00'),('Proposed action','refund USD 12.50'),('Status','PENDING_APPROVAL'),('After approval','COMMITTED • one receipt'),('Retry approval','Same receipt • total refunded USD 12.50')],
  'states':['PROPOSED','VALIDATED','PENDING','APPROVED','COMMITTED'],
  'fail':'Expired / changed balance / wrong digest → reject',
  'steps':['customer message','untrusted model proposal','human reviews exact amount','conditional sandbox commit'],
 },
 'extraction':{
  'title':'Invoice review desk',
  'services':[('Amazon SQS','invoice job queue'),('AWS Lambda','extraction worker'),('Amazon Bedrock','field extraction'),('Amazon DynamoDB','deduplication + result'),('Amazon S3','result artifact storage'),('Amazon SQS DLQ','failed-message inbox')],
  'edges':[(0,1),(1,2),(1,4),(4,3),(0,5)],
  'before':['Accept any model JSON','Retry the entire batch','Missing total becomes zero'],
  'after':['Verify currency + evidence','Retry only failed messages','Route ambiguity to review'],
  'rows':[('Source','ACME invoice 17. TOTAL USD 12.50'),('Record','invoice-17'),('Validated result','USD • 1250 cents'),('Status','ACCEPTED • artifact saved'),('Unreadable invoice','REVIEW_REQUIRED • data = null')],
  'states':['QUEUED','EXTRACTED','VALIDATED','STORED','ACKED'],
  'fail':'Model unavailable → retry; ambiguous total → review',
  'steps':['immutable record ID + text','one model extraction','schema + source evidence','conditional result publication'],
 },
 'evaluation':{
  'title':'Release evidence desk',
  'services':[('AWS CLI','labeled test cases'),('AWS Lambda','evaluation runner'),('Amazon Bedrock','candidate classification'),('Amazon S3','report artifact storage'),('Amazon DynamoDB','immutable run registry'),('Amazon DynamoDB','active release pointer')],
  'edges':[(0,1),(1,2),(1,3),(3,4),(4,5)],
  'before':['Average quality looks high','Promote a mutable model alias','Rollback cannot find evidence'],
  'after':['Check severe failures + coverage','Register model + dataset + report','Swap a versioned release pointer'],
  'rows':[('Candidate','fixture-v1 • deterministic test double'),('Suite','6 cases • 3 categories'),('Result','6 / 6 pass • 0 severe misses'),('Release','release-2 • revision 2'),('Rollback','release-1 • revision 3')],
  'states':['LABELED','EXECUTED','SCORED','REGISTERED','PROMOTED'],
  'fail':'Any severe miss / missing coverage → release blocked',
  'steps':['independent labels','actual candidate outputs','per-case comparisons','eligible report + conditional release'],
 }
}

for slug,d in SCENES.items():
    # A product-like result panel showing only behavior implemented by the CLI.
    s='<rect x="34" y="160" width="892" height="430" rx="18" fill="#173d31"/>'
    s+=label(60,194,'EXPECTED CONSOLE RESULT / NOT A SEPARATE WEB UI',12,'#a8cbbb',weight=600)
    for i,(name,value) in enumerate(d['rows']):
        y=231+i*67
        s+=label(60,y,name.upper(),12,'#a8cbbb',weight=600)+label(60,y+26,value,21,'#f3f6ee')
    svg(slug+'-result',d['title']+': the finished result','Read this panel before running the project. The sessions print the same fields as JSON.',s)
    # Box topology: stable service vocabulary with architectural role beneath.
    slots=[(42,182),(352,182),(662,182),(42,389),(352,389),(662,389)]
    s=''
    for a,b in d['edges']:
        x,y=slots[a];xx,yy=slots[b]
        if y==yy and abs(xx-x)>310:
            s+=f'<path d="M{x+125} {y+109} V{y+140} H{xx+125} V{yy+110}" fill="none" stroke="{GREEN}" stroke-width="2.5" marker-end="url(#good)"/>'
        elif y==yy:s+=arrow(x+256,y+49,xx-10,yy+49) if x<xx else arrow(x-4,y+49,xx+266,yy+49)
        else:s+=arrow(x+125,y+103,xx+125,yy-12)
    for (x,y),(service,role) in zip(slots,d['services']):s+=box(x,y,252,102,service,role)
    s+=label(40,558,'Lambda-labeled stages share the supplied handler; repeated DynamoDB boxes share one table.',15,MUTED)
    s+=label(40,585,'Arrows show application-mediated data flow; storage services do not call one another.',15,MUTED)
    svg(slug+'-aws',d['title']+': AWS architecture','Name the role before the service. Keep model output outside the authority that commits state.',s)
    # Explicit contrast with an observable consequence on each side.
    s=label(50,190,'FAILURE BEFORE THE BOUNDARY',14,ORANGE,weight=600)+label(515,190,'BEHAVIOR AFTER THE BOUNDARY',14,GREEN,weight=600)
    for col,labels in enumerate([d['before'],d['after']]):
        x=45+col*467
        for i,value in enumerate(labels):
            y=215+i*115;s+=box(x,y,397,84,value,bad=col==0)
            if i<2:s+=arrow(x+195,y+88,x+195,y+106,bad=col==0)
    svg(slug+'-before',d['title']+': before and after','Predict the visible failure on the left. Then point to the precise new authority on the right.',s)
    # Lifecycle has branches and retry/rejection behavior, never "exactly once" animation magic.
    s=''
    points=[(50,190),(360,190),(670,190),(515,371),(205,371)]
    for i,(x,y) in enumerate(points):
        s+=box(x,y,235,86,d['states'][i],f'checkpoint {i+1}')
        if i<4:
            xx,yy=points[i+1]
            s+=arrow(x+240,y+43,xx-10,yy+43) if y==yy and xx>x else arrow(x-5,y+43,xx+243,yy+43) if y==yy else arrow(x+117,y+94,xx+117,yy-12)
    s+=box(70,517,820,75,d['fail'],bad=True)
    s+=arrow(790,285,790,505,bad=True)
    svg(slug+'-state',d['title']+': lifecycle','A success path needs named failure exits. Stored states survive a restarted client or worker.',s)
    # Continuous request tracing. No hiding labels or long slide transitions.
    s=''
    points=[(50,205),(515,205),(515,405),(50,405)]
    for i,(x,y) in enumerate(points):s+=box(x,y,395,92,f'{i+1:02d}  '+d['steps'][i])
    paths=['M450 250 H505','M712 305 V395','M505 450 H450']
    for i,path in enumerate(paths):
        s+=f'<path id="track{i}" d="{path}" stroke="{GREEN}" stroke-width="3" fill="none" marker-end="url(#good)"/>'
        s+=f'<g class="moving"><circle r="7" fill="{ORANGE}"><animateMotion dur="2.4s" begin="{-i*.8}s" repeatCount="indefinite" path="{path}"/></circle></g>'
    s+=label(45,558,'Moving dots show a request crossing a boundary; labels remain visible throughout the loop.',15,MUTED)
    svg(slug+'-flow',d['title']+': follow the request','Explain what is trusted at each hand-off. Motion is illustrative, not a measured service latency.',s,True)
    # Different mechanism view for each project.
    if slug=='assistant':
        s=box(45,185,250,105,'Catalog revision 4','alice may read policy')+box(660,185,250,105,'Catalog revision 5','access revoked',True)
        s+=arrow(304,238,651,238)+label(480,218,'revocation commits',17,ORANGE,'middle')
        s+=box(225,370,510,100,'Response checks revision 4 != 5','SOURCE_CHANGED; no excerpts',True)
        s+=arrow(787,300,630,360,True)+arrow(165,300,320,360)
        s+=label(480,550,'The final catalog read defines this response’s authorization decision.',19,anchor='middle')
    elif slug=='agent':
        s=box(50,185,350,105,'Before approval','paid 2000 / refunded 0')+box(560,185,350,105,'Proposal r1','refund 1250 / digest d1')
        s+=arrow(225,300,390,365)+arrow(735,300,570,365)
        s+=box(235,374,490,100,'One conditional order write','refunded 1250 + receipt d1')
        s+=label(480,540,'Retry d1 → return saved receipt. Changed request → conflict.',19,anchor='middle')
        s+=label(480,575,'An external payment requires its own idempotency and reconciliation.',16,MUTED,'middle')
    elif slug=='extraction':
        s=box(340,180,280,86,'Record invoice-17','hash = h1')
        s+=arrow(360,277,230,363)+arrow(599,277,740,363,True)
        s+=box(50,375,355,104,'Same ID / same hash','reuse saved ACCEPTED result')+box(555,375,355,104,'Same ID / changed hash','CONFLICT; do not overwrite',True)
        s+=label(480,553,'Retries can repeat inference before the commit, but not publish two results.',18,anchor='middle')
    else:
        s=box(48,190,263,106,'Quality','all 6 fixtures pass')+box(349,190,263,106,'Coverage','3 labels + severe cases')+box(650,190,263,106,'Authority','expected revision matches')
        for x in (180,480,780):s+=arrow(x,307,480,389)
        s+=box(310,402,340,88,'Promote eligible report','active v2 / previous v1')
        s+=label(480,554,'A tiny fixture suite proves gate behavior, not production readiness.',19,ORANGE,'middle')
    svg(slug+'-mechanism',d['title']+': the guarantee','Read the values. A useful diagram explains exactly which state change prevents the failure.',s)

print('Rendered 24 teaching diagrams and 4 motion-off stills')
