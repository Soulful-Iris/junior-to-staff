"""Local mechanism demonstration for the-paved-road. No AWS resources are created."""
import json
def template(name,retention_days=14):
    if retention_days not in (14,30): raise ValueError('choose a documented policy or record an exception')
    return {'Resources':{'Logs':{'Type':'AWS::Logs::LogGroup','Properties':{'LogGroupName':'/exercise/'+name,'RetentionInDays':retention_days}}}}
print(json.dumps(template('bookmarks'),indent=2))
print('Approved alternative:',template('archive-reader',30)['Resources']['Logs']['Properties'])
actual={'RetentionInDays':None}; print('Existing resource needs review:',actual['RetentionInDays'] not in (14,30))
