from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ...cognition.planning.intent import Intent
from ...cognition.skills.library import SKILLS
from ...cognition.skills.skill import Skill, SkillStep
from ...execution.action import Action
from ...execution.executor import Executor
from ...execution.tools import build_default_registry
from ...execution.tools.base import Tool
from ...infrastructure.config.settings import Settings
from ...infrastructure.tenancy import Tenant, TenantConfig, TenantContext, TenantRegistry
from ...interfaces.llm.provider import GeminiProvider, MockLLMProvider
from ...kernel.policy.engine import PolicyEngine
from ...kernel.policy.models import Policy, PolicyRule
from ...kernel.world.events import Event, EventLog
from ...orchestration.orchestrator import Orchestrator

app = FastAPI(title="Agentic OS", version="0.1.0")

# CORS: permitir el frontend React (Vite dev server en :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Estado global (en memoria por ahora; se persistirá más adelante) ---
settings = Settings()
_event_log = EventLog()

if settings.gemini_api_key:
    _llm = GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
else:
    # Sin API key: usamos un mock determinista para que el backend arranque
    # y el frontend pueda probarse. Sustituir por Gemini real configurando .env
    _llm = MockLLMProvider(
        default_response=(
            '{"goal": "responder al usuario", "kind": "reply_to_user", '
            '"entity_id": "n/a", "payload": "", "rationale": "mock sin API key", '
            '"reply_to_user": "Hola! Soy el director (modo mock). Configura GEMINI_API_KEY en .env para respuestas reales."}'
        )
    )

_orchestrator = Orchestrator(log=_event_log, llm=_llm)

# --- Persistencia de conversaciones ---
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _conv_path(conv_id: str) -> Path:
    return CONVERSATIONS_DIR / f"{conv_id}.json"


