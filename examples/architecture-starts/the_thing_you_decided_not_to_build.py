"""Local mechanism demonstration for the-thing-you-decided-not-to-build. No AWS resources are created."""
custom=6*5+12*1; script=3+12*.25; exports=2*12
print({'custom_engineer_days_year':custom,'script_engineer_days_year':script,'exports_year':exports})
print('Decision candidate: use the bounded script; revisit if demand or guarantees change.')
