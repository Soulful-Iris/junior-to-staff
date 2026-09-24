"""Local mechanism demonstration for the-flood. No AWS resources are created."""
queued=completed=rejected=0
for second in range(10):
    waiting=queued+100; done=min(20,waiting); completed+=done; waiting-=done
    rejected+=max(0,waiting-300); queued=min(300,waiting)
print({'offered':1000,'completed':completed,'queued':queued,'rejected':rejected})
