"""Local mechanism demonstration for personalized-ranking. No AWS resources are created."""
candidates=[{'id':'a','score':9,'eligible':False},{'id':'b','score':5,'eligible':True},{'id':'c','score':3,'eligible':True}]
feature_elapsed_ms=170; remaining_ms=250-feature_elapsed_ms
mode='fallback' if remaining_ms<80+20+30 else 'personalized'
ranked=sorted(candidates,key=lambda x:-x['score'])
print('Mode:',mode,'remaining budget:',remaining_ms)
print('Returned:',[x['id'] for x in ranked if x['eligible']])
