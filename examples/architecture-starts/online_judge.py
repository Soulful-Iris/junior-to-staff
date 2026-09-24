"""Local mechanism demonstration for online-judge. No AWS resources are created."""
import subprocess,sys
program="while True: pass"
try:
    subprocess.run([sys.executable,'-c',program],timeout=0.2,capture_output=True)
except subprocess.TimeoutExpired:
    print('wall-clock limit exceeded; child terminated')
print('This subprocess example is NOT a security sandbox.')
