"""Local mechanism demonstration for a-shared-reading-list. No AWS resources are created."""
link={'version':3,'note':'Original'}; read_state={('ana','l7'):True,('ben','l7'):False}
def save(base,draft):
    if base!=link['version']: return {'state':'conflict','draft':draft,'server':dict(link)}
    link.update(version=base+1,note=draft); return {'state':'saved','server':dict(link)}
print(save(3,'Ana note')); print(save(3,'Ben draft')); print('Personal read state:',read_state)
