"""Local mechanism demonstration for feature-rollout. No AWS resources are created."""
import hashlib
def exposed(subject,percent):
    bucket=int(hashlib.sha256(('invoice-v1:'+subject).encode()).hexdigest(),16)%10000
    return bucket<percent*100
for user in ['ana','ben','chen']:
    print(user,'5%',exposed(user,5),'25%',exposed(user,25),'repeat',exposed(user,5))
print('Emergency off:',[exposed(u,0) for u in ['ana','ben','chen']])
