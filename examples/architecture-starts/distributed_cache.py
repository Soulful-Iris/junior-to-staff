"""Local mechanism demonstration for distributed-cache. No AWS resources are created."""
cache={'item7':{'version':5,'value':'new price'}}
def fill(key,version,value):
    current=cache.get(key)
    if current and current['version']>version: return 'stale fill rejected'
    cache[key]={'version':version,'value':value}; return 'filled'
print(fill('item7',4,'old price')); print(cache)
requests=1000; per_process_coalesced=1; processes=10
print('One hot miss:',requests,'requests can still cause',processes*per_process_coalesced,'origin reads across processes')
