"""Local mechanism demonstration for notification-platform. No AWS resources are created."""
preferences={'ana':True}; intents={}; attempts=[]
def queue(event,user): intents.setdefault((event,user),{'state':'queued'})
def deliver(event,user):
    intent=intents[(event,user)]
    if not preferences.get(user,False): intent['state']='suppressed'; return
    if intent['state']=='provider_accepted': return
    attempts.append((event,user)); intent['state']='provider_accepted'
queue('campaign-7','ana'); queue('campaign-7','ana')
preferences['ana']=False; deliver('campaign-7','ana')
print(intents,'provider attempts:',attempts)
