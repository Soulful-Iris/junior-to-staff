"""The teaching sequence. Source documents remain canonical and unchanged.

Navigation/index pages are reference material, not tasks. Primers precede the
problems they introduce; continuing-project stages and assessments arrive in
context. Every source page is still published and available in the contents.
"""
from pathlib import Path

NAV_NAMES = {'projects.md', 'ai-projects.md', 'change-projects.md', 'foundations-index.md', 'advanced-index.md'}
FOUNDATION_ORDER = [
    ('Cost and basic collections', ['00-cost', '10-sequences', '11-sets', '01-maps']),
    ('Order and linked structures', ['07-stack', '12-queues', '13-linked-lists', '14-trees', '06-heaps', '15-tries']),
    ('Connections', ['05-graphs', '16-union-find', '21-weighted-paths']),
    ('Algorithms that narrow the work', ['22-sorting', '04-order', '17-two-pointers', '02-windows', '03-prefix', '18-greedy']),
    ('Search, reuse, and selection', ['09-search', '08-dp', '19-bits', '20-choose']),
]
CODING_ORDER = [
    ('Scan and remember', ['practice-sequence.md', 1, 2, 3, 4, 5, 6, 7, 8]),
    ('Order and boundaries', [9, 10, 11, 12, 13]),
    ('Identity and recursion', [14, 15, 16, 17, 18, 19, 20]),
    ('Graphs and retained state', [21, 22, 23, 24, 25, 26, 27, 30]),
    ('Search and recurrence', [31, 32, 33, 34, 35, 36]),
    ('Stacks, parsing, and streams', [37, 38, 39, 41]),
    ('Consolidate and assess', ['pattern-notes.md', 'reference.md']),
]
# These existing standalone materials were previously outside the reading flow.
INSERT = {
    2: ['practice/coding-mock.md', 'practice/candidate/coding.md'],
    6: ['projects/reading-list/stages/01-it-works/README.md', 'practice/candidate/full-stack.md'],
    7: ['practice/candidate/practical-debug.md'],
    9: ['practice/candidate/design.md'],
    10: ['projects/reading-list/stages/03-under-load/README.md'],
    12: ['practice/candidate/infra.md'],
    15: ['projects/reading-list/stages/02-it-survives/README.md'],
    16: ['projects/reading-list/stages/05-it-changes/README.md'],
    18: ['projects/reading-list/stages/04-it-reasons/README.md'],
}


def organize(pages):
    by_src = {p['src']: p for p in pages}
    # Preserve published lesson URLs while separating teaching from rehearsal.
    foundations = by_src['curriculum/01-code/02-data-structures-algorithms/README.md']
    practice = by_src['curriculum/01-code/03-coding-practice/README.md']
    for p in pages:
        if p.get('chapter') == foundations['chapter'] and p.get('sub') and '/lessons/' not in p['src']:
            p.update(chapter=practice['chapter'], subject=practice['subject'],
                     subject_title=practice['title'])
    sequence = [pages[0]]
    for group in [p for p in pages if p['kind'] == 'group']:
        sequence.append(group)
        for chapter in [p for p in pages if p['kind'] == 'subject' and p['group'] == group['group']]:
            number = chapter['chapter']
            sequence.append(chapter)
            children = [p for p in pages if p.get('chapter') == number and p.get('sub') and Path(p['src']).name not in NAV_NAMES]
            if number == foundations['chapter']:
                prefix = str(Path(chapter['src']).parent) + '/lessons/'
                ordered = []
                for label, stems in FOUNDATION_ORDER:
                    for stem in stems:
                        p = by_src[prefix + stem + '.md']
                        p['section'] = label
                        ordered.append(p)
                assert {p['src'] for p in children} == {p['src'] for p in ordered}, 'Unsequenced foundations'
                children = ordered
            if number == practice['chapter']:
                prefix = 'curriculum/01-code/02-data-structures-algorithms/'
                ordered = []
                for label, keys in CODING_ORDER:
                    for key in keys:
                        p = next((p for p in children if (f'/problems/{key:02}-' in p['src'] if isinstance(key, int) else p['src'] == prefix + key)), None)
                        if p:
                            p['section'] = label
                            ordered.append(p)
                assert {p['src'] for p in children} == {p['src'] for p in ordered}, 'Unsequenced coding material'
                children = ordered
            for source in INSERT.get(number, []):
                p = by_src[source]
                p.update(group=group['group'], subject=chapter['subject'], chapter=number,
                         gnum=group['gnum'], subject_title=chapter['title'], group_title=group['title'],
                         part_label=group.get('part_label'),
                         section='Projects and practical assessment', sub=0)
                children.append(p)
            for n, p in enumerate(children, 1):
                p['sub'] = n
                p['step_count'] = len(children)
            sequence.extend(children)
    # An elective company studio follows the core book, with its own linear
    # next/previous sequence. The reference shelf remains outside that path.
    sequence.extend(by_src[f'companies/{name}'] for name in
                    ('README.md', 'openai.md', 'reddit.md', 'meta.md', 'databricks.md', 'observe.md', 'crowdstrike.md'))
    assert len({p['src'] for p in sequence}) == len(sequence)
    for n, page in enumerate(sequence):
        page['position'] = n
        page['sequence_count'] = len(sequence)
    members = {p['src'] for p in sequence}
    for p in pages:
        if p['src'] not in members:
            p.pop('sub', None)
    return sequence
