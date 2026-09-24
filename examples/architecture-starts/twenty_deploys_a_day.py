"""Local mechanism demonstration for twenty-deploys-a-day. No AWS resources are created."""
releases={'v1':{'reads':{'title','url'}},'v2':{'reads':{'title','url','tagObjects'}}}
record={'title':'Guide','url':'https://example.invalid','tagObjects':[]}
active='v2'; flag=False
print('Deployed:',active,'feature enabled:',flag)
active='v1'
print('Rolled back:',active,'can read required fields:',releases[active]['reads'].issubset(record))
del record['title']
print('After destructive schema change:',releases[active]['reads'].issubset(record))
