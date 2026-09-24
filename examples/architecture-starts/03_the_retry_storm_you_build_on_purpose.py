"""Local mechanism demonstration for 03-the-retry-storm-you-build-on-purpose. No AWS resources are created."""
for attempts in (3,4): print(attempts,'total attempts per layer ->',attempts**3,'dependency attempts')
remaining_ms=500; retry_after_ms=2000
print('Start another attempt:',retry_after_ms<remaining_ms)
import random
rng=random.Random(7)
print('Bounded jitter delays ms:',[round(rng.uniform(0,400)) for _ in range(5)])
