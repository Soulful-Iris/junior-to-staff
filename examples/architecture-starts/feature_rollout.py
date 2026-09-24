"""Local mechanism demonstration for feature-rollout. No AWS resources are created."""
import hashlib
def exposed(subject,percent):
    bucket=int(hashlib.sha256(('invoice-v1:'+subject).encode()).hexdigest(),16)%10000
    return bucket<percent*100
users=[f'user-{i}' for i in range(200)]
users=[u for u in users if exposed(u,5)][:2]+[u for u in users if exposed(u,25) and not exposed(u,5)][:2]
for user in users:
    print(user,'5%',exposed(user,5),'25%',exposed(user,25),'repeat',exposed(user,5))
print('Emergency off:',[exposed(u,0) for u in ['ana','ben','chen']])
