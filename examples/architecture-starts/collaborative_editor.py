"""Local mechanism demonstration for collaborative-editor. No AWS resources are created."""
doc={'revision':12,'text':'Incident draft'}; accepted={}
def edit(op,base,text):
    if op in accepted: return accepted[op]
    if base!=doc['revision']: return {'status':409,'server_revision':doc['revision'],'keep_draft':text}
    doc.update(revision=base+1,text=text); accepted[op]=dict(doc); return accepted[op]
print(edit('ana-1',12,'Ana update'))
print(edit('ben-1',12,'Ben offline draft'))
print(edit('ana-1',12,'Ana update'))
