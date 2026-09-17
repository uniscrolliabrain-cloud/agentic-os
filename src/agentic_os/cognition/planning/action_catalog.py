"""Catalogo de acciones propuestas desde el chat (Fase A).

Contrato unico entre:
  - LLMProposer (Fase B): que kinds puede emitir y con que payload
  - Router determinista (Fase B): match keyword -> kind
  - rest.py (Fase B): validar payload antes de ejecutar
  - Policy (ya): autorizar por nombre de action

El catalogo NO ejecuta nada. Solo declara esquemas.
Invariante: lo que no valida contra schema, no se propone.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictParams(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ReplyToUserParams(_StrictParams):
    message: str = Field(default="")


class SendEmailParams(_StrictParams):
    to: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)

    @field_validator("to")
    @classmethod
    def _email_like(cls, v: str) -> str:
        v = v.strip()
        if "@" not in v or " " in v:
            raise ValueError("to debe ser una direccion de email valida")
        return v


class ReadEmailParams(_StrictParams):
    max_results: int = Field(default=5, ge=1, le=50)
    query: str = ""


class ListDriveParams(_StrictParams):
    folder: str = ""


class ReadDriveFileParams(_StrictParams):
    path: str = Field(min_length=1)


class CreateEventParams(_StrictParams):
    title: str = Field(min_length=1)
    start: str = Field(min_length=1)
    end: str = ""
    attendees: list[str] = Field(default_factory=list)


class ListEventsParams(_StrictParams):
    max_results: int = Field(default=5, ge=1, le=50)


class SearchWebParams(_StrictParams):
    query: str = Field(min_length=1)


class ScrapeWebParams(_StrictParams):
    url: str = Field(min_length=5)


class ActionSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: str
    action: str
    params_model: Type[BaseModel]
    requires_approval: bool = False
    description: str = ""


ACTION_CATALOG: Dict[str, ActionSpec] = {
    spec.kind: spec
    for spec in (
        ActionSpec(kind="reply_to_user", action="reply_to_user", params_model=ReplyToUserParams, description="Responder al usuario sin ejecutar ninguna tool."),
        ActionSpec(kind="send_email", action="gmail_send", params_model=SendEmailParams, requires_approval=True, description="Enviar un email externo. REQUIERE APROBACION HUMANA."),
        ActionSpec(kind="read_email", action="gmail_read", params_model=ReadEmailParams, description="Leer los ultimos mensajes del buzon."),
        ActionSpec(kind="list_drive", action="drive_list_files", params_model=ListDriveParams, description="Listar ficheros de Drive."),
        ActionSpec(kind="read_drive_file", action="drive_read_file", params_model=ReadDriveFileParams, description="Leer un fichero de Drive."),
        ActionSpec(kind="create_event", action="calendar_create_event", params_model=CreateEventParams, description="Crear un evento."),
        ActionSpec(kind="list_events", action="calendar_list_events", params_model=ListEventsParams, description="Listar eventos."),
        ActionSpec(kind="search_web", action="web_search", params_model=SearchWebParams, description="Buscar en la web."),
        ActionSpec(kind="scrape_web", action="web_scrape", params_model=ScrapeWebParams, description="Extraer contenido de una pagina."),
    )
}


def get_spec(kind: Optional[str]) -> Optional[ActionSpec]:
    if not kind:
        return None
    return ACTION_CATALOG.get(kind.strip().lower())


def validate_params(kind: str, payload: Any) -> Optional[BaseModel]:
    spec = get_spec(kind)
    if spec is None:
        return None
    try:
        return spec.params_model.model_validate(payload or {})
    except Exception:
        return None


def catalog_prompt_block() -> str:
    lines = ["Acciones disponibles (usa SOLO estos kind):"]
    for spec in ACTION_CATALOG.values():
        approval = " [REQUIERE APROBACION HUMANA]" if spec.requires_approval else ""
        fields = ", ".join(spec.params_model.model_fields.keys())
        lines.append(f"- {spec.kind}: {spec.description}{approval}")
        if fields:
            lines.append(f"    campos: {fields}")
    return "\n".join(lines)


__all__ = ["ACTION_CATALOG", "ActionSpec", "get_spec", "validate_params", "catalog_prompt_block"]