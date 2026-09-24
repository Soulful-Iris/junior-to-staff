"""Local mechanism demonstration for video-streaming-platform. No AWS resources are created."""
session={'expected_parts':{1,2,3},'received':{1:'hash-a',3:'hash-c'}}
print('Resume missing parts:',sorted(session['expected_parts']-session['received'].keys()))
session['received'][2]='hash-b'
print('Upload complete:',session['expected_parts']==set(session['received']))
video={'ready':True,'private':True}; members={'ana'}
for viewer in ('ana','ben'):
    print(viewer,'manifest allowed' if video['ready'] and (not video['private'] or viewer in members) else '403')
