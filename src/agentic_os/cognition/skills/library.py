from __future__ import annotations

import hashlib
from types import MappingProxyType
from typing import Any, Dict, Tuple

import yaml

from ..memory.store import MemoryItem, MemoryStore
from ...infrastructure.persistence import get_eventlog_repo
from ...kernel.world.events import Event

from .skill import Skill, SkillStep

_SKILLS: Dict[str, Skill] = {
    # --- Gestión de email (inbox zero) ---
    "inbox_zero": Skill(
        name="inbox_zero",
        description="Procesar email y proponer Intent",
        requires_tool="gmail_read",
        steps=[
            SkillStep(order=1, name="leer_inbox", tool="gmail_read", validation="email_valido"),
            SkillStep(order=2, name="clasificar", tool="documentation_search"),
        ],
        role_required="operator",
        input_schema={"query": "str", "max_results": "int"},
        output_schema={"status": "str", "messages": "list"},
    ),
    # --- Agendar reunión ---
    "schedule_meeting": Skill(
        name="schedule_meeting",
        description="Proponer y crear reunión en calendario",
        requires_tool="calendar_create_event",
        steps=[
            SkillStep(order=1, name="listar_disponibilidad", tool="calendar_list_events"),
            SkillStep(order=2, name="crear_evento", tool="calendar_create_event", validation="evento_valido"),
        ],
        role_required="operator",
        input_schema={"title": "str", "start": "str", "end": "str", "attendees": "list"},
        output_schema={"status": "str", "event_id": "str"},
    ),
    # --- Enviar email (SOP) ---
    "send_email_sop": Skill(
        name="send_email_sop",
        description="Redactar y enviar un email siguiendo el SOP",
        requires_tool="gmail_send",
        steps=[
            SkillStep(order=1, name="validar_destinatario", tool="gmail_send", validation="email_valido"),
            SkillStep(order=2, name="registrar_envio", tool="documentation_create"),
        ],
        role_required="operator",
        input_schema={"to": "str", "subject": "str", "body": "str"},
        output_schema={"status": "str", "message_id": "str"},
    ),
    # --- Conversar por Slack ---
    "slack_respond": Skill(
        name="slack_respond",
        description="Leer canal de Slack y responder siguiendo el tono",
        requires_tool="slack_send",
        steps=[
            SkillStep(order=1, name="leer_canal", tool="slack_read"),
            SkillStep(order=2, name="responder", tool="slack_send"),
        ],
        role_required="operator",
        input_schema={"channel": "str", "text": "str"},
        output_schema={"status": "str", "ts": "str"},
    ),
    # --- WhatsApp ---
    "whatsapp_respond": Skill(
        name="whatsapp_respond",
        description="Leer y responder por WhatsApp",
        requires_tool="whatsapp_send",
        steps=[
            SkillStep(order=1, name="leer_conversacion", tool="whatsapp_read"),
            SkillStep(order=2, name="responder", tool="whatsapp_send"),
        ],
        role_required="operator",
        input_schema={"to": "str", "text": "str"},
        output_schema={"status": "str", "message_id": "str"},
    ),
    # --- Web scraping ---
    "scrape_web": Skill(
        name="scrape_web",
        description="Extraer y documentar contenido de una URL",
        requires_tool="web_scrape",
        steps=[
            SkillStep(order=1, name="scrapear", tool="web_scrape"),
            SkillStep(order=2, name="documentar", tool="documentation_create"),
        ],
        role_required="operator",
        input_schema={"url": "str"},
        output_schema={"status": "str", "title": "str"},
    ),
}

# Registro canónico e INMUTABLE de Skills ejecutables (fail-closed).
# - Cada Skill ya es una instancia Pydantic frozen=True (no mutable).
# - MappingProxyType hace la colección inmutable: ningún módulo puede
#   añadir/eliminar/reemplazar skills en runtime (anti-tampering).
# SKILL_REGISTRY es el alias canónico; SKILLS se conserva por compatibilidad
# con imports existentes (rest.py, executor.py) y son EL MISMO objeto.
SKILLS: MappingProxyType[str, Skill] = MappingProxyType(_SKILLS)
SKILL_REGISTRY = SKILLS

# Almacén del sistema para los Prompt Skills instalados (divulgación progresiva).
# `install_skill` persiste aquí las fichas MemoryItem; la búsqueda top-k por
# tenant usa el magnetismo determinista de `MemoryStore.search`.
PROMPT_SKILLS = MemoryStore()


