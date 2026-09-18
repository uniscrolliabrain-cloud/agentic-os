"""Invariante estructural: el kernel NO importa nada fuera del kernel.

AUD-01: los imports relativos (`from ...infrastructure.tenancy import X`)
tienen `node.level > 0` y `node.module` NO empieza por `agentic_os.*`. Un test
que solo mira `node.module` es ciego a esta evasion. Este test resuelve el
modulo absoluto desde (level, module, path) antes de comprobar la lista de
prohibidos.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
KERNEL = REPO / "src" / "agentic_os" / "kernel"
SRC = REPO / "src"

FORBIDDEN = (
    "agentic_os.domains",
    "agentic_os.orchestration",
    "agentic_os.cognition",
    "agentic_os.interfaces",
    "agentic_os.connectors",
    "agentic_os.execution",
    "agentic_os.infrastructure",
    "agentic_os.agents",
    "agentic_os.contracts",
)

FORBIDDEN_RELATIVE = (
    "domains",
    "orchestration",
    "cognition",
    "interfaces",
    "connectors",
    "execution",
    "infrastructure",
    "agents",
    "contracts",
)


def _all_kernel_py() -> list[pathlib.Path]:
    return sorted(KERNEL.rglob("*.py"))


def _resolve_relative(py: pathlib.Path, module: str, level: int) -> str:
    if level <= 0:
        return module
    parts = list(py.relative_to(SRC / "agentic_os").parts[:-1])
    up = level - 1
    base = parts[: len(parts) - up] if up else parts
    if module:
        base = base + module.split(".")
    return "agentic_os." + ".".join(base) if base else "agentic_os"


@pytest.mark.parametrize("py", _all_kernel_py(), ids=lambda p: p.name)
def test_kernel_file_does_not_import_outside(py: pathlib.Path) -> None:
    tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0:
                mod = node.module or ""
                for prefix in FORBIDDEN:
                    assert not mod.startswith(prefix), (
                        f"{py.relative_to(REPO)} importa '{mod}' "
                        f"(absoluto, prohibido: {prefix})"
                    )
            else:
                abs_mod = _resolve_relative(py, node.module or "", node.level)
                for prefix in FORBIDDEN:
                    assert not abs_mod.startswith(prefix), (
                        f"{py.relative_to(REPO)} importa '{abs_mod}' "
                        f"(relativo level={node.level}, prohibido: {prefix})"
                    )
                if node.module:
                    first = node.module.split(".")[0]
                    assert first not in FORBIDDEN_RELATIVE, (
                        f"{py.relative_to(REPO)} importa '{first}.*' "
                        f"(relativo level={node.level}, prohibido)"
                    )
        elif isinstance(node, ast.Import):
            for name in node.names:
                for prefix in FORBIDDEN:
                    assert not name.name.startswith(prefix), (
                        f"{py.relative_to(REPO)} importa '{name.name}'"
                    )