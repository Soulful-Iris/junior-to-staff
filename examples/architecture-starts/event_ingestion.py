"""Local mechanism demonstration for event-ingestion. No AWS resources are created."""
events=[{'id':'e1','version':1,'value':7},{'id':'e1','version':1,'value':7},{'id':'e2','version':99,'value':8}]
seen=set(); output=[]; quarantine=[]
for event in events:
    if event['version']!=1: quarantine.append((event,'unsupported schema')); continue
    if event['id'] in seen: continue
    output.append(event['value']); seen.add(event['id'])
print('Applied:',output,'quarantine:',quarantine)
