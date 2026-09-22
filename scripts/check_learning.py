"""Check local learning links, SVG accessibility/structure, and lab configuration."""
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
errors=[]
files=[ROOT/'README.md',ROOT/'docs/HOW-TO-USE.md',ROOT/'docs/STYLE.md']+list((ROOT/'paths').rglob('*.md'))+list((ROOT/'tiers').glob('*/*/README.md'))
for path in files:
    content=path.read_text()
    # Code samples may contain syntax that looks like a Markdown link.
    prose=re.sub(r'```.*?```','',content,flags=re.S)
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',prose):
        if target.startswith(('https://','http://','mailto:','#')):continue
        target=target.split('#')[0]
        if not (path.parent/target).exists():errors.append(f'{path.relative_to(ROOT)}: missing {target}')
    if content.count('```')%2:errors.append(f'{path}: unclosed code fence')
ns={'s':'http://www.w3.org/2000/svg'}
for path in (ROOT/'assets/learning').glob('*-mechanism.svg'):
    root=ET.parse(path).getroot()
    if root.find('s:title',ns) is None or 'prefers-reduced-motion' not in path.read_text():
        errors.append(f'{path}: missing accessibility metadata')
data=json.loads((ROOT/'scripts/learning_storyboards.json').read_text())
for item in data:
    for mode in ['compare','trace','still']:
        path=ROOT/'assets/learning'/f'{item["key"]}-{mode}.svg'
        try:
            root=ET.parse(path).getroot()
            if root.find('s:title',ns) is None or root.find('s:desc',ns) is None:errors.append(f'{path}: missing accessible description')
            if mode!='still' and 'prefers-reduced-motion' not in path.read_text():errors.append(f'{path}: no reduced motion')
        except Exception as e:errors.append(f'{path}: {e}')
    if item['chapter']:
        chapter=next((ROOT/'tiers').glob('*/'+item['chapter']+'/README.md'))
        for mode in ['compare','trace','still']:
            if f'{item["key"]}-{mode}.svg' not in chapter.read_text():errors.append(f'{chapter}: missing {mode}')
template=json.loads((ROOT/'paths/interviews/aws/labs/job-pipeline/template.yaml').read_text())
props=template['Resources']['Worker']['Properties'];event=props['Events']['JobsEvent']['Properties']
assert event['FunctionResponseTypes']==['ReportBatchItemFailures']
assert template['Resources']['Jobs']['Properties']['VisibilityTimeout']>=6*props['Timeout']
assert props['ReservedConcurrentExecutions']>=event['ScalingConfig']['MaximumConcurrency']
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f'Checked {len(files)} Markdown files, {len(list((ROOT/'assets/learning').glob('*.svg')))} SVGs, 21 chapter integrations, and lab configuration invariants.')
