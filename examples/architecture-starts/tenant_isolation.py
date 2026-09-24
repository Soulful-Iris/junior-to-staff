"""Local mechanism demonstration for tenant-isolation. No AWS resources are created."""
reports={('acme','r1'):'Acme revenue',('birch','r2'):'Birch payroll'}
members={('ana','acme')}; cache={('acme','r1'):'Acme revenue'}
def read(user,tenant,rid):
    if (user,tenant) not in members: return '403 membership revoked'
    return cache.get((tenant,rid),reports.get((tenant,rid),'404 scoped resource'))
print(read('ana','acme','r2'))
print(read('ana','acme','r1'))
members.remove(('ana','acme'))
print(read('ana','acme','r1'))
