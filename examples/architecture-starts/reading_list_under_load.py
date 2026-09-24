"""Local mechanism demonstration for reading-list-under-load. No AWS resources are created."""
job={'epoch':2,'state':'succeeded','title':'New title'}
def late_publish(epoch,title):
    if job['epoch']!=epoch or job['state']!='running': return 'rejected stale attempt'
    job['title']=title; return 'published'
print(late_publish(1,'Old title'),job)
print('Offered 200/s, origin budget 100/s: at least 100/s need cache, bounded stale data, or rejection.')
print('Ten local coalescers can still produce ten origin fills for one hot miss.')
