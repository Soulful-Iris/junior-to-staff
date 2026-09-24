"""Local mechanism demonstration for metrics-platform. No AWS resources are created."""
buckets=[{'count':1,'sum':100},{'count':9,'sum':90}]
wrong=sum(b['sum']/b['count'] for b in buckets)/len(buckets)
correct=sum(b['sum'] for b in buckets)/sum(b['count'] for b in buckets)
print('Unweighted average of averages:',wrong)
print('Correct weighted average:',correct)
labels={'service':'checkout','request_id':'unique-123'}
print('Rejected labels:',sorted(set(labels)-{'service','region','status'}))
