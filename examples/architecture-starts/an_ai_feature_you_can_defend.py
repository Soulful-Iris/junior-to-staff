"""Local mechanism demonstration for an-ai-feature-you-can-defend. No AWS resources are created."""
human=['pass']*99+['fail']; judge=['pass']*100
agreement=sum(a==b for a,b in zip(human,judge))/len(human)
failures=[i for i,x in enumerate(human) if x=='fail']
recall=sum(judge[i]=='fail' for i in failures)/len(failures)
print({'agreement':agreement,'failure_recall':recall})
