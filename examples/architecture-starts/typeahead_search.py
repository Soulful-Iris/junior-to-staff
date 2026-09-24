"""Local mechanism demonstration for typeahead-search. No AWS resources are created."""
latest={'generation':2,'query':'iph'}
responses=[{'generation':2,'query':'iph','items':['iphone']},{'generation':1,'query':'ipa','items':['ipad']}]
for response in responses:
    print('display' if response['generation']==latest['generation'] else 'ignore stale',response['items'])
index={'iph':['iphone','iphone case','iphone charger']}
print('Suggestions:',index.get('iph',[])[:5])
