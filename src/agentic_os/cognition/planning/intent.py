from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from ...kernel.types.ids import new_id

class IntentKind(str, Enum):
    REPLY_TO_USER = "reply_to_user"
    SEND_EMAIL = "send_email"
    SEND_SLACK = "send_slack"
    SEND_WHATSAPP = "send_whatsapp"
    CREATE_EVENT = "create_event"
    SEARCH_WEB = "search_web"
    EXTRACT_PAGE = "extract_page"
    CREATE_DOCUMENT = "create_document"
    SCHEDULE_JOB = "schedule_job"
    PUBLISH_POST = "publish_post"
    READ_FILE = "read_file"
    CUSTOM = "custom"

class Intent(BaseModel):
    """Propuesta del LLM/Proposer. NUNCA es una accion ejecutada. Pasa por Policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    goal: str = Field(default="", description="que quiere lograr en una frase")
    kind: str = Field(
        default=IntentKind.REPLY_TO_USER.value,
        description="clase de acción propuesta (canónico o libre; el mapping fail-closed lo resuelve)",
    )
    entity_id: str = Field(default="n/a")
    payload: Dict[str, Any] = Field(default_factory=dict, description="parametros estructurados, no string libre")
    rationale: str = Field(default="", description="por que se propone, auditable")
    reply_to_user: Optional[str] = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    requires_approval: bool = Field(default=False)
    risk_level: str = Field(default="low", description="low|medium|high")
    source_belief_ids: List[str] = Field(default_factory=list)

    def is_safe_to_auto_execute(self) -> bool:
        return not self.requires_approval and self.risk_level == "low" and self.kind == IntentKind.REPLY_TO_USER
