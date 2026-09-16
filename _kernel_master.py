"""Corre tests kernel ontology en MAIN repo (master) -> _kernel_master.txt."""
from __future__ import annotations

import subprocess

MAIN = r"C:\Users\Alfonso\Desktop\git hub repos\agentic-os"
PY = MAIN + r"\.venv\Scripts\python.exe"

targets = [
    "tests/kernel/test_ontology_contracts.py",
    "tests/kernel/test_ontology_bundle.py",
    "tests/kernel/test_ontology_typed.py",
]
out = []
for t in targets:
    r = subprocess.run(
        [PY, "-m", "pytest", t, "-q", "--tb=line"],
        cwd=MAIN,
        capture_output=True,
        text=True,
    )
    out.append(f"===== MASTER {t} (exit={r.returncode}) =====")
    out.append((r.stdout + r.stderr).strip()[-2000:])
    out.append("")

with open(MAIN + r"\_kernel_master.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")
