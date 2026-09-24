"""Local mechanism demonstration for erasure-workflow. No AWS resources are created."""
ledger={'ana':6}; records={'ana':{'version':5,'email':'ana@example.invalid'}}
def import_record(subject,version,payload):
    if version<=ledger.get(subject,-1): return 'rejected by deletion generation'
    records[subject]=payload; return 'imported'
records.pop('ana',None)
print(import_record('ana',4,{'email':'old backup copy'}))
print('Readable account:',records.get('ana','absent'))
print('Deletion evidence:',ledger)
