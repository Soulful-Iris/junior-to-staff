"""Local mechanism demonstration for file-synchronization. No AWS resources are created."""
file={'version':3,'manifest':'hash-original','deleted':False}
def publish(base,manifest):
    if base!=file['version']: return {'status':409,'keep_local':manifest,'server':dict(file)}
    file.update(version=base+1,manifest=manifest); return dict(file)
print(publish(3,'hash-ana'))
print(publish(3,'hash-ben'))
file.update(version=5,deleted=True,manifest=None)
print(publish(3,'hash-old-laptop'))
