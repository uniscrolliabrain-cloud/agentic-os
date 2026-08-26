from .base import Tool
from .gmail_tool import GmailSendTool, GmailReadTool
from .slack_tool import SlackSendTool, SlackReadTool
from .whatsapp_tool import WhatsAppSendTool, WhatsAppReadTool
from .calendar_tool import CalendarCreateEventTool, CalendarListEventsTool
from .scraper_tool import WebScrapeTool, WebSearchTool
from .documentation_tool import DocumentationCreateTool, DocumentationSearchTool
from .registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolRegistry",
    "GmailSendTool",
    "GmailReadTool",
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
]

ALL_TOOLS = [
    GmailSendTool(),
    GmailReadTool(),
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
]


def build_default_registry() -> ToolRegistry:
    """Construye un ToolRegistry con todas las tools disponibles."""
    registry = ToolRegistry()
    for tool in ALL_TOOLS:
        registry.register(tool)
    return registry