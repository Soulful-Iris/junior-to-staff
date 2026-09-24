"""Local mechanism demonstration for 05-the-failure-that-will-not-recover. No AWS resources are created."""
for backlog,arrivals,capacity in [(600,20,50),(600,60,50)]:
    net=capacity-arrivals
    print({'backlog':backlog,'net_drain_per_s':net,'ideal_drain_s':backlog/net if net>0 else 'never at these rates'})
