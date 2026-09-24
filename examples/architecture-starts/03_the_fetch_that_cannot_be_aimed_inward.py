"""Local mechanism demonstration for 03-the-fetch-that-cannot-be-aimed-inward. No AWS resources are created."""
import ipaddress
from urllib.parse import urlsplit
def permitted(url,resolved):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or p.username or p.password or p.port not in (None,80,443): return False
    return bool(resolved) and all(ipaddress.ip_address(a).is_global for a in resolved)
for url,addresses in [('https://example.com',['93.184.216.34']),('http://metadata.invalid',['169.254.169.254']),('https://mixed.invalid',['93.184.216.34','127.0.0.1'])]:
    print(url,permitted(url,addresses))
print('Policy demonstration only; the network adapter must pin the validated IP.')
