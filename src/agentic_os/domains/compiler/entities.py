"""Entidades del dominio `compiler` (FASE 1 — PLAN_CLINE_AGENTE_COMPILADOR.md).

Tres entidades Pydantic **strict** (``frozen=True``, ``extra="forbid"``,
``validate_assignment=True``, ``use_enum_values=True``) que describen el ciclo
del compilador de tenants: una idea en lenguaje natural, el blueprint propuesto
y el estado de una compilación.

Un payload que no valida aquí **no existe** para el kernel (fail-closed).
"""
from __future__ import annotations

import re
from typing import Dict, List, Literal, Optional, Set

from pydantic import Field, field_validator, model_validator

from ...kernel.ontology.domain_models import BaseDomainModel

# ---------------------------------------------------------------------------
# Enumeraciones canónicas del dominio
# ---------------------------------------------------------------------------

BlueprintStatus = Literal["proposed", "approved", "rejected"]

RunStatus = Literal[
    "queued",
    "planning",
    "awaiting_approval",
    "compiling",
    "testing",
    "publishing",
    "done",
    "failed",
    "cancelled",
]

EffectKind = Literal["allow", "deny", "require_approval"]

DEFAULT_MODE = "plan"

# Kinds de entidad del dominio (para la ontología y el registro explícito).
COMPILER_ENTITY_KINDS: frozenset = frozenset(
    {
        "compiler.idea",
        "compiler.blueprint",
        "compiler.run",
    }
)

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}[a-z0-9]?$")
_WORD_RE = re.compile(r"[a-záéíóúñü0-9]+")

# Palabras vacías que no aportan al slug ni a las keywords de la idea.
_STOP_WORDS: Set[str] = {
    "que", "con", "para", "una", "unos", "unas", "los", "las", "por", "como",
    "del", "son", "esta", "este", "esto", "pero", "mas", "más", "muy", "quiero",
    "necesito", "tengo", "hacer", "hazme", "the", "and", "for", "with", "from",
}

# Rama protegida: el compilador jamás publica en `main` sin PR (invariante I8).
PROTECTED_BRANCH = "main"


def _validate_not_empty(v: str, field: str) -> str:
    if not v or not v.strip():
        raise ValueError(f"{field} obligatorio")
    return v.strip()


def normalize_idea(text: str) -> str:
    """Normaliza una idea: colapsa espacios y saltos, recorta extremos."""
    return " ".join((text or "").split())


def idea_keywords(text: str, limit: int = 12) -> List[str]:
    """Extrae keywords deterministas (orden de aparición, sin duplicados)."""
    out: List[str] = []
    seen: Set[str] = set()
    for word in _WORD_RE.findall((text or "").lower()):
        if len(word) < 3 or word in _STOP_WORDS or word in seen:
            continue
        seen.add(word)
        out.append(word)
        if len(out) >= limit:
            break
    return out


def _validate_slug(v: str) -> str:
    v = v.strip().lower()
    if not _SLUG_RE.match(v) or ".." in v or "/" in v or "\\" in v:
        raise ValueError(
            f"slug inválido: '{v}'. Solo minúsculas, números, guiones y "
            "guiones bajos (1-64 caracteres), sin path traversal."
        )
    return v

# ---------------------------------------------------------------------------
# Entidades del dominio compiler
# ---------------------------------------------------------------------------


class TenantIdea(BaseDomainModel):
    """Idea en lenguaje natural con la que un cliente se «muda» a Agentic OS.

    El compilador NO interpreta la idea con heurísticas libres en el kernel:
    guarda el texto literal (``idea_nl``) y una versión normalizada
    (``idea_normalizada``) más las keywords extraídas de forma determinista.
    """

    kind: Literal["compiler.idea"] = "compiler.idea"
    idea_nl: str
    idea_normalizada: str = ""
    slug_hint: str = ""
    domain_hint: str = "generic"
    keywords: List[str] = Field(default_factory=list)

    @field_validator("idea_nl")
    @classmethod
    def _idea_not_empty(cls, v: str) -> str:
        v = _validate_not_empty(v, "idea_nl")
        if len(normalize_idea(v)) < 3:
            raise ValueError("idea_nl demasiado corta (mínimo 3 caracteres útiles)")
        return v

    @field_validator("keywords")
    @classmethod
    def _keywords_no_vacias(cls, v: List[str]) -> List[str]:
        for item in v:
            if not item.strip():
                raise ValueError("keywords no puede contener entradas vacías")
        return v

    @model_validator(mode="after")
    def _autocompletar(self) -> "TenantIdea":
        """Deriva normalizada/keywords/slug de la idea (determinista)."""
        texto = normalize_idea(self.idea_nl)
        if not self.idea_normalizada:
            object.__setattr__(self, "idea_normalizada", texto)
        if not self.keywords:
            object.__setattr__(self, "keywords", idea_keywords(texto))
        if self.slug_hint:
            object.__setattr__(self, "slug_hint", _validate_slug(self.slug_hint))
        elif self.keywords:
            object.__setattr__(self, "slug_hint", _validate_slug(self.keywords[0]))
        return self


