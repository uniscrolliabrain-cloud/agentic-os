"""El PipelineRunner despacha por (tenant, pipeline_id) via DomainRegistry."""
from __future__ import annotations

import pytest

from agentic_os.orchestration.pipelines.runner import (
    PipelineRunner,
    PipelineStepError,
    UnknownPipelineError,
    get_tenant_handlers,
    get_tenant_pipelines,
    list_registered_tenants,
)


class _StubExecutor:
    """Executor minimo: no ejecuta tools, solo permite construir el runner."""

    def __init__(self):
        self.registry = None
        self.event_log = None

    def execute(self, **kwargs):
        return {"success": True, "output": {}}


def test_tenants_registrados():
    slugs = list_registered_tenants()
    assert "bor-agencia" in slugs
    assert "agentic-compiler" in slugs


def test_pipelines_por_tenant():
    assert set(get_tenant_pipelines("bor-agencia")) == {
        "leads_to_draft", "inbox_watcher", "daily_social",
    }
    assert set(get_tenant_pipelines("agentic-compiler")) == {
        "blueprint_from_idea", "compile_tenant",
    }


def test_handlers_por_tenant():
    assert set(get_tenant_handlers("bor-agencia")) == {
        "leads_to_draft", "inbox_watcher", "daily_social",
    }
    assert set(get_tenant_handlers("agentic-compiler")) == {
        "blueprint_from_idea", "compile_tenant",
    }


def test_tenant_desconocido_no_ve_pipelines():
    assert get_tenant_pipelines("no-existe") == {}
    assert get_tenant_handlers("no-existe") == {}


def test_runner_sin_tenant_slug_no_puede_correr():
    runner = PipelineRunner(executor=_StubExecutor(), llm=None)
    with pytest.raises(UnknownPipelineError):
        runner.run("leads_to_draft", "t1", {})


def test_runner_con_tenant_desconocido_falla():
    runner = PipelineRunner(
        executor=_StubExecutor(), llm=None, tenant_slug="no-existe"
    )
    with pytest.raises(UnknownPipelineError):
        runner.run("leads_to_draft", "t1", {})


def test_runner_con_pipeline_desconocido_falla():
    runner = PipelineRunner(
        executor=_StubExecutor(), llm=None, tenant_slug="bor-agencia"
    )
    with pytest.raises(UnknownPipelineError):
        runner.run("pipeline_que_no_existe", "t1", {})


def test_runner_rechaza_pipeline_deshabilitado():
    """Los pipelines del compilador nacen enabled=False (Fase 1)."""
    runner = PipelineRunner(
        executor=_StubExecutor(), llm=None, tenant_slug="agentic-compiler"
    )
    with pytest.raises(PipelineStepError) as exc_info:
        runner.run("blueprint_from_idea", "agentic-compiler", {})
    assert "deshabilitado" in str(exc_info.value).lower()


def test_aislamiento_entre_tenants():
    """Mismo pipeline_id no existe en el otro tenant (dominios disjuntos)."""
    bor = set(get_tenant_pipelines("bor-agencia"))
    comp = set(get_tenant_pipelines("agentic-compiler"))
    assert bor.isdisjoint(comp)
    # y el runner de un tenant no ve pipelines del otro
    runner = PipelineRunner(
        executor=_StubExecutor(), llm=None, tenant_slug="bor-agencia"
    )
    with pytest.raises(UnknownPipelineError):
        runner.run("compile_tenant", "t1", {})


def test_tenant_slug_por_parametro_gana_sobre_el_runner():
    """run(..., tenant_slug=X) permite reutilizar el runner."""
    runner = PipelineRunner(
        executor=_StubExecutor(), llm=None, tenant_slug="bor-agencia"
    )
    # pipeline_id del OTRO tenant -> debe fallar porque el slug real es bor-agencia
    with pytest.raises(UnknownPipelineError):
        runner.run("blueprint_from_idea", "t1", {}, tenant_slug="bor-agencia")
    # y con el slug correcto del otro tenant, encuentra el pipeline (aunque
    # luego falle por 'deshabilitado', ya paso el dispatch).
    with pytest.raises(PipelineStepError):
        runner.run(
            "blueprint_from_idea", "agentic-compiler", {},
            tenant_slug="agentic-compiler",
        )