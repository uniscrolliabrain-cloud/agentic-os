import subprocess
import os

os.chdir('C:\\Users\\Alfonso\\Desktop\\git hub repos\\agentic-os')

print('=== BRANCH ===')
r = subprocess.run(['git','--no-pager','branch','--show-current'], capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())

print('\n=== STATUS ===')
r = subprocess.run(['git','--no-pager','status','--short'], capture_output=True, text=True)
print(r.stdout[:1000] if r.stdout else 'limpiio')

print('\n=== BRANCHES ===')
r = subprocess.run(['git','--no-pager','branch','-a'], capture_output=True, text=True)
print(r.stdout[:1000] if r.stdout else r.stderr[:500])
