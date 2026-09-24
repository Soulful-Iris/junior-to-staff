"""Local mechanism demonstration for multi-tenant-migration. No AWS resources are created."""
target={}
def apply(key,version,value):
    old=target.get(key)
    if old and old['version']>=version: return 'ignored stale/duplicate'
    target[key]={'version':version,'value':value}; return 'applied'
for v,value in [(5,'live edit'),(6,None),(4,'old backfill')]:
    print(v,apply('acme:7',v,value))
print('Target:',target,'visible:',target['acme:7']['value'])
