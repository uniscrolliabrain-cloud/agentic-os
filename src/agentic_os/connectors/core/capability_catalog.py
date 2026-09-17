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
# .create NO va aqui: crear un recurso no es comunicacion externa ni
# destructivo. El handoff lo dice explicito: solo send/delete/publish
# requieren aprobacion humana por convencion. Los creates que de verdad
# requieran aprobacion los declara el spec con requires_approval=True.
_APPROVAL_SUFFIXES = (".delete", ".remove", ".clear", ".publish", ".send")


class ActionSpec(BaseModel):
    """Declaracion estable de una capability del sistema.

    Esta es la unidad que el `LLMProposer` recibe. El LLM no ve el provider
    por debajo; el `providers` es metadata para el router (que decide a
    quien pedir la capability segun tenant y credenciales).

    Varios providers pueden soportar el mismo kind (p.ej. `web.search` lo
    declaran tavily, serpapi, exa, brave_search). Todos van en `providers`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str
    providers: tuple[str, ...]
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


# Sufijos que mapean a EXTERNAL_COMMUNICATION por convencion. Coherente
# con `_APPROVAL_SUFFIXES`: send/publish son comunicacion externa.
_EXTERNAL_SUFFIXES = (".send", ".publish", ".post")


def _risk_for(kind: str, declared: Optional[str]) -> str:
    """Risk declarado o derivado por sufijo (fallback del kernel).

    Orden:
      1. Declarado explicitamente en el spec.
      2. `risk_class_for(kind)` de `core/models.py` (mapa canonico).
      3. Fallback local por sufijo (.send/.publish/.post -> EXTERNAL).
      4. `LOW_RISK_WRITE` (default de `risk_class_for`).
    """
    if declared:
        return declared
    base = risk_class_for(kind)
    if base != RiskClass.LOW_RISK_WRITE:
        return base
    if kind.endswith(_EXTERNAL_SUFFIXES):
        return RiskClass.EXTERNAL_COMMUNICATION
    return base


def _approval_for(kind: str, declared: Optional[bool]) -> bool:
    """Aprobacion declarada o derivada por sufijo."""
    if declared is not None:
        return declared
    return kind.endswith(_APPROVAL_SUFFIXES)


def derive_action_spec(
    providers: tuple[str, ...],
    kind: str,
    meta: Dict[str, Any],
) -> ActionSpec:
    """Construye un ActionSpec a partir de la lista de providers + kind + meta."""
    schema_cls = meta.get("schema") or archetype_for_kind(kind)
    if not (isinstance(schema_cls, type) and issubclass(schema_cls, BaseModel)):
        raise TypeError(
            f"capability '{kind}' de {providers} declara schema no-Pydantic: "
            f"{schema_cls!r}"
        )
    risk = _risk_for(kind, meta.get("risk"))
    requires_approval = _approval_for(kind, meta.get("requires_approval"))
    description = meta.get("description") or _default_description(kind)
    return ActionSpec(
        kind=kind,
        providers=providers,
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

    # Primera pasada: agrupar providers por kind.
    by_kind: Dict[str, Dict[str, Any]] = {}
    for prov, spec in specs.items():
        if provider is not None and prov != provider:
            continue
        for kind, meta in _declared_capabilities(spec):
            entry = by_kind.setdefault(kind, {"providers": [], "meta": {}})
            if prov not in entry["providers"]:
                entry["providers"].append(prov)
            # El primer meta no vacio gana (los declarados explicitos
            # pesan mas que los legacy caps:[]).
            if meta and not entry["meta"]:
                entry["meta"] = meta

    # Segunda pasada: construir ActionSpec por kind.
    catalog: Dict[str, ActionSpec] = {}
    for kind, entry in by_kind.items():
        providers = tuple(sorted(entry["providers"]))
        catalog[kind] = derive_action_spec(providers, kind, entry["meta"])
    return catalog




# ---------------------------------------------------------------------------
# Acciones internas del orquestador (no son capabilities de connector)
# ---------------------------------------------------------------------------

class _ReplyToUserParams(BaseModel):
    """Params de la accion interna `reply_to_user`."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    message: str = Field(default="")


_INTERNAL_ACTIONS: Dict[str, ActionSpec] = {
    "reply_to_user": ActionSpec(
        kind="reply_to_user",
        providers=(),
        params_schema=_ReplyToUserParams,
        risk=RiskClass.READ_ONLY,
        requires_approval=False,
        description="Responder al usuario sin ejecutar ninguna tool.",
    ),
}


# ---------------------------------------------------------------------------
# API publica para el orquestador
# ---------------------------------------------------------------------------

# Cache del catalogo derivado (inmutable). Se puebla en el primer acceso.
_CATALOG_CACHE: Optional[Dict[str, ActionSpec]] = None


def _get_catalog() -> Dict[str, ActionSpec]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        _CATALOG_CACHE = derive_catalog()
    return _CATALOG_CACHE


def get_action_spec(kind: Optional[str]) -> Optional[ActionSpec]:
    """Devuelve el ActionSpec por kind.

    Busca primero en las acciones internas del orquestador
    (`reply_to_user`) y luego en el catalogo derivado de providers.
    Devuelve None si el kind no existe (fail-closed).
    """
    if not kind:
        return None
    k = kind.strip().lower()
    internal = _INTERNAL_ACTIONS.get(k)
    if internal is not None:
        return internal
    return _get_catalog().get(k)


def validate_action_params(kind: str, payload: Any) -> Optional[BaseModel]:
    """Valida payload contra el schema del kind.

    Devuelve la instancia validada o None si el kind no existe o el
    payload no cumple el schema (fail-closed).
    """
    spec = get_action_spec(kind)
    if spec is None:
        return None
    try:
        return spec.params_schema.model_validate(payload or {})
    except Exception:
        return None


def catalog_prompt_block() -> str:
    """Bloque de texto para inyectar en el system prompt del LLM.

    Formato compacto: kind + riesgo + approval + campos. Sin providers
    (el LLM no debe elegir provider; lo hace el router del kernel).
    """
    lines = ["Acciones disponibles (usa SOLO estos kind):"]
    # Internas primero.
    for spec in _INTERNAL_ACTIONS.values():
        fields = ", ".join(spec.params_schema.model_fields.keys())
        lines.append(f"- {spec.kind}: {spec.description}")
        if fields:
            lines.append(f"    campos: {fields}")
    # Derivadas de providers.
    for kind in sorted(_get_catalog()):
        spec = _get_catalog()[kind]
        approval = " [REQUIERE APROBACION HUMANA]" if spec.requires_approval else ""
        fields = ", ".join(spec.params_schema.model_fields.keys())
        lines.append(f"- {kind}: [{spec.risk}]{approval} {spec.description}")
        if fields:
            lines.append(f"    campos: {fields}")
    return "\n".join(lines)


__all__ = [
    "ActionSpec",
    "derive_action_spec",
    "derive_catalog",
    "get_action_spec",
    "validate_action_params",
    "catalog_prompt_block",
]