def _load_conversation(conv_id: str) -> Dict[str, Any]:
    path = _conv_path(conv_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_conversation(conv: Dict[str, Any]) -> None:
    with open(_conv_path(conv["id"]), "w", encoding="utf-8") as f:
        json.dump(conv, f, ensure_ascii=False, indent=2)


# --- Schemas de request/response ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: Intent
    reply: str


class MessageOut(BaseModel):
    role: str
    content: str


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[MessageOut]


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class EventOut(BaseModel):
    id: str
    kind: str
    entity_id: str
    payload: Dict[str, Any]
    at: str
    actor_id: Optional[str] = None


class StateOut(BaseModel):
    role: str
    event_count: int


# --- Endpoints base ---
@app.get("/")
def root() -> Dict[str, str]:
    return {"app": "Agentic OS", "status": "ok"}


@app.get("/api/state", response_model=StateOut)
def get_state() -> StateOut:
    return StateOut(
        role=_orchestrator.current_role.name,
        event_count=len(_event_log),
    )


@app.get("/api/events", response_model=List[EventOut])
def get_events() -> List[EventOut]:
    return [
        EventOut(
            id=e.id,
            kind=e.kind,
            entity_id=e.entity_id,
            payload=e.payload,
            at=e.at.isoformat(),
            actor_id=e.actor_id,
        )
        for e in _event_log.events
    ]


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """El usuario escribe un mensaje -> el rol activo (director) propone una
    Intent -> se guarda como evento auditable -> se devuelve la propuesta.
    NUNCA ejecuta nada por sí mismo."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    try:
        intent = _orchestrator.handle_user_message(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la propuesta: {e}")

    reply = intent.reply_to_user or f"(Propuesta: {intent.kind} sobre {intent.entity_id})"
    return ChatResponse(intent=intent, reply=reply)


# --- Endpoints de conversaciones ---
@app.get("/api/conversations", response_model=List[ConversationSummary])
def list_conversations() -> List[ConversationSummary]:
    """Lista todas las conversaciones guardadas, ordenadas por updated_at desc."""
    summaries = []
    for path in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                conv = json.load(f)
            summaries.append(
                ConversationSummary(
                    id=conv["id"],
                    title=conv["title"],
                    created_at=conv["created_at"],
                    updated_at=conv["updated_at"],
                    message_count=len(conv["messages"]),
                )
            )
        except Exception:
            continue
    summaries.sort(key=lambda c: c.updated_at, reverse=True)
    return summaries


@app.post("/api/conversations", response_model=ConversationOut)
def create_conversation() -> ConversationOut:
    """Crea una conversación nueva vacía."""
    now = datetime.utcnow().isoformat()
    conv = {
        "id": str(uuid.uuid4()),
        "title": "Nueva conversación",
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    _save_conversation(conv)
    return ConversationOut(**conv)


@app.get("/api/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(conv_id: str) -> ConversationOut:
    """Carga una conversación por id."""
    conv = _load_conversation(conv_id)
    return ConversationOut(**conv)


@app.post("/api/conversations/{conv_id}/messages", response_model=ConversationOut)
def add_message(conv_id: str, msg: MessageOut) -> ConversationOut:
    """Añade un mensaje a una conversación y actualiza su título si es el primero."""
    conv = _load_conversation(conv_id)
    conv["messages"].append({"role": msg.role, "content": msg.content})
    if len(conv["messages"]) == 1:
        # Usar el primer mensaje del usuario como título
        conv["title"] = msg.content[:50] + ("..." if len(msg.content) > 50 else "")
    conv["updated_at"] = datetime.utcnow().isoformat()
    _save_conversation(conv)
    return ConversationOut(**conv)


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str) -> Dict[str, str]:
    """Elimina una conversación."""
    path = _conv_path(conv_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    path.unlink()
    return {"status": "deleted", "id": conv_id}


# --- Estado global adicional: tenants, policy, executor ---
_tenant_registry = TenantRegistry()
_policy_engine = PolicyEngine()
_executor = Executor(registry=build_default_registry())


# --- Schemas de tenants ---
class TenantCreate(BaseModel):
    name: str
    slug: str
    config: Optional[Dict[str, Any]] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    config: Dict[str, Any]
    created_at: str


# --- Schemas de ejecución ---
class ExecuteRequest(BaseModel):
    tenant_id: str
    action: str
    params: Dict[str, Any] = {}


class ExecuteResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None


class SkillOut(BaseModel):
    name: str
    description: str
    steps: List[str]


class ToolOut(BaseModel):
    name: str


# --- Endpoints de tenants ---
@app.get("/api/tenants", response_model=List[TenantOut])
def list_tenants() -> List[TenantOut]:
    """Lista todos los tenants registrados."""
    return [
        TenantOut(
            id=t.id,
            name=t.config.name,
            slug=t.slug,
            config=t.config.model_dump(),
            created_at=t.created_at.isoformat(),
        )
        for t in _tenant_registry.list_all()
    ]


@app.post("/api/tenants", response_model=TenantOut, status_code=201)
def create_tenant(req: TenantCreate) -> TenantOut:
    """Crea un nuevo tenant (organización/espacio aislado)."""
    try:
        tenant = _tenant_registry.create(
            name=req.name,
            slug=req.slug,
            config=req.config or {},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TenantOut(
        id=tenant.id,
        name=tenant.config.name,
        slug=tenant.slug,
        config=tenant.config.model_dump(),
        created_at=tenant.created_at.isoformat(),
    )


@app.get("/api/tenants/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str) -> TenantOut:
    """Obtiene un tenant por id."""
    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return TenantOut(
        id=tenant.id,
        name=tenant.config.name,
        slug=tenant.slug,
        config=tenant.config.model_dump(),
        created_at=tenant.created_at.isoformat(),
    )


@app.patch("/api/tenants/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: str, req: TenantUpdate) -> TenantOut:
    """Actualiza nombre y/o configuración de un tenant."""
    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Tenant es inmutable (frozen) -> construimos uno nuevo
    new_config = tenant.config
    if req.name is not None:
        new_config = new_config.model_copy(update={"name": req.name})
    if req.config is not None:
        merged = tenant.config.model_dump()
        merged.update(req.config)
        new_config = TenantConfig(**merged)

    updated = Tenant(
        id=tenant.id,
        slug=tenant.slug,
        config=new_config,
        created_at=tenant.created_at,
    )
    _tenant_registry.update(updated)
    return TenantOut(
        id=updated.id,
        name=updated.config.name,
        slug=updated.slug,
        config=updated.config.model_dump(),
        created_at=updated.created_at.isoformat(),
    )


@app.delete("/api/tenants/{tenant_id}")
def delete_tenant(tenant_id: str) -> Dict[str, str]:
    """Elimina un tenant."""
    if not _tenant_registry.delete(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return {"status": "deleted", "id": tenant_id}


# --- Endpoints de skills y tools ---
@app.get("/api/skills", response_model=List[SkillOut])
def list_skills() -> List[SkillOut]:
    """Lista el catálogo de skills/SOPs disponibles."""
    return [
        SkillOut(
            name=s.name,
            description=s.description,
            steps=[step.name for step in s.steps],
        )
        for s in SKILLS.values()
    ]


@app.get("/api/tools", response_model=List[ToolOut])
def list_tools() -> List[ToolOut]:
    """Lista las herramientas disponibles en el registry."""
    return [
        ToolOut(name=t.name)
        for t in _executor.registry.tools.values()
    ]


# --- Endpoint de ejecución ---
@app.post("/api/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest) -> ExecuteResponse:
    """Ejecuta una acción concreta en el contexto de un tenant.
    El flujo completo es: LLM propone Intent -> Policy la valida -> Executor la ejecuta."""
    tenant = _tenant_registry.get(req.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # 1. Validar política del tenant
    if not _policy_engine.is_allowed(tenant_id=tenant.id, action=req.action):
        return ExecuteResponse(
            success=False,
            result=None,
            error=f"Acción '{req.action}' denegada por política del tenant",
        )

    # 2. Ejecutar la acción
    try:
        result = _executor.execute(
            action=req.action,
            params=req.params,
            context=TenantContext(tenant=tenant),
        )
        return ExecuteResponse(success=True, result=result)
    except Exception as e:
        return ExecuteResponse(success=False, result=None, error=str(e))
