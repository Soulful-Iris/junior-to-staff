"""Local mechanism demonstration for knowledge-assistant. No AWS resources are created."""
docs={'d1':{'text':'Expenses require a receipt.','allowed':True},'d2':{'text':'Secret acquisition plan','allowed':False}}
candidates=['d2','d1']; evidence=[(i,docs[i]['text']) for i in candidates if docs[i]['allowed']]
print('Authorized evidence:',evidence)
docs['d1']['allowed']=False
print('Final response:', 'withheld: access changed' if any(not docs[i]['allowed'] for i,_ in evidence) else evidence)
