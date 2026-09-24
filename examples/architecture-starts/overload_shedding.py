"""Local mechanism demonstration for overload-shedding. No AWS resources are created."""
arrival=40000; service=20000; limit=100000; queued=0
for second in range(1,8):
    offered=queued+arrival; completed=min(service,offered)
    waiting=offered-completed; rejected=max(0,waiting-limit); queued=min(waiting,limit)
    print(second,'completed',completed,'queued',queued,'rejected',rejected)