class TenantBlueprint(BaseDomainModel):
    """Esquema del tenant propuesto por el compilador (modo PLAN).

    Es un **artefacto de propuesta**: nada de lo que describe se aplica hasta
    que un humano resuelve el Gate 1. Las capabilities listadas son las que
    tendría el tenant NUEVO, nunca permisos que el compilador se autoconceda.
    """

    kind: Literal["compiler.blueprint"] = "compiler.blueprint"
    idea_id: str
    idea_nl: str
    slug: str
    tenant_name: str
    domain: str = "generic"
    entities: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    policy: Dict[str, EffectKind] = Field(default_factory=dict)
    phases: List[str] = Field(default_factory=list)
    status: BlueprintStatus = "proposed"
    gate: str = "gate_1"
    mode: str = DEFAULT_MODE

    @field_validator("idea_id", "tenant_name")
    @classmethod
    def _obligatorios(cls, v: str) -> str:
        return _validate_not_empty(v, "campo obligatorio")

    @field_validator("slug")
    @classmethod
    def _slug_valid(cls, v: str) -> str:
        return _validate_slug(v)

    @field_validator("entities")
    @classmethod
    def _entities_no_vacias(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("entities debe contener al menos una entidad propuesta")
        return v

    @field_validator("capabilities")
    @classmethod
    def _capabilities_no_vacias(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("capabilities debe contener al menos una capability")
        return v

    @field_validator("mode")
    @classmethod
    def _modo_plan_por_defecto(cls, v: str) -> str:
        if v not in ("plan", "act"):
            raise ValueError("mode debe ser 'plan' o 'act'")
        return v

    @model_validator(mode="after")
    def _gate_obligatorio_si_propuesto(self) -> "TenantBlueprint":
        """Un blueprint en estado `proposed` SIEMPRE tiene gate humano pendiente."""
        if self.status == "proposed" and not self.gate:
            object.__setattr__(self, "gate", "gate_1")
        return self


class CompilationRun(BaseDomainModel):
    """Estado de una compilación (de la idea al tenant vivo)."""

    kind: Literal["compiler.run"] = "compiler.run"
    blueprint_id: str
    status: RunStatus = "queued"
    branch: str = ""
    steps: List[str] = Field(default_factory=list)
    last_error: Optional[str] = None

    @field_validator("blueprint_id")
    @classmethod
    def _blueprint_obligatorio(cls, v: str) -> str:
        return _validate_not_empty(v, "blueprint_id")

    @field_validator("branch")
    @classmethod
    def _rama_nunca_main(cls, v: str) -> str:
        """Invariante I8: el código generado vive en `agentic-os-roo`, nunca en main."""
        if v.strip().lower() == PROTECTED_BRANCH:
            raise ValueError(
                f"branch '{PROTECTED_BRANCH}' prohibida: el compilador publica vía PR "
                "(invariante I8)"
            )
        return v.strip()

    @field_validator("steps")
    @classmethod
    def _steps_no_vacios(cls, v: List[str]) -> List[str]:
        for step in v:
            if not step.strip():
                raise ValueError("steps no puede contener pasos vacíos")
        return v


__all__ = [
    "COMPILER_ENTITY_KINDS",
    "DEFAULT_MODE",
    "PROTECTED_BRANCH",
    "BlueprintStatus",
    "RunStatus",
    "EffectKind",
    "TenantIdea",
    "TenantBlueprint",
    "CompilationRun",
    "normalize_idea",
    "idea_keywords",
]