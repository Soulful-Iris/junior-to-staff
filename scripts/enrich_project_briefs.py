#!/usr/bin/env python3
"""Put the deliverable and changed-requirement conversation at the top of projects."""
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- project-expectation:start -->'
END = '<!-- project-expectation:end -->'
VISUALS = {
    'curriculum/02-applications/01-backend/projects/a-public-form.md': 'assets/product/public-form.svg',
    'curriculum/02-applications/02-databases/projects/a-receipt-tracker.md': 'assets/product/receipt-tracker.svg',
    'curriculum/02-applications/03-frontend/projects/a-shared-reading-list.md': 'assets/product/shared-reading-list.svg',
    'curriculum/02-applications/05-security/projects/a-shift-schedule.md': 'assets/product/shift-schedule.svg',
    'projects/reading-list/stages/01-it-works/README.md': 'assets/product/shared-reading-list.svg',
}
ARTIFACT_OVERRIDES = {
    'curriculum/02-applications/01-backend/projects/a-public-form.md': 'A public, accessible form that validates on both sides, survives duplicate submission, makes rejection useful, and gives its authenticated owner a safe export.',
    'curriculum/02-applications/02-databases/projects/a-receipt-tracker.md': 'A receipt workspace where uploads reach durable storage directly, processing state is visible, repeated delivery is harmless, and summaries can be reconciled to source receipts.',
    'curriculum/02-applications/03-frontend/projects/a-shared-reading-list.md': 'A responsive shared reading list where members add and tag links, personal read state never leaks between users, ownership is enforced by the server, and title-fetch failure stays visible.',
    'curriculum/02-applications/05-security/projects/a-shift-schedule.md': 'A role-aware shift schedule where staff can see their work and request swaps, managers approve changes, and every direct API request enforces the same authorization shown by the interface.',
    'projects/reading-list/stages/01-it-works/README.md': 'A complete first reading-list slice: sign in, save a URL, preserve it when title lookup fails, tag it, track read state per person, and refuse another member’s edit or delete.',
}

def clean(value, limit=330):
    value=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',value)
    value=re.sub(r'[*_>`#]+','',value)
    value=' '.join(value.split())
    if len(value)<=limit:return value
    clipped=value[:limit].rsplit(' ',1)[0]
    return clipped.rstrip(' ,;:')+'…'

def first_sentence(value, limit=240):
    value=clean(value,1000)
    match=re.match(r'(.+?[.!?])(?:\s|$)',value)
    return clean(match.group(1) if match else value,limit)

def capture(text, pattern, label):
    match=re.search(pattern,text,re.S)
    if not match:raise RuntimeError(f'Missing {label}')
    return match

def project_files():
    files=[p for p in (ROOT/'curriculum').rglob('*.md') if '/projects/' in p.as_posix()]
    files+=list((ROOT/'projects/reading-list/stages').rglob('README.md'))
    return sorted(files)

def finished_artifact(text, stage):
    if stage:
        section=capture(text,r'## Build and prompt sequence\n(.*?)(?=\n## What done means)', 'stage build section').group(1)
        paragraphs=[clean(p) for p in re.split(r'\n\s*\n',section) if clean(p)]
        return clean(' '.join(paragraphs[:2]))
    raw=capture(text,r'\*\*Build\*\*\s*(.*?)(?=\n\*\*The thought process\*\*)','build outcome').group(1)
    raw=re.sub(r'```.*?```','',raw,flags=re.S)
    raw=re.sub(r'!\[[^]]*\]\([^)]+\)','',raw)
    return clean(raw)

def followup(text, number):
    match=capture(text,rf'## Follow-up {number} · ([^\n]+).*?\*\*Changed requirement:\*\*\s*(.*?)(?=\n\s*<details>)','follow-up')
    title=clean(match.group(1),80);question=clean(match.group(2),250)
    section=text[match.end():]
    expected=capture(section,r'<summary>Expected reasoning and changed diagram</summary>\s*(.*?)(?=\n\s*```|\n\s*</details>)','follow-up expectation').group(1)
    return title,question,clean(expected,300)

def render(path, text):
    relative=path.relative_to(ROOT).as_posix();stage='/stages/' in relative
    artifact=ARTIFACT_OVERRIDES.get(relative) or finished_artifact(text,stage)
    f1=followup(text,1);f2=followup(text,2)
    evidence_section=capture(text,r'## Evidence to bring to review\s*(.*?)(?=\n\*\*Senior expectation:\*\*)','evidence').group(1)
    evidence=first_sentence(evidence_section)
    visual=''
    if relative in VISUALS:
        target=ROOT/VISUALS[relative]
        href=os.path.relpath(target,path.parent).replace(os.sep,'/')
        visual=(f'\n![Expected end product preview for this project: the main workflow, visible state, '
                f'and reviewable outcomes]({href})\n')
    return f'''{START}

## What you are expected to hand over

**The finished artifact:** {artifact}
{visual}
Treat that sentence as a review contract, not an inspiration. A reviewable
submission contains all of the following:

- the narrow working slice or decision artifact described above, reproducible
  from a clean checkout with assumptions stated;
- captured proof of the normal flow **and** the boundary/failure row above;
- tests, probes, or metrics that can go red when the important guarantee breaks;
- a short decision record naming ownership, excluded scope, and the first
  operational limit; and
- a changed contract, diagram, and new evidence for each follow-up—not only a
  paragraph claiming the original design still works.

### How the review conversation gets harder

| Review gate | The interviewer changes | Expected response |
|---|---|---|
| Baseline | Run the small example from the table above. | Demonstrate the observable outcome end to end and identify which boundary owns it. |
| Failure | Reproduce the boundary/failure row above. | Show the failure before the fix, then prove the protected behavior without hiding the error. |
| Senior · {f1[0]} | {f1[1]} | {f1[2]} |
| Lead · {f2[0]} | {f2[1]} | {f2[2]} |
| Evidence | A reviewer asks, “How do you know?” | {evidence} |
| Handoff | The author is unavailable and the environment is new. | Another engineer can run, observe, break, and recover the artifact from the repository evidence. |

Before implementation, say the baseline invariant, the owner of each piece of
state, and what the user sees when the named dependency or assumption fails. That
five-minute explanation is part of the project: if it is vague, the build is not
ready to begin.

{END}'''

def main():
    files=project_files()
    if len(files)!=45:raise RuntimeError(f'Expected 45 project briefs, found {len(files)}')
    for path in files:
        text=path.read_text();block=render(path,text)
        if START in text:
            text=re.sub(re.escape(START)+r'.*?'+re.escape(END),block,text,flags=re.S)
        else:
            lines=text.splitlines()
            start=next(i for i,line in enumerate(lines) if line.startswith('| Case | Exact input or workload | Expected outcome |'))
            end=start
            while end+1<len(lines) and lines[end+1].startswith('|'):end+=1
            lines[end+1:end+1]=['',block]
            text='\n'.join(lines)+('\n' if text.endswith('\n') else '')
        path.write_text(text)
    print(f'Updated {len(files)} project briefs with deliverables and review gates.')

if __name__=='__main__':main()
