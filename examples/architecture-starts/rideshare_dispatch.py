"""Local mechanism demonstration for rideshare-dispatch. No AWS resources are created."""
rides={'r1':None,'r2':None}; drivers={'d7':None}
def accept(ride,driver):
    if rides[ride] is not None or drivers[driver] is not None: return '409 already assigned'
    rides[ride]=driver; drivers[driver]=ride; return 'assignment committed'
print(accept('r1','d7')); print(accept('r2','d7')); print(rides,drivers)
latest={'seq':9,'cell':'north'}
for seq,cell in [(8,'south'),(10,'east')]:
    if seq>latest['seq']: latest.update(seq=seq,cell=cell)
print('Latest location:',latest)
