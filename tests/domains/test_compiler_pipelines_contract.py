"""Contrato Pydantic de los pipelines del tenant agentic-compiler."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.domains.compiler import PIPELINES, CompilerPipeline, CompilerStep


def test_los_dos_pipelines_existen():
    assert set(PIPELINES) == {"blueprint_from_idea", "compile_tenant"}


def test_gates_correctos():
    assert PIPELINES["blueprint_from_idea"].requires_gate == "gate_1"
    assert PIPELINES["compile_tenant"].requires_gate == "gate_2"


def test_modes_correctos():
    assert PIPELINES["blueprint_from_idea"].mode == "plan"
    assert PIPELINES["compile_tenant"].mode == "act"


def test_estan_deshabilitados_hasta_implementar():
    for pipeline in PIPELINES.values():
        assert pipeline.enabled is False


def test_step_sin_tool_falla():
    with pytest.raises(ValidationError):
        CompilerStep(tool="")


def test_pipeline_sin_steps_falla():
    with pytest.raises(ValidationError):
        CompilerPipeline(id="x", name="X", steps=[])