"""Compare required source content with published lessons, not a minimum count."""
from collections import Counter
import hashlib
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
import markdown


def source_references(root, pages):
    """Run before navigation or source-inclusion transformations can hide errors."""
    records = {}
    for page in pages:
        text = page['text'].replace('<details>', '<details markdown="1">')
        soup = BeautifulSoup(markdown.markdown(text, extensions=['extra', 'md_in_html']), 'html.parser')
        refs = []
        for tag in soup.select('[href], img[src]'):
            raw = tag.get('href') or tag.get('src'); url = urlsplit(raw)
            if url.scheme or url.netloc or not url.path:
                continue
            path = root / unquote(url.path).lstrip('/') if url.path.startswith('/') else (root / page['src']).parent / unquote(url.path)
            path = path.resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                raise ValueError(f'Missing source reference: {page["src"]} -> {raw}')
            refs.append({'href': raw, 'source': path.relative_to(root.resolve()).as_posix()})
        records[page['src']] = refs
    return records


def validate(out, manifest):
    pages = manifest['pages']
    if not pages:
        raise ValueError('Empty expected page inventory')
    expected = {p['output'] for p in pages.values()} | {'gallery/index.html'} | set(manifest.get('resource_html', []))
    actual = {p.relative_to(out).as_posix() for p in out.rglob('*.html')}
    if actual != expected:
        raise ValueError(f'Page inventory mismatch: missing={expected-actual}, extra={actual-expected}')
    gallery = BeautifulSoup((out/'gallery/index.html').read_text(), 'html.parser')
    for source, item in pages.items():
        article = BeautifulSoup((out/item['output']).read_text(), 'html.parser').select_one('article.lesson-body')
        if article is None:
            raise ValueError(f'Missing article: {source}')
        visual = gallery if item['presentation'] == 'generated-overview' else article
        rendered = Counter(Path(img['src']).name for img in visual.select('img[src]') if '/assets/mermaid/' in img['src'])
        missing = Counter(item['mermaid']) - rendered
        if missing:
            raise ValueError(f'Missing displayed diagrams: {source}: {missing}')
        for asset in item['source_images']:
            if not (out/asset).is_file():
                raise ValueError(f'Missing source image: {source}: {asset}')
        if item['presentation'] != 'generated-overview':
            code = {p['data-source'] for p in article.select('figure.code-file[data-source]')}
            if code != set(item['code_inclusions']):
                raise ValueError(f'Code inclusion mismatch: {source}')
    for asset, digest in manifest['assets'].items():
        path = out/asset
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Missing or changed required asset: {asset}')
