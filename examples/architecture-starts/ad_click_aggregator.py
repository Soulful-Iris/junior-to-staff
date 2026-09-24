"""Local mechanism demonstration for ad-click-aggregator. No AWS resources are created."""
seen=set(); windows={}; watermark=120; lateness=120
for eid,campaign,at in [('e1','c7',61),('e1','c7',61),('e2','c7',10),('e3','c7',-180)]:
    if eid in seen: print(eid,'duplicate'); continue
    if at<watermark-lateness: print(eid,'too late: reconciliation path'); continue
    seen.add(eid); key=(campaign,(at//60)*60); windows[key]=windows.get(key,0)+1
print('Provisional counts:',windows)
