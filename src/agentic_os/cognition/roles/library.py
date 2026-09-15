"""Libreria de roles production."""
from .role import Role

LIBRARY = {
    "director": Role(
        name="director",
        description="Propone intenciones, nunca ejecuta. LLM principal.",
        permissions=["propose_intent", "read"],
        forbidden_tools=["*"],
    ),
    "operator": Role(
        name="operator",
        description="Ejecuta tools aprobadas. No puede enviar email sin approval.",
        permissions=["execute", "read"],
        forbidden_tools=["gmail_send"],
        allowed_tools=["gmail_read", "slack_send", "web_search", "web_scrape", "documentation_create", "calendar_list_events", "drive_list_files"],
    ),
    "communicator": Role(
        name="communicator",
        description="Puede enviar comunicaciones tras approval del director/usuario.",
        permissions=["execute", "read", "propose_intent"],
        forbidden_tools=[],
        allowed_tools=["gmail_send", "slack_send", "whatsapp_send", "gmail_create_draft", "meta_post_publish"],
        inherits=["operator"],
    ),
    "researcher": Role(
        name="researcher",
        description="Solo lectura web y documentacion. No escribe ni envia.",
        permissions=["read", "propose_intent"],
        forbidden_tools=["gmail_send", "slack_send", "whatsapp_send", "meta_post_publish", "calendar_create_event"],
    ),
    "admin": Role(
        name="admin",
        description="Acceso total, gestiona tenants y policies. Solo con X-Admin-Key.",
        permissions=["propose_intent", "execute", "read", "write", "approve", "manage_tenants"],
        forbidden_tools=[],
    ),
    "auditor": Role(
        name="auditor",
        description="Solo lectura para auditoria. Nunca ejecuta.",
        permissions=["read"],
        forbidden_tools=["*"],
    ),
}

def get_role(name: str) -> Role:
    role = LIBRARY.get(name.lower())
    if not role:
        raise KeyError(f"rol no registrado: {name!r}")
    return role

def can_role_execute(role_name: str, tool_name: str) -> bool:
    role = get_role(role_name)
    return role.can_use_tool(tool_name)