def _parse_frontmatter(skill_md_content: str) -> Tuple[Dict[str, Any], str]:
    """Extrae el frontmatter YAML y el cuerpo de un SKILL.md estilo Claude.

    Formato obligatorio:
        ---
        name: <id del skill>
        description: <qué hace>
        version: <semver>
        pipeline_id: <clave en el registro SKILLS>   (o `triggers`)
        ---
        <cuerpo markdown: instrucciones consultivas>

    Falla con ``ValueError`` si el frontmatter no existe, está malformado o no
    es un mapeo YAML (fail-closed: nada ambiguo llega al almacén).
    """
    text = (skill_md_content or "").lstrip()
    if not text:
        raise ValueError("skill_md_content vacío: se requiere un SKILL.md")
    if not text.startswith("---"):
        raise ValueError(
            "SKILL.md debe comenzar con frontmatter YAML (línea '---')"
        )
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("frontmatter YAML sin cerrar (falta línea '---')")
    frontmatter = text[3:end]
    body = text[end + 4 :].strip()
    try:
        meta = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:  # pragma: no cover - dependiente de yaml
        raise ValueError(f"frontmatter YAML inválido: {exc}") from exc
    if not isinstance(meta, dict):
        raise ValueError("frontmatter YAML debe ser un mapeo (---\\nclave: valor\\n---)")
    return meta, body


def install_skill(skill_md_content: str, tenant_id: str) -> MemoryItem:
    """Instala un Prompt Skill (SKILL.md estilo Claude) en el sistema.

    Mecanismo fail-closed:
    - El frontmatter debe declarar ``name``, ``description``, ``version`` y
      ``pipeline_id`` (o ``triggers``).
    - El ``pipeline_id``/``name`` debe existir en el registro INMUTABLE
      ``SKILLS`` (MappingProxyType de Skill Pydantic frozen); si no hay un
      Skill ejecutable equivalente, se cancela la instalación con
      ``ValueError`` (nada de texto libre se registra como ejecutable).
    - La ficha se persiste en ``PROMPT_SKILLS`` como ``MemoryItem`` con el
      hash MD5 del contenido (mitiga drift) y se audita un evento
      ``SkillInstalled`` en el EventLog del tenant.
    """
    meta, body = _parse_frontmatter(skill_md_content)

    name = str(meta.get("name") or "").strip()
    description = str(meta.get("description") or "").strip()
    version = str(meta.get("version") or "").strip()
    pipeline_id = str(meta.get("pipeline_id") or "").strip()
    triggers = meta.get("triggers")

    if not name:
        raise ValueError("frontmatter: 'name' es obligatorio")
    if not description:
        raise ValueError("frontmatter: 'description' es obligatoria")
    if not version:
        raise ValueError("frontmatter: 'version' es obligatoria")
    if not pipeline_id and not triggers:
        raise ValueError(
            "frontmatter: se requiere 'pipeline_id' o 'triggers'"
        )

    skill_key = pipeline_id or name
    if skill_key not in SKILLS:
        raise ValueError(
            f"fail-closed: no existe un Skill ejecutable '{skill_key}' en el "
            "registro Pydantic inmutable (library.SKILLS); se cancela la "
            "instalación del Prompt Skill"
        )
    # Normalización: metadata/auditoría siempre apuntan al Skill ejecutable
    # real (si el frontmatter usaba triggers sin pipeline_id, se resuelve name).
    pipeline_id = skill_key

    content_md5 = hashlib.md5(
        skill_md_content.encode("utf-8")
    ).hexdigest()

    item = MemoryItem(
        id=f"skill:{name}:prompt",
        content=body,
        metadata={
            "name": name,
            "tenant_id": tenant_id,
            "version": version,
            "pipeline_id": pipeline_id,
            "triggers": triggers,
            "content_md5": content_md5,
        },
    )
    PROMPT_SKILLS.put(item)

    get_eventlog_repo().append(
        Event(
            kind="SkillInstalled",
            entity_id=item.id,
            tenant_id=tenant_id,
            actor_id="skills",
            payload={
                "name": name,
                "version": version,
                "pipeline_id": pipeline_id,
                "triggers": triggers,
                "content_md5": content_md5,
            },
        )
    )

    return item