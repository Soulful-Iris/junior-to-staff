"""Local mechanism demonstration for ticket-inventory. No AWS resources are created."""
seat={'owner':None,'expires':0,'sold':False}
def hold(owner,now):
    if seat['sold'] or (seat['owner'] and now<seat['expires']): return '409 unavailable'
    seat.update(owner=owner,expires=now+300); return 'held'
def sell(owner,now):
    if seat['owner']!=owner or now>=seat['expires'] or seat['sold']: return '409 hold invalid'
    seat['sold']=True; return 'sold'
print('Ana',hold('ana',0)); print('Ben',hold('ben',1))
print('Ben after expiry',hold('ben',301)); print('Late Ana',sell('ana',302))
print('Ben',sell('ben',302))
