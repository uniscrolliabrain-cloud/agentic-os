import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/orchestration/test_audit_fail_closed.py', '--timeout=30', '--tb=short', '-v'], capture_output=True, text=True)
with open('_test_094.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/orchestration/test_audit_fail_closed.py::test_eventlog_ok_ejecucion_normal', '--tb=short', '-v', '-p', 'no:timeout'], capture_output=True, text=True)
with open('_test_094.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/orchestration/test_audit_fail_closed.py::test_eventlog_ok_ejecucion_normal', '--timeout=30', '--tb=short', '-v'], capture_output=True, text=True)
with open('_test_094.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/orchestration/test_audit_fail_closed.py', '--timeout=30', '--tb=short', '-v', '-x'], capture_output=True, text=True)
with open('_test_094.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/orchestration/test_audit_fail_closed.py', '--timeout=60', '--tb=short', '-v'], capture_output=True, text=True)
with open('_test_094.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/kernel/', 'tests/orchestration/', 'tests/connectors/', 'tests/security/', 'tests/automation/', 'tests/infrastructure/', 'tests/interfaces/', 'tests/bugs/', '--timeout=60', '--tb=short', '-v'], capture_output=True, text=True)
with open('_alltests_verbose.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/kernel/', 'tests/orchestration/', 'tests/connectors/', 'tests/security/', 'tests/automation/', 'tests/infrastructure/', 'tests/interfaces/', 'tests/bugs/', 'tests/execution/', '--timeout=60', '--tb=short', '-v'], capture_output=True, text=True)
with open('_alltests_verbose.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/kernel/', 'tests/orchestration/', 'tests/connectors/', 'tests/security/', 'tests/automation/', 'tests/infrastructure/', 'tests/interfaces/', 'tests/bugs/', 'tests/execution/', '--timeout=30', '--tb=no', '-q'], capture_output=True, text=True)
with open('_alltests.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
# Get list of test directories
test_dirs = [d for d in os.listdir('tests') if os.path.isdir(os.path.join('tests', d))]
print('Test directories:', test_dirs)
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '--timeout=30', '--tb=no', '-q'], capture_output=True, text=True)
with open('_alltests.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/kernel/', 'tests/orchestration/', 'tests/connectors/', 'tests/security/', 'tests/automation/', 'tests/infrastructure/', 'tests/interfaces/', 'tests/bugs/', 'tests/cognition/', 'tests/execution/', '--timeout=30', '--tb=no', '-q'], capture_output=True, text=True)
with open('_alltests.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '--timeout=30', '--tb=no', '-q', '-x'], capture_output=True, text=True)
with open('_pytest_result.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys, os
os.chdir(r'c:\Users\Alfonso\Desktop\git hub repos\agentic-os')
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '--timeout=60', '--tb=no', '-q'], capture_output=True, text=True)
with open('_pytest_result.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')

import subprocess, sys
r = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '--timeout=60', '--tb=no', '-q'], capture_output=True, text=True)
with open('_pytest_result.txt', 'w') as f:
    f.write('STDOUT:\n' + r.stdout + '\nSTDERR:\n' + r.stderr + '\nRC: ' + str(r.returncode))
print('done')
