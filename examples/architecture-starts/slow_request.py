"""Local mechanism demonstration for slow-request. No AWS resources are created."""
import math
samples=[80]*96+[1900]*4
samples.sort()
for percentile in (50,95,99):
    value=samples[math.ceil(percentile/100*len(samples))-1]
    print('p'+str(percentile),value,'ms')
trace={'pool_wait_ms':1700,'query_ms':40,'application_ms':160}
print('Slow request phases:',trace,'total',sum(trace.values()),'ms')
