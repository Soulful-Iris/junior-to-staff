"""Local mechanism demonstration for calendar-availability. No AWS resources are created."""
bookings=[]
def reserve(start,end):
    if end<=start: return '400 invalid interval'
    if any(start<b and a<end for a,b in bookings): return '409 room occupied'
    bookings.append((start,end)); return '201 reserved'
for interval in [(600,660),(630,690),(660,720)]:
    print(interval,reserve(*interval))
print('Minutes from midnight:',bookings)
