"""Local mechanism demonstration for the-incident-you-caused-on-purpose. No AWS resources are created."""
times={'inject':0,'impact':5,'alert':60,'rollback':120,'recovered':210}
print({'detection_after_impact_s':times['alert']-times['impact'],'mitigation_after_alert_s':times['rollback']-times['alert'],'recovery_after_impact_s':times['recovered']-times['impact']})
print('Rollback is a milestone; backlog clear establishes recovery.')
