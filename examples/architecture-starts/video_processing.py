"""Local mechanism demonstration for video-processing. No AWS resources are created."""
required={'360p','720p','1080p'}; outputs={}; published=None
def publish():
    global published
    if not required.issubset(outputs): return 'still processing: '+str(sorted(required-outputs.keys()))
    published=dict(outputs); return 'ready'
outputs.update({'360p':'g2/360.mp4','720p':'g2/720.mp4'})
print(publish()); outputs['1080p']='g2/1080.mp4'; print(publish()); print(published)
