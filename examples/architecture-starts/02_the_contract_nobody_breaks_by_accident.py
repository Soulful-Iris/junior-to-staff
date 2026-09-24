"""Local mechanism demonstration for 02-the-contract-nobody-breaks-by-accident. No AWS resources are created."""
def decode(body):
    duration=body.get('durationMs')
    if not isinstance(body.get('title'),str): return 'invalid title'
    if isinstance(duration,bool) or not isinstance(duration,(int,float)) or duration<0: return 'invalid durationMs'
    return 'shape accepted; unit meaning still requires the contract'
for body in [{'title':'Guide','durationMs':12},{'title':'Guide','durationMs':'12'}]: print(body,decode(body))
