"""Local mechanism demonstration for checkout-payment. No AWS resources are created."""
# A tiny provider fixture models a charge whose response was lost.
provider={}; order={'id':'order-7','state':'pending'}
key='payment:order-7:v1'
def charge(k):
    if k not in provider: provider[k]={'charge_id':'charge-91','amount_minor':1999}
    return provider[k]
charge(key)  # provider committed; simulate losing the response
order['state']='payment_unknown'
print('After timeout:',order)
evidence=charge(key)  # the SAME provider key resolves the same charge
order.update(state='paid',charge_id=evidence['charge_id'])
print('After reconciliation:',order,'provider charge count:',len(provider))
