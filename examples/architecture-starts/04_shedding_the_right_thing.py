"""Local mechanism demonstration for 04-shedding-the-right-thing. No AWS resources are created."""
def allocate(critical,bulk,capacity):
    c=min(critical,capacity); b=min(bulk,max(0,capacity-c))
    return {'critical_admitted':c,'bulk_admitted':b,'critical_rejected':critical-c,'bulk_rejected':bulk-b}
print(allocate(80,50,100)); print(allocate(120,0,100))
print('100 save-units can fund',100//100,'export or',100,'saves')
