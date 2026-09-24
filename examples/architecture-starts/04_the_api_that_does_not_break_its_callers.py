"""Local mechanism demonstration for 04-the-api-that-does-not-break-its-callers. No AWS resources are created."""
tags=[{'id':'t7','label':'databases','color':'blue'}]
def response():
    return {'tags':[t['label'] for t in tags],'tagObjects':[dict(t) for t in tags]}
body=response(); print(body)
print('Old client:',', '.join(body['tags']))
print('New client:',body['tagObjects'][0]['id'])
