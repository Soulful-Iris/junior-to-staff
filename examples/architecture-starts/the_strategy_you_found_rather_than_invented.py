"""Local mechanism demonstration for the-strategy-you-found-rather-than-invented. No AWS resources are created."""
from collections import Counter
records=[('D1','transactions'),('D2','transactions'),('D3','transactions'),('D4','replay'),('D5','reporting')]
print('Constructed evidence:',records)
print('Shared requirements:',dict(Counter(kind for _,kind in records)))
print('Default: transactional store; exceptions: independently replayable events and isolated analytics.')
