"""Local mechanism demonstration for a-shift-schedule. No AWS resources are created."""
shifts=[('ana',9,12)]; managers={'m1'}
def assign(actor,employee,start,end):
    if actor not in managers: return '403 revoked'
    if any(e==employee and start<b and a<end for e,a,b in shifts): return '409 overlapping shift'
    shifts.append((employee,start,end)); return 'saved'
print(assign('m1','ana',11,14)); print(assign('m1','ana',12,15))
managers.remove('m1'); print(assign('m1','ben',9,12))
