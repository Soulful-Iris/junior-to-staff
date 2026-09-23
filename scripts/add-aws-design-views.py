#!/usr/bin/env python3.12
"""Add AWS-labeled box views to the twelve earlier design exercises.

The role inside every SVG box is deliberately provider-neutral; the table in
the lesson states why that service fits and where an alternative wins.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'design-practice'

# slug, relative chapter, five (AWS name, general job), architectural choices
SCENES = [
 ('api-quota','03-production/01-system-design',
  [('Amazon API Gateway','edge entry'),('AWS Lambda','admission worker'),('Amazon DynamoDB','atomic quota store'),('Amazon ElastiCache','optional read cache'),('Amazon CloudWatch','decision telemetry')],
  'DynamoDB conditional updates arbitrate a single shared quota key; a transaction or reservation handles minute and daily quotas together. An ElastiCache cache is useful for approximate reads, but a stale cache cannot enforce an exact limit. ECS can replace Lambda when connection reuse or steady traffic justifies a service.'),
 ('ticket-inventory','03-production/01-system-design',
  [('Amazon API Gateway','admission entry'),('Amazon SQS','waiting room queue'),('AWS Lambda','hold processor'),('Amazon DynamoDB','seat authority'),('Amazon CloudWatch','hold telemetry')],
  'DynamoDB conditionally moves one seat from FREE to HELD; Aurora with a row lock is an alternative when grouped seats require relational transactions. SQS buffers arrivals but is not the seat owner. Lambda handles holds; ECS suits long-lived, predictable reservation workers.'),
 ('realtime-chat','03-production/01-system-design',
  [('API Gateway WebSocket','live connection'),('Amazon ECS','room sequencer'),('Amazon DynamoDB','message log'),('Amazon SQS','fanout buffer'),('Amazon CloudWatch','replay telemetry')],
  'WebSocket connections deliver low-latency updates, while a DynamoDB log owns acknowledged history. ECS owners may assign room sequence numbers; a database conditional write must still fence old owners. SQS fans out work but can redeliver, so reconnect uses log cursors instead.'),
 ('social-feed','03-production/01-system-design',
  [('Amazon API Gateway','read/write entry'),('Amazon DynamoDB','post store'),('Amazon SQS','fanout buffer'),('Amazon ElastiCache','feed cache'),('Amazon CloudWatch','freshness metrics')],
  'DynamoDB owns post IDs and versioned views; Aurora is a reasonable alternative for follower joins under smaller load. SQS decouples ordinary fanout but has duplicate delivery; cache readers merge high-fanout authors. Neither queue nor cache replaces read-time privacy checks.'),
 ('video-processing','03-production/01-system-design',
  [('Amazon S3','upload object store'),('Amazon SQS','processing queue'),('AWS Elemental MediaConvert','video transcoder'),('Amazon DynamoDB','job status authority'),('Amazon CloudFront','playback CDN')],
  'Direct S3 upload keeps bytes away from API workers. MediaConvert handles managed media jobs; ECS with FFmpeg fits custom codecs and scheduling. DynamoDB moves status to READY only when outputs exist, SQS can redeliver, and CloudFront distributes authorized renditions.'),
 ('checkout-payment','03-production/01-system-design',
  [('Amazon API Gateway','order entry'),('Amazon RDS / Aurora','order + outbox'),('Amazon SQS','payment attempt queue'),('AWS Lambda','reconcile worker'),('Amazon CloudWatch','unknown-charge alarm')],
  'An Aurora transaction records intent and local state; DynamoDB transactional writes are an alternative for key-oriented orders. SQS retries can duplicate work: the provider idempotency key and status lookup are still required. An ECS worker suits high-volume, long-running reconciliation.'),
 ('slow-request','03-production/04-observability',
  [('Application Load Balancer','request ingress'),('Amazon ECS','application work'),('Amazon RDS','database work'),('AWS X-Ray','distributed trace'),('Amazon CloudWatch','latency metrics')],
  'CloudWatch holds fleet-level denominators and tail latency by route; X-Ray or an OpenTelemetry-compatible tracing stack identifies spans and queue wait. ALB timing is a separate boundary. A trace sample cannot substitute for complete request metrics.'),
 ('durable-jobs','03-production/05-reliability',
  [('Amazon API Gateway','job creation'),('Amazon DynamoDB','job state authority'),('Amazon SQS','at-least-once queue'),('AWS Lambda','idempotent worker'),('Amazon S3','output object store')],
  'SQS buffers accepted jobs but redelivers on a lost acknowledgement. DynamoDB stores stable job IDs and conditional status; S3 outputs use stable keys and existence checks. ECS can replace Lambda for jobs that exceed its duration or memory envelope.'),
 ('document-search','04-scale-and-evolution/01-data-at-scale',
  [('Amazon S3','document source'),('Amazon OpenSearch Service','candidate search index'),('Amazon DynamoDB','live permission store'),('Amazon ECS','authorization gate'),('Amazon CloudWatch','index freshness')],
  'OpenSearch finds candidates, not permission; DynamoDB or Aurora holds current ACL under the chosen data model. ECS checks it before titles or snippets. Bedrock Knowledge Bases can manage retrieval, but the independent live permission check remains.'),
 ('trending-counts','04-scale-and-evolution/01-data-at-scale',
  [('Amazon Kinesis','partitioned event stream'),('AWS Lambda','window aggregation'),('Amazon DynamoDB','versioned top list'),('Amazon S3','raw event archive'),('Amazon CloudWatch','lag telemetry')],
  'Kinesis partitions input; a hot topic must be salted or otherwise distributed, because a hot partition key stays hot. Lambda aggregates windows or Managed Service for Apache Flink handles complex event-time work; DynamoDB serves a versioned result and S3 enables replay.'),
 ('personalized-ranking','04-scale-and-evolution/03-ai-systems',
  [('Amazon API Gateway','request entry'),('Amazon ECS','eligibility + fallback'),('Amazon SageMaker','ranker inference'),('Amazon DynamoDB','feature lookup'),('Amazon CloudWatch','latency + quality')],
  'SageMaker endpoints serve a managed ranker; ECS inference fits a lighter model with existing deployment tooling. DynamoDB serves versioned online features. ECS enforces final eligibility and fallback; CloudWatch observes latency and denial outcomes, not model quality by itself.'),
 ('regional-failover','04-scale-and-evolution/04-migrations',
  [('Amazon Route 53','region routing'),('Amazon ECS','fenced writer'),('DynamoDB Global Tables','replicated data'),('Amazon CloudWatch','health evidence'),('Amazon S3','recovery backups')],
  'Route 53 changes where clients connect but cannot replicate missing acknowledged writes. DynamoDB Global Tables have mode-dependent consistency; Aurora Global Database is another choice with its own replication and failover guarantees. A writer epoch must be enforced at write time, and CloudWatch health alone cannot fence an old writer.'),
]

EDGES = {
 'api-quota':[(0,1),(1,2),(1,3),(1,4)],
 'ticket-inventory':[(0,1),(1,2),(2,3),(2,4)],
 'realtime-chat':[(0,1),(1,2),(1,3),(1,4)],
 'social-feed':[(0,1),(1,2),(0,3),(2,4)],
 'video-processing':[(0,1),(1,2),(2,3),(3,4)],
 'checkout-payment':[(0,1),(1,2),(2,3),(3,4)],
 'slow-request':[(0,1),(1,2),(1,3),(1,4)],
 'durable-jobs':[(0,1),(1,2),(2,3),(3,4)],
 'document-search':[(0,1),(1,3),(3,2),(3,4)],
 'trending-counts':[(0,1),(1,2),(0,3),(1,4)],
 'personalized-ranking':[(0,1),(1,2),(3,1),(1,4)],
 'regional-failover':[(0,1),(1,2),(1,3),(2,4)],
}


def label(x,y,value,size=15,color='#253a32',weight='normal'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="middle" fill="{color}">{escape(value)}</text>'


for slug, chapter, services, rationale in SCENES:
    path=ROOT/'curriculum'/chapter/'problems'/f'{slug}.md'
    assert path.exists(),path
    title=slug.replace('-',' ').title()
    s=('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="555" viewBox="0 0 960 555" role="img" aria-labelledby="title desc">'
       f'<title id="title">{escape(title)}: AWS services and their architectural roles</title>'
       f'<desc id="desc">Five AWS boxes named together with their general roles: {escape("; ".join(a+" is "+b for a,b in services))}.</desc>'
       '<style>text{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}</style>'
       '<defs><marker id="arr" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L9 4L0 9" fill="#2d785a"/></marker></defs>'
       '<rect x="1" y="1" width="958" height="553" rx="19" fill="#fbfcf8" stroke="#d7e3d8"/>')
    s += label(480,54,'AWS SERVICE / GENERAL ROLE',17,'#627369','bold')
    pts=[(35,120),(345,120),(655,120),(190,339),(500,339)]
    for (a,b) in EDGES[slug]:
        x,y=pts[a];xx,yy=pts[b]
        if y==yy and x<xx: d=f'M{x+269} {y+49} L{xx-9} {yy+49}'
        elif y==yy: d=f'M{x-4} {y+49} L{xx+274} {yy+49}'
        elif y<yy: d=f'M{x+131} {y+105} L{xx+131} {yy-12}'
        else: d=f'M{x+131} {y-8} L{xx+131} {yy+110}'
        s += f'<path d="{d}" stroke="#2d785a" stroke-width="2.5" fill="none" marker-end="url(#arr)"/>'
    for (x,y),(service,role) in zip(pts,services):
        s+=f'<rect x="{x}" y="{y}" width="265" height="97" rx="12" fill="#eff7ef" stroke="#317755" stroke-width="2"/>'
        s+=label(x+132,y+37,service,14 if len(service)>25 else 16,weight='bold')
        s+=label(x+132,y+68,role,15,'#657369')
    s+=label(480,505,'Name which box owns truth; routing, queues and caches are not a transaction.',15,'#52675c')+'</svg>'
    (OUT/f'{slug}-aws.svg').write_text(s,encoding='utf-8')
    current=path.read_text(encoding='utf-8')
    marker='## Put the AWS names on the boxes'
    if marker in current: continue
    section=(f'{marker}\n\n![AWS service boxes labeled with their general architectural roles](../../../../assets/design-practice/{slug}-aws.svg)\n\n'
             f'**Why these boxes, and what changes the choice:** {rationale}\n\n'
             'Read the smaller label under each service first: it names the architectural job. Then ask whether that service supplies the guarantee in the problem, or simply moves work to the next box.\n\n')
    assert '**Senior follow-up:**' in current,slug
    path.write_text(current.replace('**Senior follow-up:**',section+'**Senior follow-up:**',1),encoding='utf-8')

print(f'Wrote {len(SCENES)} AWS architecture diagrams and inserted service decisions')
