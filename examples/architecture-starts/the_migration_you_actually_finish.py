"""Local mechanism demonstration for the-migration-you-actually-finish. No AWS resources are created."""
target={}
def apply(version,tags,deleted=False):
    if target and version<=target['version']: return 'ignored stale'
    target.update(version=version,tags=tags,deleted=deleted); return 'applied'
for v,tags,deleted in [(5,['tag-db'],False),(6,[],True),(4,['old-text'],False)]:
    print(v,apply(v,tags,deleted))
print('Final target:',target)
