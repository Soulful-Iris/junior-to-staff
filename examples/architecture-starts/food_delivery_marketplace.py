"""Local mechanism demonstration for food-delivery-marketplace. No AWS resources are created."""
menu={'meal7':{'price':1250,'version':3,'available':True}}
cart={'meal7':{'price':1250,'version':3}}
menu['meal7'].update(price=1400,version=4)
def checkout(cart):
    for item,seen in cart.items():
        current=menu[item]
        if not current['available']: return '409 item unavailable'
        if seen['version']!=current['version']: return {'status':409,'new_price':current['price'],'needs_acceptance':True}
    return 'order accepted'
print(checkout(cart))
