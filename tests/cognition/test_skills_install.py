"""TAREA 1 - Instalador de Prompt Skills (install_skill)."""

import hashlib

import pytest

import agentic_os.cognition.skills.library as lib
from agentic_os.cognition.beliefs.belief import Belief
from agentic_os.cognition.memory.store import MemoryItem, MemoryStore
from agentic_os.cognition.planning.intent import Intent
from agentic_os.infrastructure.persistence.memory import InMemoryEventLog

VALID_MD = """---
name: inbox_cero
description: Procesar email y proponer Intent
version: 1.0.0
pipeline_id: inbox_zero
---
Sigue el skill inbox_zero. Lee el inbox, clasifica y propón un intent
estructurado. Nunca ejecutes nada directamente: solo propón.
"""


def test_no_hay_modelos_duplicados():
    """Feedback PR #1: NO se crean modelos nuevos — se usan los canónicos.

    Memoria, creencias e intenciones deben ser las MISMAS clases del
    codebase (identidad de objeto), nunca redefiniciones locales.
    """
    import agentic_os.cognition.reasoning.proposer as proposer_mod

    # library y el proposer importan MemoryItem/Belief/Intent desde las
    # ubicaciones canónicas → misma identidad de clase.
    assert lib.MemoryItem is MemoryItem
    assert proposer_mod.Belief is Belief
    assert proposer_mod.Intent is Intent
    # El executor no define modelos propios: usa el registro inmutable SKILLS.
    from agentic_os.execution.executor import EXECUTABLE_SKILLS

    assert EXECUTABLE_SKILLS is lib.SKILLS


def test_registro_skills_es_inmutable():
    """Feedback PR #1: el registro SKILLS debe ser inmutable (anti-tampering)."""
    from types import MappingProxyType

    assert isinstance(lib.SKILLS, MappingProxyType)
    # SKILL_REGISTRY es el alias canónico del MISMO objeto inmutable.
    assert lib.SKILL_REGISTRY is lib.SKILLS
    # Intentar mutar el registro falla en seco.
    with pytest.raises(TypeError):
        lib.SKILLS["otro_skill"] = "no"


@pytest.fixture()
def fresh_env(monkeypatch):
    store = MemoryStore()
    log = InMemoryEventLog()
    monkeypatch.setattr(lib, "PROMPT_SKILLS", store)
    monkeypatch.setattr(lib, "get_eventlog_repo", lambda: log)
    return store, log


def test_install_skill_ok(fresh_env):
    store, log = fresh_env
    item = lib.install_skill(VALID_MD, tenant_id="tenant-a")

    assert item.id == "skill:inbox_cero:prompt"
    assert "Lee el inbox" in item.content
    assert item.metadata["tenant_id"] == "tenant-a"
    assert item.metadata["version"] == "1.0.0"
    assert item.metadata["pipeline_id"] == "inbox_zero"
    assert item.metadata["content_md5"] == hashlib.md5(
        VALID_MD.encode("utf-8")
    ).hexdigest()

    # Persistido en el almacén del sistema.
    assert store.get(item.id) is item

    # Evento SkillInstalled auditado para el tenant.
    events = log.list_for_tenant("tenant-a")
    assert any(e.kind == "SkillInstalled" for e in events)
    installed = next(e for e in events if e.kind == "SkillInstalled")
    assert installed.entity_id == item.id
    assert installed.actor_id == "skills"


def test_install_skill_fail_closed_sin_skill_ejecutable(fresh_env):
    monkeypatch_tuple = fresh_env
    md = VALID_MD.replace("pipeline_id: inbox_zero", "pipeline_id: no_existe")
    with pytest.raises(ValueError, match="no existe un Skill ejecutable"):
        lib.install_skill(md, tenant_id="tenant-a")
    # Nada queda instalado.
    assert len(monkeypatch_tuple[0]) == 0


def test_install_skill_frontmatter_obligatorio(fresh_env):
    with pytest.raises(ValueError, match="frontmatter"):
        lib.install_skill("no hay frontmatter aqui", tenant_id="tenant-a")


def test_install_skill_frontmatter_sin_cerrar(fresh_env):
    md = "---\nname: x\nversion: 1.0.0\n"
    with pytest.raises(ValueError, match="sin cerrar"):
        lib.install_skill(md, tenant_id="tenant-a")


def test_install_skill_campos_obligatorios(fresh_env):
    md = VALID_MD.replace("version: 1.0.0", "version: ")
    with pytest.raises(ValueError, match="'version' es obligatoria"):
        lib.install_skill(md, tenant_id="tenant-a")


def test_install_skill_sin_pipeline_id_ni_triggers(fresh_env):
    md = VALID_MD.replace("pipeline_id: inbox_zero\n", "")
    with pytest.raises(ValueError, match="pipeline_id.*triggers"):
        lib.install_skill(md, tenant_id="tenant-a")


def test_install_skill_acepta_triggers_sin_pipeline_id(fresh_env):
    md = (
        VALID_MD
        .replace("name: inbox_cero", "name: inbox_zero")
        .replace("pipeline_id: inbox_zero\n", "triggers: [nuevo_email]\n")
    )
    item = lib.install_skill(md, tenant_id="tenant-a")
    assert item.metadata["name"] == "inbox_zero"
    assert item.metadata["pipeline_id"] == "inbox_zero"  # fallback al name
    assert item.metadata["triggers"] == ["nuevo_email"]