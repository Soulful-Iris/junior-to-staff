"""Local mechanism demonstration for 05-the-test-that-runs-in-production-forever. No AWS resources are created."""
steps={'create':'failed','read':'skipped','delete':'cleanup_attempted','verify_absent':'unknown'}
required=('create','read','delete','verify_absent')
print('Journey successful:',all(steps[s]=='passed' for s in required))
print('Step evidence:',steps)
last_completed=0; now=181; interval=60
print('Runner stale:',now-last_completed>3*interval)
