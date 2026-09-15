"""Libreria de skills production - 3 SOPs reales."""
from __future__ import annotations
from .skill import Skill, SkillStep

SKILLS = [
    Skill(
        name="inbox_zero",
        description="Procesa bandeja de entrada: lee unread, clasifica, crea borradores para leads.",
        category="communication",
        requires_tool="gmail_read",
        role_required="operator",
        input_schema={"type": "object", "properties": {"max_emails": {"type": "integer"}}, "required": []},
        output_schema={"type": "object", "properties": {"drafts_created": {"type": "integer"}}},
        steps=[
            SkillStep(order=0, name="list_unread", description="Lista no leidos", tool="gmail_read", output_key="emails"),
            SkillStep(order=1, name="classify", description="Clasifica por intencion", tool="documentation_create", requires="emails", output_key="classified"),
            SkillStep(order=2, name="draft_replies", description="Crea borradores", tool="gmail_create_draft", requires="classified", output_key="drafts_created"),
        ],
        preconditions=["gmail_read disponible"],
        postconditions=["borradores creados, nunca envio directo"],
        version="1.0",
    ),
    Skill(
        name="research_and_write",
        description="Investiga web y escribe documento interno.",
        category="research",
        requires_tool="web_search",
        role_required="researcher",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        steps=[
            SkillStep(order=0, name="search", tool="web_search", output_key="search_results", validation="query_no_vacia"),
            SkillStep(order=1, name="extract", tool="web_scrape", requires="search_results", output_key="pages"),
            SkillStep(order=2, name="write_doc", tool="documentation_create", requires="pages", output_key="doc_id"),
        ],
        version="1.0",
    ),
    Skill(
        name="schedule_meeting",
        description="Busca hueco y crea evento de calendario.",
        category="automation",
        requires_tool="calendar_list_events",
        role_required="operator",
        input_schema={"type": "object", "properties": {"attendees": {"type": "array"}, "duration_minutes": {"type": "integer"}}, "required": ["attendees"]},
        steps=[
            SkillStep(order=0, name="list_events", tool="calendar_list_events", output_key="existing_events"),
            SkillStep(order=1, name="propose_slot", tool="documentation_create", requires="existing_events", output_key="proposed_slot"),
            SkillStep(order=2, name="create_event", tool="calendar_create_event", requires="proposed_slot", output_key="event_id"),
        ],
        version="1.0",
    ),
]

SKILLS_BY_NAME = {s.name: s for s in SKILLS}

def get_skill(name: str) -> Skill:
    skill = SKILLS_BY_NAME.get(name)
    if not skill:
        raise KeyError(f"skill no registrado: {name!r}")
    return skill
