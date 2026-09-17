import subprocess
import sys

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/connectors/test_google_adapters.py', '--tb=short', '-q'],
    capture_output=True,
    text=True,
    timeout=60
)
print("STDOUT:", result.stdout[-2000:])
print("STDERR:", result.stderr[-2000:])
print("RC:", result.returncode)