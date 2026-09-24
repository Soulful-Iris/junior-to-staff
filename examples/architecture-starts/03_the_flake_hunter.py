"""Local mechanism demonstration for 03-the-flake-hunter. No AWS resources are created."""
def run(order,isolated):
    shared=[]; outcomes=[]
    for action in order:
        store=[] if isolated else shared
        if action=='create': store.append('item7'); outcomes.append('created')
        else: outcomes.append('empty' if not store else 'unexpected leftover')
    return outcomes
for isolated in (False,True):
    print('isolated',isolated,run(['create','expect-empty'],isolated),run(['expect-empty','create'],isolated))
