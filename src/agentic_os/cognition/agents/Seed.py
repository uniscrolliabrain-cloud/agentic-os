"""Seed del catálogo: microacciones reales (spec 08) + pipelines + agentes (spec 10)."""
from __future__ import annotations
from typing import Iterable, Optional
from .catalog import Catalog, CatalogError
from .schemas import MicroActionSchema, MiniAgentSchema, PipelineSchema, PipelineStep

_MICROACTIONS_SEED: tuple[dict, ...] = (
    {
        "id": "web.search", "action_type": "Search", "entity_type": "URL", "taxonomy": "WEB",
        "purpose": "Buscar en la web y devolver resultados rankeados",
        "tool": "web_search",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}},
        "output_schema": {"type": "object", "properties": {"results": {"type": "array"}}},
        "validation": ["urls_validas"], "error_states": ["SearchUnavailable"], "handoff": ["web.extract_page"],
    },
    {
        "id": "web.extract_page", "action_type": "Read", "entity_type": "Document", "taxonomy": "WEB",
        "purpose": "Extraer contenido estructurado de una página", "tool": "web_scrape",
        "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
        "output_schema": {"type": "object"}, "validation": ["text_no_vacio"],
        "error_states": ["ExtractionFailed"], "handoff": ["documentation.create"],
    },
    {
        "id": "communication.send_email", "action_type": "Communicate", "entity_type": "Email", "taxonomy": "COMMUNICATION",
        "purpose": "Enviar un email", "tool": "gmail_send",
        "input_schema": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}},
        "output_schema": {"type": "object"}, "validation": ["email_valido"], "error_states": ["SendFailed"],
    },
    {
        "id": "communication.read_email", "action_type": "Read", "entity_type": "Email", "taxonomy": "COMMUNICATION",
        "purpose": "Leer emails", "tool": "gmail_read", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "communication.send_slack", "action_type": "Communicate", "entity_type": "Message", "taxonomy": "COMMUNICATION",
        "purpose": "Enviar mensaje por Slack", "tool": "slack_send", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "communication.send_whatsapp", "action_type": "Communicate", "entity_type": "Message", "taxonomy": "COMMUNICATION",
        "purpose": "Enviar WhatsApp", "tool": "whatsapp_send", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "calendar.create_event", "action_type": "Create", "entity_type": "Event", "taxonomy": "AUTOMATION",
        "purpose": "Crear evento", "tool": "calendar_create_event", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "calendar.list_events", "action_type": "Read", "entity_type": "Event", "taxonomy": "AUTOMATION",
        "purpose": "Listar eventos", "tool": "calendar_list_events", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "documentation.create", "action_type": "Create", "entity_type": "Document", "taxonomy": "DOCUMENTS",
        "purpose": "Crear documento interno", "tool": "documentation_create",
        "input_schema": {"type": "object", "properties": {"title": {"type": "string"}}}, "output_schema": {"type": "object"},
    },
    {
        "id": "documentation.search", "action_type": "Search", "entity_type": "Document", "taxonomy": "DOCUMENTS",
        "purpose": "Buscar en base conocimiento", "tool": "documentation_search", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "automation.schedule_job", "action_type": "Execute", "entity_type": "Task", "taxonomy": "AUTOMATION",
        "purpose": "Programar pipeline", "tool": "scheduler_create_job", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "social.post.publish", "action_type": "Publish", "entity_type": "SocialPost", "taxonomy": "SOCIAL",
        "purpose": "Publicar post Meta simulado", "tool": "meta_post_publish", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "file.read", "action_type": "Read", "entity_type": "File", "taxonomy": "DOCUMENTS",
        "purpose": "Leer fichero cache tenant", "tool": "drive_read_file", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "file.list", "action_type": "Read", "entity_type": "File", "taxonomy": "DOCUMENTS",
        "purpose": "Listar ficheros tenant", "tool": "drive_list_files", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
    {
        "id": "draft.create", "action_type": "Create", "entity_type": "Email", "taxonomy": "COMMUNICATION",
        "purpose": "Crear borrador email", "tool": "gmail_create_draft", "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    },
)

def _tool_to_microaction(tool_name: str) -> str:
    _MAP = {
        "gmail_send": "communication.send_email",
        "gmail_read": "communication.read_email",
        "gmail_create_draft": "draft.create",
        "gmail_list_unread": "communication.read_email",
        "slack_send": "communication.send_slack",
        "whatsapp_send": "communication.send_whatsapp",
        "calendar_create_event": "calendar.create_event",
        "calendar_list_events": "calendar.list_events",
        "web_search": "web.search",
        "web_scrape": "web.extract_page",
        "documentation_create": "documentation.create",
        "documentation_search": "documentation.search",
        "meta_post_publish": "social.post.publish",
        "meta_carousel_publish": "social.post.publish",
        "drive_list_files": "file.list",
        "drive_read_file": "file.read",
        "drive_search": "file.list",
        "scheduler_create_job": "automation.schedule_job",
    }
    return _MAP.get(tool_name, f"tool.{tool_name}")

def _pipeline_schema_from_id(pipeline_id: str, purpose: str, input_schema=None, output_schema=None) -> PipelineSchema:
    from ...orchestration.pipelines import PIPELINE_TOOLS
    tools = PIPELINE_TOOLS.get(pipeline_id, [])
    steps = [PipelineStep(order=i, microaction_id=_tool_to_microaction(t)) for i, t in enumerate(tools)]
    return PipelineSchema(id=pipeline_id, name=pipeline_id, purpose=purpose, steps=steps, input_schema=input_schema or {}, output_schema=output_schema or {})

def build_catalog(tool_names: Optional[Iterable[str]] = None) -> Catalog:
    if tool_names is None:
        from ...execution.tools import build_default_registry
        tool_names = list(build_default_registry().tools.keys())
    catalog = Catalog()
    catalog.declare_tools(tool_names)
    for spec in _MICROACTIONS_SEED:
        try:
            catalog.add_microaction(MicroActionSchema(**spec))
        except CatalogError:
            pass
    from ...orchestration.pipelines import PIPELINE_TOOLS
    _purpose = {"daily_social": "Contenido social diario", "inbox_watcher": "Clasifica unread y deja borradores", "leads_to_draft": "Convierte leads en borradores"}
    for pid in PIPELINE_TOOLS:
        p = _pipeline_schema_from_id(pid, purpose=_purpose.get(pid, pid))
        for step in p.steps:
            if step.microaction_id.startswith("tool.") and catalog.microaction(step.microaction_id) is None:
                try:
                    catalog.add_microaction(MicroActionSchema(id=step.microaction_id, action_type="Execute", entity_type="Task", taxonomy="AUTOMATION", purpose=f"Tool nativa {step.microaction_id}", tool=step.microaction_id.replace("tool.", "")))
                except CatalogError:
                    pass
        try:
            catalog.add_pipeline(p)
        except CatalogError:
            pass
    catalog.add_agent(MiniAgentSchema(id="web_research_agent", name="WEB_RESEARCH_AGENT", purpose="Obtener información estructurada web", triggers=["investiga","research"], microactions=["web.search","web.extract_page","documentation.create"], tools=["web_search","web_scrape","documentation_create"], sop="", handoffs=[], permission_policy={"roles":["operator","director"],"deny_by_default":True}, human_approval_policy={"required":False}, observability=["MicroActionStarted"]))
    try:
        catalog.add_agent(MiniAgentSchema(id="communication_agent", name="COMMUNICATION_AGENT", purpose="Redactar y enviar comunicaciones", triggers=["envía email","manda slack"], microactions=["communication.send_email","communication.send_slack","communication.send_whatsapp"], tools=["gmail_send","slack_send","whatsapp_send"], human_approval_policy={"required":True}))
    except CatalogError:
        pass
    return catalog
