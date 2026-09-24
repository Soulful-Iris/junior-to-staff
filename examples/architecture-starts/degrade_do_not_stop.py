"""Local mechanism demonstration for degrade-do-not-stop. No AWS resources are created."""
rows=[{'owner':'ana','url':'https://example.invalid/a','title':'Old title','age':120},{'owner':'ben','url':'https://private.invalid','title':'Private','age':1}]
result=[]
for row in rows:
    if row['owner']!='ana': continue
    result.append({'url':row['url'],'title':row['title'] if row['age']<=3600 else None,'title_status':'stale'})
print('Provider unavailable; return local list:',result)
