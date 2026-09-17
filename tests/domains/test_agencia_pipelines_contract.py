"""Contrato Pydantic de los pipelines del tenant bor-agencia."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.domains.agencia import PIPELINES, AgencyPipeline, PipelineStep


def test_los_tres_pipelines_existen():
    assert set(PIPELINES) == {"leads_to_draft", "inbox_watcher", "daily_social"}


def test_pipelines_son_inmutables():
    p = PIPELINES["leads_to_draft"]
    with pytest.raises(ValidationError):
        p.id = "otro"  # type: ignore[misc]


def test_pipeline_rechaza_extra_fields():
    with pytest.raises(ValidationError):
        AgencyPipeline(
            id="x", name="X",
            steps=[PipelineStep(tool="drive_list_files")],
            campo_inventado="boom",  # type: ignore[call-arg]
        )


def test_pipeline_sin_steps_falla():
    with pytest.raises(ValidationError):
        AgencyPipeline(id="x", name="X", steps=[])


def test_step_sin_tool_falla():
    with pytest.raises(ValidationError):
        PipelineStep(tool="   ")


def test_daily_social_requires_approval():
    assert PIPELINES["daily_social"].requires_approval is True


def test_todos_los_steps_apuntan_a_tools_no_vacias():
    for pipeline in PIPELINES.values():
        for step in pipeline.steps:
            assert step.tool.strip()