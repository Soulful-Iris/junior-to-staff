"""Local mechanism demonstration for regional-failover. No AWS resources are created."""
authority={'epoch':7,'region':'east'}; orders=[]
def commit(region,epoch,order):
    if (region,epoch)!=(authority['region'],authority['epoch']): return 'fenced'
    orders.append(order); return 'committed'
print(commit('east',7,'order-1'))
authority.update(epoch=8,region='west')
print(commit('east',7,'late-order'))
print(commit('west',8,'order-2'))
print(orders)
