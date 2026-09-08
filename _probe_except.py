"""Probe: localiza `except ...: pass` y `except Exception:` que silencian."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(r"c:\Users\Alfonso\Desktop\git hub repos\agentic-os\src")


def main() -> None:
    hits = []
    for py in sorted(ROOT.rglob("*.py")):
        lines = py.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("except"):
                continue
            # Mirar siguiente línea no vacía
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip() == "pass":
                hits.append((str(py.relative_to(ROOT)), i + 1, stripped))
    print(f"HITS except+pass: {len(hits)}")
    for h in hits:
        print(f"  {h[0]}:{h[1]}  -> {h[2]}")
    print("--- FIN ---")


if __name__ == "__main__":
    main()