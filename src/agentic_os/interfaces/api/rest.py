from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ...cognition.planning.intent import Intent
from ...cognition.skills.library import SKILLS
from ...execution.executor import Executor
from ...execution.tools import build_default_registry
from ...infrastructure.config.settings import settings
from ...infrastructure.persistence import get_eventlog_repo
from ...infrastructure.tenancy import Tenant, TenantConfig, TenantContext, TenantRegistry
from ...interfaces.llm.chat import FrontAssistant
from ...interfaces.llm.provider import GeminiProvider, MockLLMProvider
from ...kernel.policy.engine import PolicyEngine
from ...kernel.world.events import Event
from ...orchestration.orchestrator import Orchestrator

app = FastAPI(title="Agentic OS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
EVENTLOG_DIR = DATA_DIR / "eventlog"
POLICIES_DIR = DATA_DIR / "policies"
for d in (CONVERSATIONS_DIR, EVENTLOG_DIR, POLICIES_DIR):
    d.mkdir(parents=True, exist_ok=True)

_event_log = get_eventlog_repo()

if settings.gemini_api_key:
    _llm = GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
else:
    _llm = MockLLMProvider(
        default_response=(
            '{"goal": "responder al usuario", "kind": "reply_to_user", '
            '"entity_id": "n/a", "payload": "", "rationale": "mock sin API key", '
            '"reply_to_user": "Hola! Soy el director (modo mock). Configura GEMINI_API_KEY en .env para respuestas reales."}'
        )
    )

_orchestrator = Orchestrator(log=_event_log, llm=_llm)
_front_assistant = FrontAssistant(
    model_name=settings.gemini_chat_model,
    api_key=settings.gemini_api_key,
    temperature=settings.gemini_temperature,
)

_tasks_lock = threading.Lock()
_background_tasks: Dict[str, Any] = {}

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

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    tenant_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    processing: bool = False
    task_id: Optional[str] = None

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
    tenant_id: str

class StateOut(BaseModel):
    role: str
    event_count: int

@app.get("/")
def root() -> Dict[str, str]:
    return {"app": "Agentic OS", "status": "ok"}

@app.get("/api/state", response_model=StateOut)
def get_state() -> StateOut:
    return StateOut(
        role=_orchestrator.current_role.name,
        event_count=len(_event_log.list_all()),
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
            tenant_id=e.tenant_id,
        )
        for e in _event_log.list_all()
    ]

def _append_message_to_conversation(conv_id: str, role: str, content: str) -> None:
    conv = _load_conversation(conv_id)
    conv["messages"].append({"role": role, "content": content})
    if len(conv["messages"]) == 1:
        conv["title"] = content[:50] + ("..." if len(content) > 50 else "")
    conv["updated_at"] = datetime.utcnow().isoformat()
    _save_conversation(conv)

def _map_kind_to_action(kind: Optional[str]) -> Optional[str]:
    k = (kind or "").lower()
    if any(t in k for t in ("email", "correo", "gmail", "mail")):
        return "gmail_send"
    if "slack" in k:
        return "slack_send"
    if "whatsapp" in k:
        return "whatsapp_send"
    if any(t in k for t in ("calendar", "calendario", "meeting", "reuni", "cita", "evento", "schedule")):
        return "calendar_create_event"
    if any(t in k for t in ("scrape", "scrap", "web", "url")):
        return "web_scrape"
    return None

def _try_execute(action: Optional[str], intent: Intent, tenant_id: str) -> str:
    if action is None:
        return "sin herramienta concreta"
    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        return f"tenant {tenant_id} no registrado"
    context = TenantContext(tenant=tenant)
    try:
        result = _executor.execute(
            action=action,
            params={"rationale": intent.goal, "payload": intent.payload},
            context=context,
        )
        if not result.get("success"):
            return f"rechazada/fallo '{action}': {result.get('error')}"
        return f"ejecutada '{action}'"
    except Exception as e:
        return f"fallo al ejecutar '{action}': {e}"

def _start_orchestration_task(message: str, conversation_id: Optional[str] = None, tenant_id: str = "system") -> str:
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    with _tasks_lock:
        _background_tasks[task_id] = {
            "id": task_id,
            "status": "running",
            "message": message,
            "summary": "",
            "started_at": datetime.utcnow().isoformat(),
        }
    def _run() -> None:
        try:
            intent = _orchestrator.handle_user_message(message, tenant_id=tenant_id)
            note = ""
            if intent.kind and intent.kind != "reply_to_user":
                action = _map_kind_to_action(intent.kind)
                note = _try_execute(action, intent, tenant_id) if action else f"sin tool para '{intent.kind}'"
            summary = f"Intent '{intent.kind}' procesado"
            if note:
                summary += f" · {note}"
            _event_log.append(
                Event(
                    kind="BackgroundProcessingDone",
                    entity_id=task_id,
                    payload={"task_id": task_id, "intent_kind": intent.kind, "note": note},
                    actor_id="orchestrator",
                    tenant_id="system",
                )
            )
            if conversation_id:
                try:
                    _append_message_to_conversation(conversation_id, "assistant", f"⚙️ (back office) {summary} ✅")
                except HTTPException:
                    pass
            with _tasks_lock:
                _background_tasks[task_id].update(status="completed", summary=summary, ended_at=datetime.utcnow().isoformat())
        except Exception as e:
            _event_log.append(
                Event(
                    kind="BackgroundProcessingFailed",
                    entity_id=task_id,
                    payload={"task_id": task_id, "error": str(e)},
                    actor_id="orchestrator",
                    tenant_id="system",
                )
            )
            if conversation_id:
                try:
                    _append_message_to_conversation(conversation_id, "assistant", f"⚠️ (back office) error: {e}")
                except HTTPException:
                    pass
            with _tasks_lock:
                _background_tasks[task_id].update(status="failed", summary=str(e), ended_at=datetime.utcnow().isoformat())
    threading.Thread(target=_run, daemon=True).start()
    return task_id

