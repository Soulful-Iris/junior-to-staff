"""Local mechanism demonstration for 02-the-three-second-budget. No AWS resources are created."""
budget=3000; spent=300; reserve=100
for attempt in (1,2):
    remaining=budget-spent-reserve
    timeout=min(1200,remaining)
    if timeout<=0: print('no budget for attempt',attempt); break
    print('attempt',attempt,'timeout',timeout,'ms')
    spent+=timeout
    if attempt==1: spent+=200
print('elapsed with response reserve:',spent+reserve,'ms')
