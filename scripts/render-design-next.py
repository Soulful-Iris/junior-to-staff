#!/usr/bin/env python3.12
"""Authored, accessible diagrams for the next system-design practice set.

Each scene's boxes label both the AWS product and its generic architectural job.
The diagrams are intentionally usable as still frames, with an explicit failure,
authority, and example state rather than a repeated slide animation.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'design-next'
OUT.mkdir(parents=True, exist_ok=True)
INK, MUTED, GOOD, BAD = '#243c34', '#596b63', '#267259', '#af563e'

# title; broken path; corrected path; service/role boxes; example state transitions
SCENES = {
 'collaborative-editor': ('One document, two writers',
  ['Ana edits v4', 'Ben edits v4', 'Last writer wins'], ['Stable op ID', 'Version authority', 'Rebase / replay'],
  [('API Gateway WebSocket','live connection'),('Amazon ECS','document sequencer'),('Amazon DynamoDB','operation log'),('Amazon S3','document snapshots'),('Amazon CloudWatch','replay telemetry')],
  [('Ana starts','base v4'),('Ben starts','base v4'),('Ana commits','v5; op a17'),('Ben rebases','v6; no loss')]),
 'webhook-delivery': ('One event, multiple attempts',
  ['Order commits', 'HTTP caller times out', 'Event forgotten'], ['Outbox row', 'Queued delivery', 'Same ID on retry'],
  [('Amazon RDS / Aurora','transaction + outbox'),('Amazon EventBridge','event router'),('Amazon SQS','delivery queue'),('Amazon ECS','delivery worker'),('Amazon SQS DLQ','failed delivery inbox')],
  [('Order commit','event e21'),('First POST','receiver commits'),('Reply lost','status unknown'),('Retry e21','same logical event')]),
 'tenant-isolation': ('One missing tenant predicate',
  ['Document ID', 'Global query', 'Other tenant data'], ['Verified tenant', 'Scoped key + policy', 'Allowed content only'],
  [('Amazon Cognito','user identity'),('Amazon API Gateway','request entry'),('Amazon DynamoDB','tenant-scoped records'),('Amazon S3','private object bytes'),('Amazon SQS','tenant-aware jobs')],
  [('Identity','tenant A'),('Request','doc owned by B'),('Policy gate','deny before title'),('Async job','verify tenant again')]),
 'audit-trail': ('Evidence starts with the transaction',
  ['Permission changes', 'Process crashes', 'Log never written'], ['Atomic audit intent', 'Retained archive', 'Queryable projection'],
  [('Amazon RDS / Aurora','permission + outbox'),('Amazon SQS','audit transport'),('AWS Lambda','archive writer'),('Amazon S3 Object Lock','retained evidence'),('Amazon Athena','investigation query')],
  [('Commit','seq 101'),('Archive','seq 101'),('Next commit','seq 103'),('Gap detector','find missing 102')]),
 'feature-rollout': ('A feature flag cannot reverse data',
  ['Activate all', 'Bad writes persist', 'Toggle too late'], ['Stable cohorts', 'Metric guardrail', 'Schema compatible'],
  [('AWS AppConfig','configuration rollout'),('Amazon ECS','application runtime'),('Amazon RDS','data boundary'),('Amazon CloudWatch','metrics + alarms'),('AWS AppConfig','config rollback')],
  [('5% cohort','stable assignment'),('50% cohort','watch errors'),('100% + 1d','batch discovers bug'),('Rollback','flag + data repair')]),
 'overload-shedding': ('Queues cannot create database capacity',
  ['40k arrivals/s', '20k served/s', '+20k queued/s'], ['Early admission', 'Priority budgets', 'Bounded deadlines'],
  [('Amazon API Gateway','edge admission'),('Amazon ECS','priority compute'),('Amazon RDS','durable database'),('Amazon ElastiCache','cache'),('Amazon CloudWatch','load telemetry')],
  [('t = 0s','0 backlog'),('t = 2s','40k queued'),('t = 5s','100k queued'),('After shedding','queue drains')]),
 'event-ingestion': ('One silent unit error poisons every total',
  ['Old temp = 32', 'New temp = 32F', 'One bad average'], ['Version decoder', 'Canonical units', 'Replayable raw log'],
  [('Amazon Kinesis','event stream'),('AWS Lambda','schema transformer'),('Amazon DynamoDB','current view'),('Amazon S3','raw event archive'),('Amazon SQS','invalid-record inbox')],
  [('v1 reading','32, legacy unit'),('v2 reading','32 Fahrenheit'),('Normalize','tag canonical C'),('Project','comparable totals')]),
 'knowledge-assistant': ('Relevance does not authorize a passage',
  ['Cached embedding', 'Access revoked', 'Snippet exposed'], ['Search candidates', 'Live ACL gate', 'Cited answer only'],
  [('Amazon S3','source documents'),('Bedrock Knowledge Bases','retrieval index'),('Amazon DynamoDB','authorization catalog'),('Amazon Bedrock','model inference'),('Amazon CloudWatch','quality telemetry')],
  [('Index','stale passage'),('Policy','access revoked'),('Gate','passage removed'),('Model','safe context only')]),
 'erasure-workflow': ('Deleting one row leaves nine copies',
  ['Primary deleted', 'Index still serves', 'False completed'], ['Immediate tombstone', 'Delete all copies', 'Verify exceptions'],
  [('AWS Step Functions','workflow coordinator'),('Amazon DynamoDB','tombstone + ledger'),('Amazon SQS','deletion queue'),('Amazon S3','object copies'),('Amazon CloudWatch','completion alarms')],
  [('Request','ledger open'),('Primary','deleted'),('Search + backup','outstanding'),('Completion','all evidence or hold')]),
}

# Directed flows, specified per problem. A monitoring box is never drawn as a
# predecessor of a durable data store just to make an attractive zig-zag.
EDGES = {
 'collaborative-editor': [(0,1),(1,2),(1,3),(1,4)],
 'webhook-delivery': [(0,1),(1,2),(2,3),(3,4)],
 'tenant-isolation': [(0,1),(1,2),(1,3),(1,4)],
 'audit-trail': [(0,1),(1,2),(2,3),(3,4)],
 'feature-rollout': [(0,1),(1,2),(1,3),(3,4)],
 'overload-shedding': [(0,1),(1,2),(1,3),(1,4)],
 'event-ingestion': [(0,1),(1,2),(0,3),(1,4)],
 'knowledge-assistant': [(0,1),(1,2),(2,3),(3,4)],
 'erasure-workflow': [(0,1),(0,2),(2,3),(0,4)],
}


def txt(x, y, value, size=17, color=INK, weight='normal', anchor='start'):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


def line(x, y, x2, y2, color=GOOD):
    return f'<path d="M{x} {y} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="2.5" marker-end="url(#{"good" if color == GOOD else "bad"})"/>'


def connection(origin, destination, width=268, height=94):
    x,y=origin; x2,y2=destination
    if y==y2:
        if x < x2: return line(x+width+4,y+height/2,x2-10,y2+height/2)
        return line(x-4,y+height/2,x2+width+10,y2+height/2)
    if y<y2: return line(x+width/2,y+height+7,x2+width/2,y2-12)
    return line(x+width/2,y-7,x2+width/2,y2+height+12)


def box(x, y, w, h, heading, sub='', color=GOOD):
    body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{"#edf7f2" if color == GOOD else "#fff0ea"}" stroke="{color}" stroke-width="2"/>'
    size = 15 if len(heading) < 26 else 13
    body += txt(x + w/2, y + (35 if sub else h/2+6), heading, size, INK, '600', 'middle')
    if sub:
        body += txt(x + w/2, y + 64, sub, 14, MUTED, anchor='middle')
    return body


def svg(title, description, contents, height=560):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'
            f'<defs><marker id="good" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{GOOD}"/></marker>'
            f'<marker id="bad" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{BAD}"/></marker></defs>'
            '<style>text{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}</style>'
            f'<rect x="1" y="1" width="958" height="{height-2}" rx="20" fill="#fbfcf8" stroke="#d9e2d9"/>' + contents + '</svg>')


for slug, (title, broken, repaired, services, steps) in SCENES.items():
    # A compare-and-contrast diagram: explicit counterexample and guarantee.
    body = txt(42, 57, title, 27, weight='700')
    body += '<rect x="35" y="93" width="424" height="424" rx="16" fill="#fff6f2"/><rect x="501" y="93" width="424" height="424" rx="16" fill="#eff8f2"/>'
    for x, hue, caption, labels in [(55,BAD,'WITHOUT A BOUNDARY',broken),(522,GOOD,'WITH A NAMED AUTHORITY',repaired)]:
        body += txt(x, 130, caption, 14, hue, '700')
        for n, label in enumerate(labels):
            top=164+n*111
            body += box(x+24,top,342,72,label,color=hue)
            if n < 2:
                body += line(x+195,top+77,x+195,top+104,hue)
    body += txt(480, 485, '→', 36, GOOD, anchor='middle')
    (OUT / f'{slug}-before.svg').write_text(svg(title, f'Without: {"; ".join(broken)}. With: {"; ".join(repaired)}.', body), encoding='utf-8')

    # AWS diagram labels SERVICE and GENERIC ROLE inside the same box.
    body = txt(44, 55, 'AWS BOXES  /  THE ROLE BELOW THE PRODUCT', 16, MUTED, '700')
    body += txt(44, 94, title, 26, weight='700')
    slots = [(40,153),(345,153),(650,153),(192,361),(497,361)]
    for a,b in EDGES[slug]:
        body += connection(slots[a],slots[b])
    for (x,y),(svc,role) in zip(slots,services):
        body += box(x,y,268,94,svc,role)
    body += txt(43, 526, 'Trace identity, permission, and retries through the boxes; service names do not supply those guarantees.', 15, MUTED)
    (OUT / f'{slug}-aws.svg').write_text(svg(f'{title}: AWS architecture',
        'Architecture boxes: ' + ', '.join(f'{svc}, {role}' for svc,role in services), body), encoding='utf-8')

    # Different visual grammar where the failure is a branch, capacity area,
    # security boundary, copy inventory, or reference/eligibility decision.
    body = txt(42,57, title + '  /  THE DECISION', 25, weight='700')
    if slug == 'collaborative-editor':
        body += txt(480,106,'Both edits start from v4. Only the authority assigns v5 and v6.',16,MUTED,anchor='middle')
        body += box(375,131,210,80,'Shared base','version 4')
        body += line(390,218,224,280) + line(568,218,733,280)
        body += box(85,287,284,88,'Ana submits a17','base v4') + box(590,287,284,88,'Ben submits b9','base v4')
        body += line(227,380,398,454) + line(731,380,566,454)
        body += box(358,453,245,77,'Authority','v5 then rebase to v6')
    elif slug == 'overload-shedding':
        body += txt(55,107,'40k/s arrive · 20k/s finish · backlog gains 20k each second',19,MUTED)
        body += '<path d="M97 405 H856 M97 405 V151" stroke="#668278" stroke-width="3"/>'
        body += '<path d="M97 405 L277 352 L455 293 L635 235 L817 178" fill="none" stroke="#af563e" stroke-width="5"/>'
        body += '<path d="M97 405 L277 378 L455 368 L635 362 L817 355" fill="none" stroke="#267259" stroke-width="5"/>'
        for i,n in enumerate(('0s','1s','2s','3s','4s')):
            body+=txt(97+i*180,438,n,14,MUTED,anchor='middle')
        body+=txt(605,166,'Unbounded queue: +80k by 4s',17,BAD,'700')
        body+=txt(543,338,'Admission holds queue near budget',17,GOOD,'700')
        body+=txt(55,487,'Larger buffers increase wait; they do not increase database throughput.',19,INK)
    elif slug == 'tenant-isolation':
        body+=txt(48,107,'Every downstream path must carry the verified tenant identity.',18,MUTED)
        for i,(name,decision) in enumerate([('PRIMARY QUERY','tenant key'),('SEARCH RESULT','fresh ACL'),('CACHE KEY','tenant scope'),('ASYNC JOB','tenant context')]):
            x=42+(i%2)*461;y=140+(i//2)*168
            body+=box(x,y,412,109,name,decision)
        body+=box(309,476,341,53,'DENY CROSS-TENANT READ',color=BAD)
    elif slug == 'knowledge-assistant':
        body+=txt(46,108,'Relevance score is not an access decision.',18,MUTED)
        body+=box(56,154,263,100,'Search index','candidate p17')
        body+=line(328,203,396,203)
        body+=box(406,154,222,100,'Live ACL','access revoked',BAD)
        body+=line(638,203,710,203,BAD)
        body+=box(721,154,193,100,'Model context','omit p17')
        body+='<path d="M521 268 V390 H163" stroke="#b35b43" stroke-width="3" fill="none"/>'
        body+=box(54,402,848,100,'Cached answer also needs a new permission gate','A stale citation cannot be served to a newly unauthorized user.',BAD)
    elif slug == 'erasure-workflow':
        body+=txt(52,111,'One completed checkmark does not close the request.',18,MUTED)
        for i,(name,status) in enumerate([('Primary DB','deleted'),('Search','pending'),('Cache','purged'),('Objects','3 versions left'),('Backups','restore check'),('Feature store','pending'),('Exports','pending'),('Archive','retention hold'),('Answers','invalidated')]):
            x=42+(i%3)*304;y=139+(i//3)*119
            body+=box(x,y,271,90,name,status,GOOD if status in ('deleted','purged','invalidated') else BAD)
        body+=txt(49,528,'Status: IN PROGRESS / HOLD EXCEPTION; never "complete" after the first box.',16,BAD,'700')
    else:
        body += txt(43,95, 'Follow the one piece of state whose interpretation changes.', 15, MUTED)
        for i,(event,state) in enumerate(steps):
            x=40+i*230
            if i<3: body+=line(x+204,227,x+226,227,BAD if i==1 else GOOD)
            body+=box(x,154,201,150,event,state,BAD if i==2 else GOOD)
            body+=txt(x+100,346,f'0{i+1}',15,BAD if i==2 else GOOD,'700','middle')
            if i in (0,2):
                body+=f'<path d="M{x+11} 377 H{x+193}" stroke="{GOOD if i==0 else BAD}" stroke-width="4"/>'
        body += '<rect x="41" y="403" width="878" height="103" rx="12" fill="#f0f6ee"/>'
        body += txt(64,437,'CHECK THE DECISION',13,GOOD,'700')
        body += txt(64,473,f'{steps[-1][0]}: {steps[-1][1]}',20,INK,'600')
    (OUT / f'{slug}-detail.svg').write_text(svg(f'{title}: failure trace',
        '; '.join(f'{a}: {b}' for a,b in steps),body),encoding='utf-8')

print(f'Wrote {len(SCENES)*3} diagrams with service/role labels')
