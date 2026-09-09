import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "--tb=short", "-q"],
    capture_output=True,
    text=True,
    cwd=r"C:\Users\Alfonso\Desktop\git hub repos\agentic-os"
)

with open("_full2.txt", "w", encoding="utf-8") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\nReturn code: {result.returncode}\n")

print("Done. Check _full2.txt")