@app.get("/api/tasks")
def list_tasks() -> List[Dict[str, Any]]:
    with _tasks_lock:
        return [dict(t) for t in _background_tasks.values()]

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
    if req.conversation_id:
        try:
            _append_message_to_conversation(req.conversation_id, "user", message)
        except HTTPException:
            pass
    try:
        reply = _front_assistant.answer(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"El asistente no pudo responder: {e}")
    if req.conversation_id:
        try:
            _append_message_to_conversation(req.conversation_id, "assistant", reply)
        except HTTPException:
            pass
    task_id = _start_orchestration_task(message, conversation_id=req.conversation_id, tenant_id=req.tenant_id or "system")
    return ChatResponse(reply=reply, processing=True, task_id=task_id)

@app.get("/api/conversations", response_model=List[ConversationSummary])
def list_conversations() -> List[ConversationSummary]:
    summaries = []
    for path in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                conv = json.load(f)
            summaries.append(ConversationSummary(id=conv["id"], title=conv["title"], created_at=conv["created_at"], updated_at=conv["updated_at"], message_count=len(conv["messages"])))
        except Exception:
            continue
    summaries.sort(key=lambda c: c.updated_at, reverse=True)
    return summaries

@app.post("/api/conversations", response_model=ConversationOut)
def create_conversation() -> ConversationOut:
    now = datetime.utcnow().isoformat()
    conv = {"id": str(uuid.uuid4()), "title": "Nueva conversación", "created_at": now, "updated_at": now, "messages": []}
    _save_conversation(conv)
    return ConversationOut(**conv)

@app.get("/api/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(conv_id: str) -> ConversationOut:
    conv = _load_conversation(conv_id)
    return ConversationOut(**conv)

@app.post("/api/conversations/{conv_id}/messages", response_model=ConversationOut)
def add_message(conv_id: str, msg: MessageOut) -> ConversationOut:
    conv = _load_conversation(conv_id)
    conv["messages"].append({"role": msg.role, "content": msg.content})
    if len(conv["messages"]) == 1:
        conv["title"] = msg.content[:50] + ("..." if len(msg.content) > 50 else "")
    conv["updated_at"] = datetime.utcnow().isoformat()
    _save_conversation(conv)
    return ConversationOut(**conv)

@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str) -> Dict[str, str]:
    path = _conv_path(conv_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    path.unlink()
    return {"status": "deleted", "id": conv_id}

_tenant_registry = TenantRegistry()
_policy_engine = PolicyEngine()
_executor = Executor(registry=build_default_registry(), policy_engine=_policy_engine)

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

@app.get("/api/tenants", response_model=List[TenantOut])
def list_tenants() -> List[TenantOut]:
    return [TenantOut(id=t.id, name=t.config.name, slug=t.slug, config=t.config.model_dump(), created_at=t.created_at.isoformat()) for t in _tenant_registry.list_all()]

@app.post("/api/tenants", response_model=TenantOut, status_code=201)
def create_tenant(req: TenantCreate) -> TenantOut:
    try:
        tenant = _tenant_registry.create(name=req.name, slug=req.slug, config=req.config or {})
        (EVENTLOG_DIR / f"{tenant.id}.jsonl").touch(exist_ok=True)
        (POLICIES_DIR / f"{tenant.id}.json").touch(exist_ok=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TenantOut(id=tenant.id, name=tenant.config.name, slug=tenant.slug, config=tenant.config.model_dump(), created_at=tenant.created_at.isoformat())

@app.get("/api/tenants/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str) -> TenantOut:
    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return TenantOut(id=tenant.id, name=tenant.config.name, slug=tenant.slug, config=tenant.config.model_dump(), created_at=tenant.created_at.isoformat())

@app.patch("/api/tenants/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: str, req: TenantUpdate) -> TenantOut:
    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    new_config = tenant.config
    if req.name is not None:
        new_config = new_config.model_copy(update={"name": req.name})
    if req.config is not None:
        merged = tenant.config.model_dump()
        merged.update(req.config)
        new_config = TenantConfig(**merged)
    updated = Tenant(id=tenant.id, slug=tenant.slug, config=new_config, created_at=tenant.created_at)
    _tenant_registry.update(updated)
    return TenantOut(id=updated.id, name=updated.config.name, slug=updated.slug, config=updated.config.model_dump(), created_at=updated.created_at.isoformat())

@app.delete("/api/tenants/{tenant_id}")
def delete_tenant(tenant_id: str) -> Dict[str, str]:
    if not _tenant_registry.delete(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return {"status": "deleted", "id": tenant_id}

@app.get("/api/skills", response_model=List[SkillOut])
def list_skills() -> List[SkillOut]:
    return [SkillOut(name=s.name, description=s.description, steps=[step.name for step in s.steps]) for s in SKILLS.values()]

@app.get("/api/tools", response_model=List[ToolOut])
def list_tools() -> List[ToolOut]:
    return [ToolOut(name=t.name) for t in _executor.registry.tools.values()]

@app.post("/api/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest) -> ExecuteResponse:
    tenant = _tenant_registry.get(req.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    if not _policy_engine.is_allowed(tenant_id=tenant.id, action=req.action):
        return ExecuteResponse(success=False, result=None, error=f"Acción '{req.action}' denegada por política del tenant")
    try:
        result = _executor.execute(action=req.action, params=req.params, context=TenantContext(tenant=tenant))
        return ExecuteResponse(success=True, result=result)
    except Exception as e:
        return ExecuteResponse(success=False, result=None, error=str(e))
