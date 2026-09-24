"""Local mechanism demonstration for webhook-delivery. No AWS resources are created."""
import hmac,hashlib,json
body=json.dumps({'id':'evt-7','type':'order.paid'},separators=(',',':')).encode()
secret=b'local-fixture-secret'; timestamp='1700000000'
signature=hmac.new(secret,timestamp.encode()+b'.'+body,hashlib.sha256).hexdigest()
print('Signed bytes:',body.decode()); print('Signature:',signature)
seen=set()
for attempt in (1,2):
    event=json.loads(body)['id']; duplicate=event in seen; seen.add(event)
    print('attempt',attempt,'already handled' if duplicate else 'apply event')
