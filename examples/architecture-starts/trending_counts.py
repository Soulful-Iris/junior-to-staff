"""Local mechanism demonstration for trending-counts. No AWS resources are created."""
import hashlib
seen=set(); partials={}
for eid,topic in [('e1','goal'),('e2','goal'),('e1','goal'),('e3','save')]:
    if eid in seen: continue
    seen.add(eid); shard=int(hashlib.sha256(eid.encode()).hexdigest(),16)%4
    key=(topic,shard); partials[key]=partials.get(key,0)+1
totals={}
for (topic,shard),count in partials.items(): totals[topic]=totals.get(topic,0)+count
print('Partials:',partials); print('Ranking:',sorted(totals.items(),key=lambda x:(-x[1],x[0])))
