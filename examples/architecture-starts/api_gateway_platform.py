"""Local mechanism demonstration for api-gateway-platform. No AWS resources are created."""
active={'version':1,'routes':{'/orders':'orders-v1'}}
def activate(candidate):
    if not candidate.get('routes') or any(not p.startswith('/') for p in candidate['routes']): return 'rejected; keep version '+str(active['version'])
    active.clear(); active.update(candidate); return 'active version '+str(active['version'])
print(activate({'version':2,'routes':{'orders':'broken'}}))
print(activate({'version':3,'routes':{'/orders':'orders-v2'}}))
print(active)
