"""Local mechanism demonstration for debuggable-at-three-in-the-morning. No AWS resources are created."""
impact=0; metric=30; alert=70; mitigation=130
print({'collection_s':metric-impact,'alert_delivery_and_evaluation_s':alert-metric,'detection_s':alert-impact,'mitigation_after_alert_s':mitigation-alert})
events=[{'request':'r7','job':'j9','attempt':None,'event':'accepted'},{'request':'r7','job':'j9','attempt':2,'event':'worker_timeout'}]
print('One user story:',events)
