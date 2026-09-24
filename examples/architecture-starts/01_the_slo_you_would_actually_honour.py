"""Local mechanism demonstration for 01-the-slo-you-would-actually-honour. No AWS resources are created."""
def report(total,failures,target=.999):
    if total==0: return {'state':'no eligible traffic'}
    allowed=total*(1-target)
    return {'success':(total-failures)/total,'allowed_failures':round(allowed,6),'budget_used':round(failures/allowed,3)}
print(report(1000000,10000)); print(report(1000,1)); print(report(0,0))
