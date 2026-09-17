"""Invariante estructural: el kernel NO importa nada fuera del kernel."""
from __future__ import annotations

import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
KERNEL = REPO / "src" / "agentic_os" / "kernel"

FORBIDDEN = (
    "agentic_os.domains",
    "agentic_os.orchestration",
    "agentic_os.cognition",
    "agentic_os.interfaces",
    "agentic_os.connectors",
    "agentic_os.execution",
    "agentic_os.infrastructure",
    "agentic_os.agents",
)


def _all_kernel_py():
    return sorted(KERNEL.rglob("*.py"))


@pytest.mark.parametrize("py", _all_kernel_py(), ids=lambda p: p.name)
def test_kernel_file_does_not_import_outside(py):
    tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for prefix in FORBIDDEN:
                assert not mod.startswith(prefix), (
                    f"{py.relative_to(REPO)} importa '{mod}' (prohibido: {prefix})"
                )
        elif isinstance(node, ast.Import):
            for name in node.names:
                for prefix in FORBIDDEN:
                    assert not name.name.startswith(prefix), (
                        f"{py.relative_to(REPO)} importa '{name.name}'"
                    )