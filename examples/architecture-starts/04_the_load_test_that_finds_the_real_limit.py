"""Local mechanism demonstration for 04-the-load-test-that-finds-the-real-limit. No AWS resources are created."""
queue=0; arrivals=completed=0
for second in range(10):
    arrivals+=120; queue+=120
    done=min(100,queue); queue-=done; completed+=done
print({'arrivals':arrivals,'completed':completed,'waiting':queue})
print('A closed-loop generator changes offered rate when responses slow.')
