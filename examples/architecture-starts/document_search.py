"""Local mechanism demonstration for document-search. No AWS resources are created."""
index=[{'id':'public','score':9},{'id':'secret','score':10}]
content={'public':'Engineering handbook','secret':'Private acquisition plan'}
allowed={'public'}
results=[]
for hit in sorted(index,key=lambda h:-h['score']):
    if hit['id'] not in allowed: continue
    results.append({'id':hit['id'],'snippet':content[hit['id']]})
print(results)
