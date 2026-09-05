import subprocess
import sys

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/connectors/', '-v', '--tb=short'],
    capture_output=True,
    text=True,
    timeout=90
)
with open('test_conn_result.txt', 'w', encoding='utf-8') as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
    f.write("\nRC: ")
    f.write(str(result.returncode))
print("Done, RC:", result.returncode)