from .skill import Skill, SkillStep

SKILLS = {
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