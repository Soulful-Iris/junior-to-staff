"""Local mechanism demonstration for 05-the-job-that-survives-a-restart. No AWS resources are created."""
job={'epoch':1,'state':'running','title':None}
def finish(epoch,title):
    if job['epoch']!=epoch or job['state']!='running': return 'stale worker rejected'
    job.update(state='succeeded',title=title); return 'saved'
old=job['epoch']; job['epoch']=2
print(finish(2,'Current title')); print(finish(old,'Late old title')); print(job)
