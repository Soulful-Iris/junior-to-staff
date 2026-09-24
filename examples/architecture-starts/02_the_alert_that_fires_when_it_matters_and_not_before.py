"""Local mechanism demonstration for 02-the-alert-that-fires-when-it-matters-and-not-before. No AWS resources are created."""
opened=False
for short,long in [(False,False),(True,False),(True,True),(False,True),(False,False)]:
    alarm=short and long
    if alarm: opened=True
    print({'short':short,'long':long,'alarm':alarm,'incident_open':opened})
acknowledged=True
if acknowledged and not short and not long: opened=False
print('After acknowledged recovery:',opened)
