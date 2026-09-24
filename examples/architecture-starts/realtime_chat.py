"""Local mechanism demonstration for realtime-chat. No AWS resources are created."""
messages=[]; operations={}
def send(sender,key,text):
    identity=(sender,key)
    if identity in operations: return operations[identity]
    record={'sequence':len(messages)+1,'sender':sender,'text':text}
    messages.append(record); operations[identity]=record; return record
print(send('ana','phone-7','On my way'))
print(send('ana','phone-7','On my way'))
print('Reconnect after sequence 0:',[m for m in messages if m['sequence']>0])
