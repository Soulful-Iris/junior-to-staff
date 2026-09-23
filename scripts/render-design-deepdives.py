#!/usr/bin/env python3.12
"""Eight distinct diagrams for the physical bottleneck behind a design prompt."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets/design-practice'
INK, GREEN, ORANGE, MUTED = '#20382d', '#326b50', '#ac6348', '#69746c'


def text(x, y, value, size=16, color=INK, anchor='start', weight='normal'):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>')


def box(x, y, width, height, label, color=GREEN, fill='#eff6ee'):
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="10" fill="{fill}" stroke="{color}" stroke-width="2"/>'
            + text(x + width / 2, y + height / 2 + 6, label, 16, INK, 'middle'))


def line(path, color=GREEN, dashed=False, arrow=True):
    dash = 'stroke-dasharray="6 5"' if dashed else ''
    marker = f'marker-end="url(#{"bad" if color == ORANGE else "good"})"' if arrow else ''
    return (f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" '
            f'{dash} {marker}/>')


def save(name, title, description, drawing):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 450" '
           f'width="900" height="450" role="img" aria-labelledby="title desc">'
           f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'
           f'<defs><marker id="good" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
           f'<path d="M0 0 L7 3.5 L0 7" fill="{GREEN}"/></marker>'
           f'<marker id="bad" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
           f'<path d="M0 0 L7 3.5 L0 7" fill="{ORANGE}"/></marker></defs>'
           '<style>text{font-family:ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif}</style>'
           '<rect width="900" height="450" rx="14" fill="#fbfcf8" stroke="#d6dfd4"/>'
           + text(34, 43, title, 24, INK, weight='bold')
           + text(34, 71, description, 14, MUTED)
           + drawing + '</svg>')
    (OUT / f'{name}-deep.svg').write_text(svg, encoding='utf-8')


# Two independent arrivals reach ONE conditional state transition.
d = box(42, 127, 194, 60, 'Gateway A · request 41') + box(42, 258, 194, 60, 'Gateway B · request 42')
d += box(342, 190, 226, 75, 'Counter: 1 remaining')
d += line('M237 157 H294 V211 H335') + line('M237 288 H294 V243 H335')
d += box(676, 130, 180, 58, 'A admits · 0 left') + box(676, 270, 180, 58, 'B gets 429', ORANGE, '#fcefe8')
d += line('M570 215 H632 V159 H669') + line('M570 246 H632 V299 H669', ORANGE)
d += text(360, 370, 'One atomic update determines the winner.', 17, GREEN)
d += text(42, 405, 'If each gateway keeps its own counter, both requests see 1 and both pass.', 16, ORANGE)
save('api-quota','Race the last quota token','Two gateways see the same organization and period.',d)

# One guarded state machine; the dashed late payment path cannot revive expiry.
d = box(52, 166, 172, 66, 'AVAILABLE') + box(360, 166, 172, 66, 'HELD · h1') + box(670, 166, 172, 66, 'SOLD · h1')
d += line('M226 199 H352') + line('M535 199 H662')
d += text(263, 165, 'CAS', 14, GREEN, 'middle') + text(582, 165, 'confirm h1', 14, GREEN, 'middle')
d += line('M450 235 V324 H140 V241', ORANGE)
d += text(290, 344, 'expiry: release h1 only if still HELD', 15, ORANGE, 'middle')
d += box(554, 315, 288, 50, 'Late payment: refund or repair', ORANGE, '#fcefe8')
d += line('M450 234 V288 H700 V305', ORANGE, True)
d += text(50, 407, 'TTL cleanup may lag. An expiry check at the write decides whether a hold is valid.', 16, MUTED)
save('ticket-inventory','A12 has a guarded lifecycle','The hold ID is checked again when payment completes.',d)

# Fanout drawn as differing multiplicative workloads.
d = box(38, 167, 147, 72, 'One new post')
d += line('M186 199 H251 V143 H290') + line('M251 199 V283 H290')
d += box(298, 113, 207, 66, 'Ordinary · 500 fans') + box(298, 262, 207, 66, 'Viral · 8m fans', ORANGE, '#fcefe8')
d += line('M508 144 H602') + line('M508 293 H602', ORANGE)
d += box(610, 113, 245, 66, '≈ 500 fanout writes') + box(610, 262, 245, 66, 'Merge at read time')
d += text(43, 374, 'Four viral posts × 8 million followers = 32 million candidate writes.', 18, ORANGE)
d += text(43, 409, 'The source post remains durable; the feed projection can be rebuilt.', 16, MUTED)
save('social-feed','The eight-million-follower fork','Hybrid fanout changes where the multiplication happens.',d)

# A quantitative queue rather than another network chain.
d = text(50, 112, 'ARRIVALS', 12, MUTED, weight='bold') + text(327, 112, 'WORKER CAPACITY', 12, MUTED, weight='bold')
d += text(50, 172, '500 / minute', 25, INK, weight='bold') + text(330, 172, '50 workers', 25, INK, weight='bold')
d += text(330, 202, '20 seconds / job → 150 / minute', 16, MUTED)
d += line('M230 158 H310') + line('M630 158 H712')
d += box(716, 124, 150, 70, '+350 / min', ORANGE, '#fcefe8')
for i in range(7):
    d += f'<rect x="{75+i*98}" y="{290-i*13}" width="62" height="{35+i*13}" rx="4" fill="{ORANGE if i>3 else GREEN}" opacity=".82"/>'
d += text(70, 379, 'Queued work grows while accepted jobs outpace completed jobs.', 16)
d += text(70, 414, 'Measure oldest job age and admission rate; an empty DLQ does not mean healthy.', 15, MUTED)
save('durable-jobs','The queue grows by 350 jobs each minute','Steady-state estimate: 50 workers × 3 jobs per minute = 150 completions per minute.',d)

# Candidate retrieval and authorization are explicitly separate gates.
d = box(35, 185, 169, 68, 'Search query') + box(278, 185, 177, 68, 'Index hits: 20')
d += line('M207 219 H269')
d += box(525, 164, 155, 105, 'Current ACL') + line('M458 219 H516')
d += box(742, 110, 130, 64, '19 allowed') + box(742, 265, 130, 64, '1 denied', ORANGE, '#fcefe8')
d += line('M682 195 H712 V142 H733') + line('M682 239 H712 V297 H733', ORANGE)
d += text(53, 316, 'An index hit is a candidate, never permission to reveal its title or snippet.', 17, GREEN)
d += text(53, 368, 'Index freshness target: 2 min.', 15, MUTED)
d += text(53, 399, 'Revocation target: 1 min. Each read checks the authority.', 15, MUTED)
save('document-search','Twenty hits enter, nineteen can be shown','The search index and the access-control source have different freshness contracts.',d)

# Partial counters are a visual grid with exact write rate per partition.
d = box(43, 180, 190, 72, '100k events / sec', ORANGE, '#fcefe8')
d += text(290, 128, 'SALT BY TOPIC + SHARD', 12, GREEN, weight='bold')
for j in range(3):
    y=138+j*62
    d += box(332, y, 201, 46, f'Shard {j+1} · ~1k / sec')
    d += line(f'M236 213 H275 V{y+23} H323')
    d += line(f'M536 {y+23} H590 V213 H626')
d += box(634, 177, 205, 73, 'Event-time merge')
d += text(433, 350, '… 97 more partials', 15, GREEN, 'middle')
d += text(42, 393, '100 shards × ~1,000 events/s each = 100,000 events/s.', 18)
d += text(42, 425, 'Dedup IDs and a watermark decide whether late counts revise an early result.', 15, MUTED)
save('trending-counts','Spread a hot topic across 100 partials','Partial counts are merged under event-time and deduplication rules.',d)

# A deadline budget drawn as a composition, with an exhausted branch.
d = text(45, 133, '250 ms P95 request deadline', 20, INK, weight='bold')
parts=[(35,30,'Candidates'),(129,100,'Features'),(441,50,'Rank'),(597,20,'ACL'),(659,30,'Network'),(753,20,'Slack')]
scale=3.12
for x,width,label in parts:
    w=width*scale
    d += f'<rect x="{x}" y="171" width="{w}" height="65" rx="5" fill="{GREEN if label not in ("Features", "Slack") else "#d6e9d9"}"/>'
    d += text(x+w/2, 203, label, 12, '#fff' if label not in ('Features','Slack') else INK, 'middle','bold')
    d += text(x+w/2, 256, f'{width} ms', 13, INK, 'middle')
d += text(45, 322, 'Feature call uses 170 ms instead of 100 → exceed budget by 70 ms.', 17, ORANGE)
d += text(45, 367, 'Fallback before expiry; authorization still runs on every result.', 17, GREEN)
save('personalized-ranking','A deadline is shared across every box','Example budget: 30 + 100 + 50 + 20 + 30 + 20 = 250 ms.',d)

# Two regions, explicit acknowledgement and version mismatch.
d = box(48, 126, 235, 79, 'Region A · committed v9')
d += box(602, 126, 235, 79, 'Region B · only v8', ORANGE, '#fcefe8')
d += line('M288 166 H360', ORANGE) + line('M495 166 H591', ORANGE, True)
d += box(368, 125, 125, 79, 'Replication', ORANGE, '#fcefe8')
d += line('M168 209 V307 H354', GREEN)
d += box(364, 277, 179, 70, '200 returned')
d += line('M545 314 H604 V235', ORANGE, True)
d += text(548, 267, 'A fails', 15, ORANGE)
d += text(50, 389, 'RPO zero requires v9 to cross the required durable boundary before 200.', 17, INK)
d += text(50, 419, 'Failing over routing cannot recover an unreplicated acknowledged write.', 14, MUTED)
save('regional-failover','Version v9 exists in A and not in B','The point of acknowledgment determines which write can survive total regional loss.',d)

print('Rendered 8 distinct deeper architecture diagrams')
