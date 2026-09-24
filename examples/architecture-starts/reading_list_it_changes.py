"""Local mechanism demonstration for reading-list-it-changes. No AWS resources are created."""
target={'version':0,'tags':[],'deleted':False}
for version,tags,deleted in [(5,['tag-db'],False),(6,[],True),(4,['databases'],False)]:
    if version>target['version']:
        target.update(version=version,tags=tags,deleted=deleted); outcome='applied'
    else: outcome='ignored stale'
    print(version,outcome)
print('Final:',target)
