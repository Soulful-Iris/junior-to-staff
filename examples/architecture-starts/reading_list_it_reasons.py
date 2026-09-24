"""Local mechanism demonstration for reading-list-it-reasons. No AWS resources are created."""
allowed={'databases','frontend','reliability'}
proposed=['databases','finance']; confirmed=[]
invalid=set(proposed)-allowed
print('Invalid suggestions:',sorted(invalid))
print('Confirmed before user action:',confirmed)
confirmed=['databases']
print('Explicit manual confirmation:',confirmed)
