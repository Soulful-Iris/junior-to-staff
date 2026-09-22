"""Check local navigation, native SVG animation structure, and lab invariants."""
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
errors=[]
files=sorted(ROOT.rglob('*.md'))
for path in files:
    content=path.read_text();prose=re.sub(r'```.*?```','',content,flags=re.S)
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',prose):
        if target.startswith(('https://','http://','mailto:','#')):continue
        target=target.split('#')[0]
        if not (path.parent/target).exists():errors.append(f'{path.relative_to(ROOT)}: missing {target}')
    if content.count('```')%2:errors.append(f'{path}: unclosed code fence')
    if content.count('<details>')!=content.count('</details>'):errors.append(f'{path}: unclosed disclosure')
ns={'s':'http://www.w3.org/2000/svg'}
manifest=json.loads((ROOT/'assets/learning/manifest.json').read_text())
for item in manifest:
    for suffix in ['', '-still']:
        p=ROOT/'assets/learning'/f'{item["key"]}{suffix}.svg'
        try:
            root=ET.parse(p).getroot()
            for tag in ['title','desc']:
                if root.find('s:'+tag,ns) is None:errors.append(f'{p}: no {tag}')
            if not suffix:
                if 'prefers-reduced-motion' not in p.read_text():errors.append(f'{p}: no reduced motion')
                if not root.findall('.//s:animate',ns) and not root.findall('.//s:animateMotion',ns)+root.findall('.//s:animateTransform',ns):errors.append(f'{p}: no native motion')
            for anim in root.findall('.//s:animate',ns)+root.findall('.//s:animateMotion',ns)+root.findall('.//s:animateTransform',ns):
                if anim.get('calcMode')=='discrete':errors.append(f'{p}: slideshow interpolation is not allowed')
                if anim.tag.endswith('}animate') and anim.get('attributeName')=='transform':errors.append(f'{p}: use animateTransform or animateMotion for transforms')
                if anim.tag.endswith('animateMotion') and not anim.get('path'):errors.append(f'{p}: missing motion path')
                if not anim.get('keyTimes'):continue
                values=anim.get('values',anim.get('keyPoints','')).split(';');times=[float(x) for x in anim.get('keyTimes','').split(';')]
                if len(values)!=len(times) or times[0]!=0 or times[-1]!=1 or times!=sorted(set(times)):
                    errors.append(f'{p}: invalid timeline')
                if anim.get('calcMode')=='spline':
                    curves=anim.get('keySplines','').split(';')
                    if len(curves)!=len(times)-1 or any(len(c.split())!=4 for c in curves):errors.append(f'{p}: invalid easing')
        except Exception as e:errors.append(f'{p}: {e}')
template=json.loads((ROOT/'paths/interviews/aws/labs/job-pipeline/template.yaml').read_text())
props=template['Resources']['Worker']['Properties'];event=props['Events']['JobsEvent']['Properties']
assert event['FunctionResponseTypes']==['ReportBatchItemFailures']
assert template['Resources']['Jobs']['Properties']['VisibilityTimeout']>=6*props['Timeout']
assert props['ReservedConcurrentExecutions']>=event['ScalingConfig']['MaximumConcurrency']
if errors:print('\n'.join(errors));sys.exit(1)
print(f'Checked {len(files)} Markdown files, {len(manifest)*2} mechanism SVGs, and lab invariants.')
