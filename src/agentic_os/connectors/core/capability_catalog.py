"""Loader que deriva ActionSpecs del catalogo de providers.

Lee `PROVIDER_SPECS` y por cada capability declarada en
`PROVIDER_SPECS[provider]["capabilities"]` produce un `ActionSpec`:

  - kind:             nombre canonico de la capability (p.ej. "email.message.send")
  - provider:         provider al que pertenece (p.ej. "google")
  - schema:           clase Pydantic para validar el payload
  - risk:             clase de riesgo (RiskClass.*)
  - requires_approval: True para delete/publish/external (metadata para el LLM)
  - description:      texto para el prompt del LLM

Invariante (kernel): el `risk` es METADATA. El endurecimiento duro de
delete/publish vive en `PolicyEvaluator` y NO se puede saltar declarando
un risk mas bajo en el spec.

Formato esperado en `PROVIDER_SPECS`:
    "capabilities": {
        "email.message.read": {"schema": ReadParams, "risk": RiskClass.READ_ONLY},
        "email.message.send": {"schema": SendParams, "risk": RiskClass.EXTERNAL_COMMUNICATION},
    }

Compatibilidad: si un provider aun declara `"caps": [...]` (lista de
strings), el loader usa `archetype_for_kind(kind)` y deriva el risk por
sufijo. Esto permite migrar providers de uno en uno.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Type

from pydantic import BaseModel, ConfigDict, Field

from .models import RiskClass, risk_class_for
from .schemas import GenericParams, archetype_for_kind


# Sufijos que el loader marca como requires_approval por defecto.
# Sirve como metadata para el LLM (que sepa cuando va a necesitar humano).
# El endurecimiento REAL sigue en PolicyEvaluator.
_APPROVAL_SUFFIXES = (".delete", ".remove", ".clear", ".publish", ".send", ".create")


class ActionSpec(BaseModel):
    """Declaracion estable de una capability del sistema.

    Esta es la unidad que el `LLMProposer` recibe. Ni el LLM ni el executor
    ven el provider por debajo; solo este spec.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str
    provider: str
    params_schema: Type[BaseModel]
    risk: str
    requires_approval: bool = False
    description: str = ""


def _declared_capabilities(provider_spec: Dict[str, Any]) -> Iterable[tuple[str, Dict[str, Any]]]:
    """Normaliza las dos formas posibles: `caps` (legacy) y `capabilities` (nuevo)."""
    caps = provider_spec.get("capabilities")
    if isinstance(caps, dict):
        for kind, meta in caps.items():
            yield kind, dict(meta or {})
        return
    legacy = provider_spec.get("caps") or []
    for kind in legacy:
        yield kind, {}


def _risk_for(kind: str, declared: Optional[str]) -> str:
    """Risk declarado o derivado por sufijo (fallback del kernel)."""
    if declared:
        return declared
    return risk_class_for(kind)


def _approval_for(kind: str, declared: Optional[bool]) -> bool:
    """Aprobacion declarada o derivada por sufijo."""
    if declared is not None:
        return declared
    return kind.endswith(_APPROVAL_SUFFIXES)


def derive_action_spec(provider: str, kind: str, meta: Dict[str, Any]) -> ActionSpec:
    """Construye un ActionSpec a partir del provider + kind + meta."""
    schema_cls = meta.get("schema") or archetype_for_kind(kind)
    if not (isinstance(schema_cls, type) and issubclass(schema_cls, BaseModel)):
        raise TypeError(
            f"capability '{kind}' de '{provider}' declara schema no-Pydantic: "
            f"{schema_cls!r}"
        )
    risk = _risk_for(kind, meta.get("risk"))
    requires_approval = _approval_for(kind, meta.get("requires_approval"))
    description = meta.get("description") or _default_description(kind)
    return ActionSpec(
        kind=kind,
        provider=provider,
        params_schema=schema_cls,
        risk=risk,
        requires_approval=requires_approval,
        description=description,
    )


def _default_description(kind: str) -> str:
    """Descripcion humana por convencion del nombre."""
    parts = kind.split(".")
    if len(parts) >= 3:
        verb = parts[-1]
        noun = " ".join(parts[:-1])
        return f"{verb.capitalize()} {noun}"
    return kind


def derive_catalog(
    provider: Optional[str] = None,
    specs: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, ActionSpec]:
    """Deriva el catalogo completo o el de un provider concreto.

    Args:
        provider: si se indica, solo devuelve las capabilities de ese provider.
        specs:    mapa de providers. Si es None, importa PROVIDER_SPECS.

    Returns:
        Dict[kind, ActionSpec]. Fail-closed: kinds sin schema valido
        lanzan TypeError.
    """
    if specs is None:
        from ..providers import PROVIDER_SPECS as _SPECS
        specs = _SPECS

    catalog: Dict[str, ActionSpec] = {}
    for prov, spec in specs.items():
        if provider is not None and prov != provider:
            continue
        for kind, meta in _declared_capabilities(spec):
            catalog[kind] = derive_action_spec(prov, kind, meta)
    return catalog


__all__ = [
    "ActionSpec",
    "derive_action_spec",
    "derive_catalog",
]