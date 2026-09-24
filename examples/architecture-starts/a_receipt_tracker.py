"""Local mechanism demonstration for a-receipt-tracker. No AWS resources are created."""
from decimal import Decimal
receipt={'suggested_minor':19990,'confirmed_minor':None,'revision':1}
confirmed=int(Decimal('19.99')*100)
receipt.update(confirmed_minor=confirmed,revision=2)
receipt['suggested_minor']=19990
print('Machine suggestion:',receipt['suggested_minor'])
print('Report amount:',receipt['confirmed_minor'],'minor units; revision',receipt['revision'])
