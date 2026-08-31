from .base import Tool
from .gmail_tool import (
    GmailSendTool,
    GmailReadTool,
    GmailCreateDraftTool,
    GmailListUnreadTool,
)
from .slack_tool import SlackSendTool, SlackReadTool
from .whatsapp_tool import WhatsAppSendTool, WhatsAppReadTool
from .calendar_tool import CalendarCreateEventTool, CalendarListEventsTool
from .scraper_tool import WebScrapeTool, WebSearchTool
from .documentation_tool import DocumentationCreateTool, DocumentationSearchTool
from .drive_tool import DriveListFilesTool, DriveReadFileTool, DriveSearchTool
from .meta_tool import MetaPostPublishTool, MetaCarouselPublishTool
from .scheduler_tool import (
    SchedulerCreateJobTool,
    SchedulerListJobsTool,
    SchedulerDeleteJobTool,
)
from .registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolRegistry",
    "GmailSendTool",
    "GmailReadTool",
    "GmailCreateDraftTool",
    "GmailListUnreadTool",
    "SlackSendTool",
    "SlackReadTool",
    "WhatsAppSendTool",
    "WhatsAppReadTool",
    "CalendarCreateEventTool",
    "CalendarListEventsTool",
    "WebScrapeTool",
    "WebSearchTool",
    "DocumentationCreateTool",
    "DocumentationSearchTool",
    "DriveListFilesTool",
    "DriveReadFileTool",
    "DriveSearchTool",
    "MetaPostPublishTool",
    "MetaCarouselPublishTool",
    "SchedulerCreateJobTool",
    "SchedulerListJobsTool",
    "SchedulerDeleteJobTool",
]

ALL_TOOLS = [
    GmailSendTool(),
    GmailReadTool(),
    GmailCreateDraftTool(),
    GmailListUnreadTool(),
    SlackSendTool(),
    SlackReadTool(),
    WhatsAppSendTool(),
    WhatsAppReadTool(),
    CalendarCreateEventTool(),
    CalendarListEventsTool(),
    WebScrapeTool(),
    WebSearchTool(),
    DocumentationCreateTool(),
    DocumentationSearchTool(),
    DriveListFilesTool(),
    DriveReadFileTool(),
    DriveSearchTool(),
    MetaPostPublishTool(),
    MetaCarouselPublishTool(),
]


def build_default_registry(scheduler=None) -> ToolRegistry:
    """Construye el ToolRegistry unificado (FASE 2 de hardening).

    Fuente de verdad de qué capabilities existen: el Connector Kernel
    (CapabilityRegistry construido desde ConnectorFactory + catálogo).
    Si la capability canónica de una tool existe en el kernel, la resolución
    va SIEMPRE por ConnectorRouter (ConnectorBridgeTool); el mock de
    execution/tools/*.py es solo el fallback para capabilities sin connector.

    Si se pasa un `scheduler` (FASE 6), se registran también las tools de
    scheduler (necesitan la instancia real para programar/consultar/eliminar).
    """
    from .connector_bridge import (
        CANONICAL_ALIASES,
        ConnectorBridgeTool,
        build_connector_router,
    )

    router = build_connector_router()
    registry = ToolRegistry()
    for tool in ALL_TOOLS:
        capability = CANONICAL_ALIASES.get(tool.name)
        if capability and router.registry.has_capability(capability):
            registry.register(
                ConnectorBridgeTool(name=tool.name, capability=capability, router=router)
            )
        else:
            # Fallback: mock determinista (capability sin connector registrado)
            registry.register(tool)

    if scheduler is not None:
        registry.register(SchedulerCreateJobTool(scheduler))
        registry.register(SchedulerListJobsTool(scheduler))
        registry.register(SchedulerDeleteJobTool(scheduler))

    return registry