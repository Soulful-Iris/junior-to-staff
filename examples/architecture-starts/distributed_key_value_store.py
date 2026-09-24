"""Local mechanism demonstration for distributed-key-value-store. No AWS resources are created."""
import json,os,tempfile
with tempfile.TemporaryDirectory() as directory:
    path=directory+'/wal.jsonl'
    with open(path,'w') as log:
        log.write(json.dumps({'index':1,'term':3,'key':'a','value':'saved'})+'
')
        log.flush(); os.fsync(log.fileno())
    recovered={}
    with open(path) as log:
        for line in log:
            entry=json.loads(line); recovered[entry['key']]=entry['value']
    print('Recovered after closing the writer:',recovered)
print('Local WAL only: this is not a replicated consensus implementation.')
