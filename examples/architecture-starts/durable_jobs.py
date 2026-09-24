"""Local mechanism demonstration for durable-jobs. No AWS resources are created."""
job={'epoch':4,'state':'running','result':None}; objects={}
def publish(epoch,key):
    if job['epoch']!=epoch or job['state']!='running': return 'stale publication rejected'
    job.update(state='succeeded',result=key); return 'published'
old_epoch=4
job['epoch']=5
objects['job7/5/result']='new worker bytes'
print(publish(5,'job7/5/result'))
objects['job7/4/result']='late old worker bytes'
print(publish(old_epoch,'job7/4/result'))
print('Visible result:',job['result'],objects[job['result']])
