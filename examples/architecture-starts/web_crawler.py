"""Local mechanism demonstration for web-crawler. No AWS resources are created."""
from urllib.parse import urlsplit,urlunsplit
seen=set()
def normalize(url):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or p.username or p.password: raise ValueError('unsupported URL')
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',p.query,''))
for url in ['https://EXAMPLE.invalid/a#one','https://example.invalid/a#two','https://example.invalid/a?sort=1']:
    key=normalize(url); print(key,'duplicate' if key in seen else 'new'); seen.add(key)
print('Normalization only; network destination validation is a separate required boundary.')
