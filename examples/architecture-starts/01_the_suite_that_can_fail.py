"""Local mechanism demonstration for 01-the-suite-that-can-fail. No AWS resources are created."""
records=[('owner filter','semantic','detected'),('expiry boundary','semantic','survived'),('comment','equivalent','excluded'),('local rename','equivalent','excluded')]
relevant=[r for r in records if r[1]=='semantic']
print('Selected semantic defects:',len(relevant))
print('Detected:',sum(r[2]=='detected' for r in relevant))
print('Needs investigation:',[r[0] for r in relevant if r[2]=='survived'])
