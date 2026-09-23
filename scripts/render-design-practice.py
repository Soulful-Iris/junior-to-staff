#!/usr/bin/env python3.12
"""Exact, standalone architecture boxes and event traces for the design problems.

Every scene has authored labels and a different failure/repair boundary. No JS
or animation is needed to understand a frame; mobile readers can pan the SVG.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'design-practice'
OUT.mkdir(parents=True, exist_ok=True)
INK = '#20382d'
MUTED = '#69746c'
GOOD = '#326b50'
BAD = '#ac6348'
PAPER = '#fbfcf8'

# (title, failure nodes, protected nodes, broken boundary, repaired boundary,
#  actors, four successive events, state revealed by the final event)
SCENES = {
 'api-quota': ('The last token belongs to one admission decision',
  ['Two gateways','Local counters: 1 left','Both admit'],
  ['Gateway A / B','Atomic quota owner','One admits · one 429'],
  'Separate counters each see 1.', 'A shared conditional decision spends it once.',
  ['CLIENT','GATEWAYS','COUNTER','RESPONSE'],
  ['A and B arrive','Both read 1 left','A commits 0','B fails condition'],
  'The second request is rejected, even across gateways.'),
 'ticket-inventory': ('One seat has one live owner',
  ['Two buyers read','Unprotected updates','Both write HELD'],
  ['Seat A12','Conditional hold','One hold ID'],
  'Read then write allows two owners.', 'The seat transition is the single authority.',
  ['BUYERS','SEAT STORE','PAYMENT','FINALIZE'],
  ['A gets hold h1','Payment starts','Hold expiry races','Recheck h1 owner'],
  'An expired hold cannot quietly become a sold seat.'),
 'realtime-chat': ('A live socket cannot own durable history',
  ['Phone sends','Socket disconnects','Ben misses text'],
  ['Idempotent send','Room message log','Cursor replay'],
  'Lost delivery becomes a missing message.', 'Accepted messages replay from stable IDs.',
  ['ANA','ROOM LOG','GATEWAY','BEN'],
  ['Send id c7','Commit room seq 18','ACK gets lost','Replay from seq 17'],
  'A duplicate send returns the same server message.'),
 'social-feed': ('Popular authors change fanout economics',
  ['Viral author','8m follower writes','Queue saturates'],
  ['One source post','Ordinary fanout','Viral read merge'],
  'One post multiplies into millions of writes.', 'Readers merge viral items without blocking publish.',
  ['AUTHOR','POST STORE','FANOUT','READER'],
  ['Post commits','Ordinary fanout starts','Viral copy skipped','Read merges both'],
  'Privacy is checked again when a feed is read.'),
 'video-processing': ('A large upload needs a separate byte path',
  ['Phone uploads 4 GB','API holds bytes','Request times out'],
  ['Scoped S3 upload','Durable work queue','Ready manifest'],
  'A long API request holds scarce capacity.', 'Status changes only after required outputs exist.',
  ['CREATOR','OBJECT STORE','WORKER','PLAYBACK'],
  ['Upload completes','Worker writes one','Task redelivered','Manifest commits'],
  'READY follows all renditions; retries reuse output keys.'),
 'checkout-payment': ('Two authorities require reconciliation',
  ['Call payment','Reply lost','Retry charges again'],
  ['Order intent','One provider key','Reconcile charge'],
  'A timeout hides a successful external effect.', 'The same attempt has one durable identity.',
  ['CUSTOMER','ORDER STORE','PROVIDER','REPAIR'],
  ['Intent saved','Charge succeeds','Response lost','Lookup by key'],
  'Unknown is resolved before any fresh charge is issued.'),
 'slow-request': ('An average cannot diagnose a slow request',
  ['P50 looks healthy','Pool waits 1.7s','P99 breaches'],
  ['End-to-end metric','Wait + retry spans','Alert + owner'],
  'Averages hide queue wait and retries.', 'Trace exemplars explain fleet-level tail latency.',
  ['CLIENT','POOL','DATABASE','PROVIDER'],
  ['Deadline 2s','Pool wait 1.7s','DB work 30ms','Retry exceeds budget'],
  'The request fails locally before provider average matters.'),
 'durable-jobs': ('Queue progress is not job completion',
  ['Message delivered','Output written','Worker dies'],
  ['Durable job ID','Stable output key','Versioned status'],
  'The ACK and side effect cannot commit together.', 'The next worker verifies output before retrying.',
  ['API','QUEUE','WORKER','JOB STORE'],
  ['Job accepted','Worker writes file','ACK disappears','Redelivery checks'],
  'SUCCEEDED stays true after the second delivery.'),
 'document-search': ('Search access needs live authority',
  ['Index has old ACL','Cache has old hit','Alice sees title'],
  ['Index candidates','Current ACL check','Authorized snippets'],
  'A cached search hit can expose stale permissions.', 'Check eligibility before title and snippet.',
  ['DOCUMENT','INDEXER','ACL','SEARCH'],
  ['Edit at 12:00','Access revoked','Index still stale','Search checks ACL'],
  'Revocation wins even while indexing lags.'),
 'trending-counts': ('One topic can become one hot partition',
  ['100k events/s','One topic counter','Writes queue'],
  ['Salted partials','Window merge','Versioned top ten'],
  'One counter serializes a global spike.', 'Partition writes; merge by event-time window.',
  ['DEVICE','PARTITIONS','WATERMARK','VIEW'],
  ['Event at 12:01','Early top ten read','Event arrives 12:03','Window corrected'],
  'Before watermark closure, rankings are provisional.'),
 'personalized-ranking': ('Eligibility comes before rank output',
  ['Cached rank score','Author blocked','Still recommended'],
  ['Fetch candidates','Check eligibility','Rank or fallback'],
  'A score is not permission to show an item.', 'Final eligibility and budget gate each response.',
  ['REQUEST','FEATURES','RANKER','RESPONSE'],
  ['Deadline 250ms','Feature times out','Fallback chosen','Blocked item removed'],
  'Users receive a safe response within the deadline.'),
 'regional-failover': ('The acknowledgment defines durability',
  ['A commits v9','A returns 200','B missing v9'],
  ['Commit policy','Replicated authority','Fenced new writer'],
  'Routing to B does not move unreplicated data.', 'Acknowledge only under a stated RPO guarantee.',
  ['REGION A','CUSTOMER','REGION B','OPERATOR'],
  ['A writes v9','A returns 200','A loses power','B has only v8'],
  'Under async replication, v9 can be lost after 200.'),
}


def t(x, y, label, size=18, color=INK, anchor='start', weight='normal'):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(label)}</text>')


def panel(x, y, w, h, label, stroke=GOOD, bg='#f1f7ef'):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="2"/>'
            + t(x + w / 2, y + h / 2 + 6, label, 16, INK, 'middle'))


def arrow(x, y, x2, y2, stroke=GOOD):
    return (f'<path d="M{x} {y} L{x2} {y2}" fill="none" stroke="{stroke}" '
            f'stroke-width="2.5" marker-end="url(#arrow-{stroke[1:]})"/>')


def frame(title, description, body, height=460):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 {height}" '
            f'width="880" height="{height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'
            f'<defs><marker id="arrow-{GOOD[1:]}" markerWidth="7" markerHeight="7" '
            f'refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7" fill="{GOOD}"/></marker>'
            f'<marker id="arrow-{BAD[1:]}" markerWidth="7" markerHeight="7" '
            f'refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7" fill="{BAD}"/></marker></defs>'
            '<style>text{font-family:ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif}</style>'
            f'<rect width="880" height="{height}" rx="14" fill="{PAPER}" stroke="#d6dfd4"/>'
            + body + '</svg>')


for i, (name, (title, broken, fixed, risk, repair, actors, events, conclusion)) in enumerate(SCENES.items()):
    # Alternate graph geometry: distributed lanes, vertical authority,
    # and a forked decision. The state labels, not a repeated animation,
    # explain the actual failure boundary for each scenario.
    body = t(32, 43, title, 23, INK, weight='600')
    body += t(32, 86, 'WITHOUT THE GUARANTEE', 12, BAD, weight='bold')
    body += t(32, 224, 'WITH THE GUARANTEE', 12, GOOD, weight='bold')
    for row, labels, hue in [(105, broken, BAD), (255, fixed, GOOD)]:
        mode = i % 3
        xs = [45, 318, 590] if mode == 0 else [52, 327, 600] if mode == 1 else [45, 328, 600]
        ys = [row, row, row] if mode == 0 else [row, row + 19, row] if mode == 1 else [row + 14, row, row + 14]
        for j, label in enumerate(labels):
            body += panel(xs[j], ys[j], 235, 63, label, hue, '#fcefe8' if hue == BAD else '#eef6ee')
            if j:
                body += arrow(xs[j-1] + 239, ys[j-1] + 31, xs[j] - 8, ys[j] + 31, hue)
    body += t(47, 203, risk, 16, BAD)
    body += t(47, 351, repair, 16, GOOD)
    body += f'<path d="M32 380 H848" stroke="#d6dfd4"/>'
    body += t(32, 410, 'NAME THE AUTHORITY', 12, MUTED, weight='bold')
    body += t(240, 410, 'What changes state? What survives a retry?', 15, INK)
    (OUT / f'{name}-boundary.svg').write_text(frame(title, f'{risk} {repair}', body), encoding='utf-8')

    body = t(32, 43, f'{name.replace("-", " ").title()} · one failure in time', 23, INK, weight='600')
    body += t(32, 73, 'Follow the event that crosses the authority boundary.', 14, MUTED)
    body += '<path d="M156 173 H826" stroke="#a8b8a7" stroke-width="3"/>'
    positions = [137, 340, 543, 746]
    for j, (x, actor, event) in enumerate(zip(positions, actors, events)):
        hue = BAD if j == 2 else GOOD
        body += f'<circle cx="{x}" cy="173" r="9" fill="{hue}"/>'
        body += t(x, 129, actor, 12, MUTED, 'middle', 'bold')
        body += t(x, 212, str(j+1).zfill(2), 13, hue, 'middle', 'bold')
        body += panel(x-97, 232, 194, 65, event, hue, '#fcefe8' if j == 2 else '#eef6ee')
    body += f'<path d="M32 319 H848" stroke="#d6dfd4"/>'
    body += t(32, 352, 'CONSEQUENCE', 12, MUTED, weight='bold')
    body += t(32, 383, conclusion, 16, INK)
    (OUT / f'{name}-trace.svg').write_text(frame(f'{title}: failure timeline',
        'Four event positions reveal the state transition. ' + conclusion, body), encoding='utf-8')

print(f'Rendered {len(SCENES) * 2} architecture and failure-timeline diagrams')
