"""Tests del tenant `agentic-compiler` (FASE 1 — PLAN_CLINE_AGENTE_COMPILADOR.md).

Cubren el alta del tenant, la vista pública sin credenciales, las entidades
estrictas del dominio `compiler` y la policy real evaluada por el PolicyEngine
(`data/policies/agentic-compiler.json`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pytest
from pydantic import ValidationError

from agentic_os.domains.compiler import (
    COMPILER_ENTITY_KINDS,
    CompilationRun,
    CompilerDomain,
    TenantBlueprint,
    TenantIdea,
)
from agentic_os.infrastructure.tenancy import Tenant, TenantConfigPublic
from agentic_os.kernel.ontology.domain_models import (
    ENTITY_TYPE_REGISTRY,
    validate_registry_integrity,
)
from agentic_os.kernel.policy.engine import PolicyEngine

COMPILER_SLUG = "agentic-compiler"
REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _entorno_determinista(monkeypatch: pytest.MonkeyPatch) -> None:
    """CWD en la raíz (la policy se carga con ruta relativa) y sin DEV_ALLOW_ALL."""
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.delenv("DEV_ALLOW_ALL", raising=False)


@pytest.fixture()
def compiler_registered():
    """Bootstrap explícito del dominio (compilar → registrar) y limpieza después."""
    CompilerDomain.register_entities()
    yield
    for kind in COMPILER_ENTITY_KINDS:
        ENTITY_TYPE_REGISTRY.pop(kind, None)


def _repo_tenants() -> Dict[str, Tenant]:
    """Tenants del `registry.json` REAL, indexados por slug y por id.

    No se usa el singleton `TenantRegistry`: otros tests de la suite
    (`test_bug19_tenantregistry_singleton`) lo repuntan a un registry temporal
    que luego desaparece. Estos tests afirman sobre el alta REAL del tenant, así
    que la leen del artefacto commiteado.
    """
    raw = json.loads(
        (REPO_ROOT / "data" / "tenants" / "registry.json").read_text(encoding="utf-8")
    )
    out: Dict[str, Tenant] = {}
    for item in raw:
        tenant = Tenant(**item)
        out[tenant.slug] = tenant
        out[tenant.id] = tenant
    return out


@pytest.fixture()
def compiler_tenant() -> Tenant:
    tenant = _repo_tenants().get(COMPILER_SLUG)
    assert tenant is not None, "falta el tenant agentic-compiler en registry.json"
    return tenant


@pytest.fixture()
def policy_engine(monkeypatch: pytest.MonkeyPatch, compiler_tenant: Tenant) -> PolicyEngine:
    """PolicyEngine con el tenant real inyectado (el singleton puede estar sucio)."""
    engine = PolicyEngine()
    monkeypatch.setattr(engine, "_tenant", lambda _tid: compiler_tenant)
    return engine


# --------------------------------------------------------------- alta tenant --


def test_tenant_agentic_compiler_dado_de_alta(compiler_tenant: Tenant) -> None:
    assert compiler_tenant.slug == COMPILER_SLUG
    assert compiler_tenant.config.domain == "compiler"
    assert compiler_tenant.config.data_dir == "data/tenants/agentic-compiler"
    assert compiler_tenant.config.credentials["api_key"].startswith("tk_")
    for cap in (
        "repo.file.read",
        "repo.file.list",
        "repo.search",
        "codegen.blueprint.generate",
        "repo.file.write",
    ):
        assert cap in compiler_tenant.config.enabled_capabilities


def test_config_publico_no_expone_credenciales(compiler_tenant: Tenant) -> None:
    public = TenantConfigPublic.from_config(compiler_tenant.config)
    assert "credentials" not in public.model_dump()
    assert "api_key" not in public.connected_providers
    assert public.domain == "compiler"


# ---------------------------------------------------------------- entidades ---


def test_kinds_del_dominio_registrados_e_integridad(compiler_registered) -> None:
    assert COMPILER_ENTITY_KINDS == {
        "compiler.idea",
        "compiler.blueprint",
        "compiler.run",
    }
    for kind in COMPILER_ENTITY_KINDS:
        assert kind in ENTITY_TYPE_REGISTRY
    # Se valida DESPUÉS de compilar la ontología y registrar (camino canónico).
    validate_registry_integrity()


def test_idea_normaliza_deriva_keywords_y_slug() -> None:
    idea = TenantIdea(
        tenant_id=COMPILER_SLUG,
        idea_nl="  Quiero   un OS\n agentico para una clinica  ",
    )
    assert idea.idea_normalizada == "Quiero un OS agentico para una clinica"
    assert "clinica" in idea.keywords
    assert idea.slug_hint == idea.keywords[0]
    assert idea.domain_hint == "generic"


def test_idea_rechaza_texto_vacio() -> None:
    with pytest.raises(ValidationError):
        TenantIdea(tenant_id=COMPILER_SLUG, idea_nl="   ")


def _blueprint(**overrides) -> TenantBlueprint:
    data = {
        "tenant_id": COMPILER_SLUG,
        "idea_id": "idea-1",
        "idea_nl": "clinica dental con citas",
        "slug": "clinica-dental",
        "tenant_name": "Clinica Dental",
        "domain": "clinic",
        "entities": ["clinic.patient"],
        "capabilities": ["calendar.event.create"],
        "policy": {"calendar.event.create": "require_approval"},
    }
    data.update(overrides)
    return TenantBlueprint(**data)


def test_blueprint_nace_propuesto_con_gate_pendiente() -> None:
    bp = _blueprint()
    assert bp.status == "proposed"
    assert bp.gate == "gate_1"
    assert bp.mode == "plan"
    assert bp.entity_type == "compiler.blueprint"


@pytest.mark.parametrize(
    "overrides",
    [
        {"slug": "../etc/passwd"},
        {"entities": []},
        {"capabilities": []},
        {"mode": "auto"},
        {"policy": {"x.y": "quizas"}},
    ],
)
def test_blueprint_fail_closed(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        _blueprint(**overrides)


def test_compilation_run_nunca_publica_en_main() -> None:
    run = CompilationRun(
        tenant_id=COMPILER_SLUG,
        blueprint_id="bp-1",
        branch="agentic-os-roo",
        steps=["plan_write"],
    )
    assert run.status == "queued"
    with pytest.raises(ValidationError):
        CompilationRun(tenant_id=COMPILER_SLUG, blueprint_id="bp-1", branch="main")


# ------------------------------------------------------------------- policy ---


@pytest.mark.parametrize(
    "cap",
    [
        "repo.file.read",
        "repo.file.list",
        "repo.search",
        "codegen.blueprint.generate",
    ],
)
def test_policy_permite_lectura_y_blueprint(policy_engine: PolicyEngine, cap: str) -> None:
    decision = policy_engine.decide(COMPILER_SLUG, cap, roles=["director"])
    assert decision.effect == "allow"


def test_policy_exige_aprobacion_para_escribir_en_repo(policy_engine: PolicyEngine) -> None:
    decision = policy_engine.decide(COMPILER_SLUG, "repo.file.write", roles=["director"])
    assert decision.effect == "require_approval"


def test_policy_deniega_escritura_sin_rol_director(policy_engine: PolicyEngine) -> None:
    assert policy_engine.decide(COMPILER_SLUG, "repo.file.write").effect == "deny"


def test_policy_deniega_capability_no_habilitada(policy_engine: PolicyEngine) -> None:
    decision = policy_engine.decide(COMPILER_SLUG, "git.push")
    assert decision.effect == "deny"
    assert "no habilitada" in decision.reason
