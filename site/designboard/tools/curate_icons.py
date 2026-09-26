#!/usr/bin/env python3
"""Copy the icons catalog.json names out of AWS's Architecture Icons package.

    python3 site/designboard/tools/curate_icons.py ~/Downloads/Asset-Package_07312026

The package is AWS's own download (aws.amazon.com/architecture/icons), which
AWS allows "to create architecture diagrams". The board ships only the icons
its catalog uses, byte for byte: no recolouring, cropping or redrawing. Each
catalog entry names its source path inside the package, so this can be re-run
against a newer package and the diff shows exactly which pictures changed.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def main(package):
    package = Path(package).expanduser()
    catalog = json.loads((HERE / 'catalog.json').read_text())
    dest = HERE / 'icons'
    dest.mkdir(exist_ok=True)
    wanted = [p for p in catalog['parts'] + catalog['groups'] if p.get('source')]
    missing = [p['source'] for p in wanted if not (package / p['source']).is_file()]
    if missing:
        sys.exit('not in the package:\n  ' + '\n  '.join(missing))
    for p in wanted:
        shutil.copyfile(package / p['source'], dest / p['icon'])
    keep = {p['icon'] for p in wanted}
    for extra in dest.glob('*.svg'):
        if extra.name not in keep:
            extra.unlink()
    print(f'{len(keep)} icons in {dest}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '~/scratch/aws-icons')
