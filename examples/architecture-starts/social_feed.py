"""Local mechanism demonstration for social-feed. No AWS resources are created."""
posts={'p1':{'text':'Team update','public':True},'p2':{'text':'Old private draft','public':False}}
feed=['p2','p1']; deleted={'p3'}
def visible(ids):
    return [posts[i]['text'] for i in ids if i not in deleted and i in posts and posts[i]['public']]
print('Warm feed candidates:',feed); print('Returned content:',visible(feed))
posts['p1']['public']=False
print('After revocation:',visible(feed))
