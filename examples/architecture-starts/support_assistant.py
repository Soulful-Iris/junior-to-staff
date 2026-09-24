"""Local mechanism demonstration for support-assistant. No AWS resources are created."""
import hashlib,json
proposal={'type':'credit','ticket':'t7','amount_minor':500,'currency':'USD'}
def digest(p): return hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
approved=digest(proposal)
proposal['amount_minor']=5000
print('Execution allowed:',digest(proposal)==approved)
print('Changed parameters require a new approval.')
