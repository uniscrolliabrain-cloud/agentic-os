from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ...cognition.planning.intent import Intent
from ...cognition.skills.library import SKILLS
from ...domains.compiler.entities import TenantBlueprint, TenantIdea, idea_keywords
from ...execution.executor import Executor
from ...execution.tools import build_default_registry
from ...infrastructure.config.settings import settings
from ...infrastructure.persistence import get_eventlog_repo
from ...infrastructure.tenancy import Tenant, TenantConfig, TenantConfigPublic, TenantContext, TenantRegistry
from ...interfaces.llm.chat import FrontAssistant
from ...interfaces.llm.provider import FallbackLLMProvider, GeminiProvider, GroqProvider, MockLLMProvider
from ...kernel.policy.engine import PolicyEngine
from ...kernel.types.time import now_utc
from ...kernel.world.events import Event
from ...orchestration.orchestrator import Orchestrator
from ...orchestration.scheduler import Scheduler

app = FastAPI(title="Agentic OS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict:
    """Liveness probe: el proceso está vivo. No toca dependencias externas."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> JSONResponse:
    """Readiness probe: el EventLog configurado responde de verdad."""
    checks: dict[str, str] = {}
    try:
        get_eventlog_repo().list_all()
        checks["eventlog"] = "ok"
    except Exception as exc:
        checks["eventlog"] = f"error: {exc}"

    healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ok" if healthy else "degraded", "checks": checks},
    )

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
CONVERSATIONS_DIR = DATA_DIR / "conversations"  # legacy (pre multi-tenant); solo lectura
TENANTS_DATA_DIR = DATA_DIR / "tenants"
EVENTLOG_DIR = DATA_DIR / "eventlog"
POLICIES_DIR = DATA_DIR / "policies"
for d in (CONVERSATIONS_DIR, TENANTS_DATA_DIR, EVENTLOG_DIR, POLICIES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- tenant ---
# Resolución del tenant activo por CABECERA (X-Tenant-Id + X-Api-Key simple
# guardada en TenantConfig.credentials, o JWT RS256 de Supabase via
# Authorization: Bearer). Nunca por body.
_TENANT_HEADER = "X-Tenant-Id"
_API_KEY_HEADER = "X-Api-Key"
_ADMIN_KEY_HEADER = "X-Admin-Key"
_AUTH_HEADER = "Authorization"

logger = logging.getLogger(__name__)


class _JWTState(str, Enum):
    NO_TOKEN = "no_token"
    VALID = "valid"
    INVALID = "invalid"


def _verify_supabase_jwt(auth_header: Optional[str]) -> Tuple[Optional[dict], _JWTState]:
    """Verifica JWT RS256 de Supabase. Devuelve (claims, estado)."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, _JWTState.NO_TOKEN
    token = auth_header[7:]
    try:
        from ...infrastructure.auth.jwt_verifier import get_verifier

        claims = get_verifier().verify(token)
        logger.info("Supabase JWT verificado para tenant_id=%s", claims.tenant_id)
        return claims.model_dump(), _JWTState.VALID
    except Exception as exc:
        logger.warning("Supabase JWT inválido/expirado: %s", exc)
        return None, _JWTState.INVALID

# tenant virtual por defecto para peticiones anónimas (back-compat en dev)
_DEFAULT_SCOPE = "system"


def tenant_scope(
    x_tenant_id: Optional[str] = Header(default=None, alias=_TENANT_HEADER),
    x_api_key: Optional[str] = Header(default=None, alias=_API_KEY_HEADER),
    x_admin_key: Optional[str] = Header(default=None, alias=_ADMIN_KEY_HEADER),
    authorization: Optional[str] = Header(default=None, alias=_AUTH_HEADER),
) -> str:
    """Dependency: resuelve y valida el tenant de la petición.

    Prioridades (fail-closed):
      1. Authorization: Bearer <JWT Supabase> → verifica JWT, extrae tenant_id
      2. X-Tenant-Id + X-Api-Key (legacy)
      3. Sin cabecera -> scope "system" (anon)
    """
    claims, jwt_state = _verify_supabase_jwt(authorization)
    if jwt_state == _JWTState.INVALID:
        raise HTTPException(status_code=401, detail="JWT inválido o expirado")
    if claims:
        user_metadata = claims.get("user_metadata")
        if isinstance(user_metadata, dict):
            tenant_id = claims.get("tenant_id") or user_metadata.get("tenant_id")
        else:
            tenant_id = claims.get("tenant_id")
        if tenant_id:
            tenant = _tenant_registry.get(str(tenant_id))
            if tenant is not None:
                return tenant.id
            logger.warning(
                "JWT tenant_id '%s' no registrado; usando scope por defecto",
                tenant_id,
            )
        return _DEFAULT_SCOPE

    if not x_tenant_id:
        if settings.admin_api_key and x_admin_key == settings.admin_api_key:
            return _DEFAULT_SCOPE
        return _DEFAULT_SCOPE
    tenant = _tenant_registry.get(x_tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # 0. Credenciales del tenant expiradas → denegar (fail-closed).
    #    Aplica a cualquier vía de acceso (api key o admin): un tenant con
    #    credenciales vencidas no debe seguir operando.
    _expires_at = tenant.config.credentials_expires_at
    if _expires_at is not None:
        _now = now_utc()
        _expires_at_utc = _expires_at if _expires_at.tzinfo else _expires_at.replace(tzinfo=_now.tzinfo)
        if _now > _expires_at_utc:
            raise HTTPException(
                status_code=401,
                detail="Credenciales del tenant expiradas: contacta al administrador",
            )

    # 1. Admin bypass si coincide X-Admin-Key con settings.admin_api_key
    if settings.admin_api_key and (x_admin_key == settings.admin_api_key or x_api_key == settings.admin_api_key):
        return tenant.id

    expected_key = tenant.config.credentials.get("api_key")
    # 2. Si el tenant tiene API key configurada, DEBE coincidir
    if expected_key:
        if x_api_key != expected_key:
            raise HTTPException(status_code=401, detail="API key inválida para el tenant")
        return tenant.id

    # 3. Si el tenant no tiene API key configurada, rechazar acceso
    if tenant.id != _DEFAULT_SCOPE:
        raise HTTPException(
            status_code=401,
            detail="Autenticación requerida: el tenant requiere API key o X-Admin-Key"
        )
    return tenant.id


def admin_scope(
    x_admin_key: Optional[str] = Header(default=None, alias=_ADMIN_KEY_HEADER),
    x_api_key: Optional[str] = Header(default=None, alias=_API_KEY_HEADER),
) -> bool:
    """Dependency: valida acceso de administrador global (SIN bypass de dev).

    Si ADMIN_API_KEY no está configurada, los endpoints admin fallan con 401
    siempre (fail-closed). DEV_ALLOW_ALL jamás concede acceso admin.
    """
    admin_key = settings.admin_api_key
    if not admin_key:
        raise HTTPException(status_code=401, detail="ADMIN_API_KEY no configurada en el servidor")
    if x_admin_key == admin_key or x_api_key == admin_key:
        return True
    raise HTTPException(status_code=401, detail="Admin API key requerida o inválida")

_event_log = get_eventlog_repo()

def _build_llm():
    primary = None
    fallback = None
    if settings.gemini_api_key:
        try:
            primary = GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        except Exception:
            primary = None
    groq_key = getattr(settings, 'groq_api_key', None) or getattr(settings, 'GROQ_API_KEY', None)
    if groq_key:
        try:
            fallback = GroqProvider(api_key=groq_key, model=getattr(settings, 'groq_model', 'llama-3.3-70b-versatile'))
        except Exception:
            fallback = None
    if primary and fallback:
        return FallbackLLMProvider(primary=primary, fallback=fallback)
    if primary:
        return primary
    if fallback:
        return fallback
    return MockLLMProvider(
        default_response=(
            '{"goal": "responder al usuario", "kind": "reply_to_user", '
            '"entity_id": "n/a", "payload": "", "rationale": "mock sin API key", '
            '"reply_to_user": "Hola! Soy el director (modo mock). Configura GEMINI_API_KEY o GROQ_API_KEY en .env para respuestas reales."}'
        )
    )

_llm = _build_llm()
_orchestrator = Orchestrator(log=_event_log, llm=_llm)
_front_assistant = FrontAssistant(
    model_name=settings.gemini_chat_model,
    api_key=settings.gemini_api_key,
    temperature=settings.gemini_temperature,
)
try:
    _front_assistant.provider = _llm
except Exception:
    pass

_tasks_lock = threading.Lock()
_background_tasks: Dict[str, Any] = {}

def _tenant_conv_dir(tenant_id: str) -> Path:
    """Carpeta de conversaciones de un tenant: data/tenants/{tenant_id}/conversations/."""
    d = TENANTS_DATA_DIR / tenant_id / "conversations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _find_conv_path(conv_id: str, scope: str) -> Optional[Path]:
    """Localiza una conversación: primero en la carpeta del tenant del scope,
    luego en la carpeta legacy plana (solo si su tenant_id coincide con el scope)."""
    scoped = _tenant_conv_dir(scope) / f"{conv_id}.json"
    if scoped.exists():
        return scoped
    legacy = CONVERSATIONS_DIR / f"{conv_id}.json"
    if legacy.exists():
        try:
            with open(legacy, "r", encoding="utf-8") as f:
                conv = json.load(f)
        except Exception:
            return None
        if conv.get("tenant_id", "system") == scope:
            return legacy
    return None


def _load_conversation(conv_id: str, scope: str) -> Dict[str, Any]:
    path = _find_conv_path(conv_id, scope)
    if path is None:
        # 404 genérico: no se filtra si la conversación existe en otro tenant
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_conversation(conv: Dict[str, Any]) -> None:
    tenant_id = conv.get("tenant_id", "system")
    path = _tenant_conv_dir(tenant_id) / f"{conv['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(conv, f, ensure_ascii=False, indent=2)
    # si venía de la carpeta legacy, limpiar el duplicado viejo
    legacy = CONVERSATIONS_DIR / f"{conv['id']}.json"
    if path != legacy and legacy.exists():
        legacy.unlink()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    tenant_id: Optional[str] = None  # DEPRECATED (FASE 4): ignorado; el tenant se resuelve por cabecera X-Tenant-Id

class ChatResponse(BaseModel):
    reply: str
    processing: bool = False
    task_id: Optional[str] = None

class MessageOut(BaseModel):
    role: str
    content: str

class ConversationOut(BaseModel):
    id: str
    tenant_id: str = "system"
    title: str
    created_at: str
    updated_at: str
    messages: List[MessageOut]

class ConversationSummary(BaseModel):
    id: str
    tenant_id: str = "system"
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

@app.get("/api/v1/state", response_model=StateOut)
def get_state(scope: str = Depends(tenant_scope)) -> StateOut:
    return StateOut(
        role=_orchestrator.current_role.name,
        event_count=len(_event_log.list_for_tenant(scope)),
    )

@app.get("/api/v1/events", response_model=List[EventOut])
def get_events(scope: str = Depends(tenant_scope)) -> List[EventOut]:
    """Eventos del tenant resuelto por cabecera — nunca de todos los tenants."""
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
        for e in _event_log.list_for_tenant(scope)
    ]

def _append_message_to_conversation(conv_id: str, role: str, content: str, scope: str) -> None:
    conv = _load_conversation(conv_id, scope)
    conv["messages"].append({"role": role, "content": content})
    if len(conv["messages"]) == 1:
        conv["title"] = content[:50] + ("..." if len(content) > 50 else "")
    conv["updated_at"] = now_utc().isoformat()
    _save_conversation(conv)

# Mapping canónico determinista intent.kind → capability/action del ToolRegistry.
# El LLM (o el router) propone el kind; la decisión de qué acción está permitida
# es SOLO de esta tabla — sin heurísticas de substring.
ACTION_BY_KIND: Dict[str, str] = {
    # email
    "send_email": "gmail_send",
    "send_correo": "gmail_send",
    "email": "gmail_send",
    # slack
    "send_slack": "slack_send",
    "slack": "slack_send",
    # whatsapp
    "send_whatsapp": "whatsapp_send",
    "whatsapp": "whatsapp_send",
    # calendar
    "create_event": "calendar_create_event",
    "create_appointment": "calendar_create_event",
    "schedule_meeting": "calendar_create_event",
    "calendar": "calendar_create_event",
    # web
    "web_scrape": "web_scrape",
    "scrape_web": "web_scrape",
    # repo (FASE 3 del agente compilador: tools read-only del repo)
    "repo_scan": "repo_scan",
    "repo_file_list": "repo_file_list",
    "repo_file_read": "repo_file_read",
    "repo_search": "repo_search",
}

def _map_kind_to_action(kind: Optional[str]) -> Optional[str]:
    """Resuelve el kind canónico de un Intent a su action del Executor.

    Determinista: lookup exacto en ACTION_BY_KIND (normalizado). Un kind
    desconocido → None (no se ejecuta nada; fail-closed).

    Nota (FASE 3): los kinds ``repo_*`` son SOLO lectura y además están
    guardados por la ``Policy`` (``repo.file.read``/``list``/``search`` →
    allow). El mapeo no concede nada por sí mismo: sin regla de policy, el
    Executor no llega a ejecutar la tool.
    """
    return ACTION_BY_KIND.get((kind or "").strip().lower())

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
            tenant_id=tenant.id,
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
            "tenant_id": tenant_id,
            "status": "running",
            "message": message,
            "summary": "",
            "started_at": now_utc().isoformat(),
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
                    tenant_id=tenant_id,
                )
            )
            # Back-office NO inyecta en la conversación del usuario.
            # Solo audita en EventLog (más arriba) para no romper la voz de Laia.
            with _tasks_lock:
                _background_tasks[task_id].update(status="completed", summary=summary, ended_at=now_utc().isoformat())
        except Exception as e:
            _event_log.append(
                Event(
                    kind="BackgroundProcessingFailed",
                    entity_id=task_id,
                    payload={"task_id": task_id, "error": str(e)},
                    actor_id="orchestrator",
                    tenant_id=tenant_id,
                )
            )
            # Back-office NO inyecta en la conversación del usuario.
            # Solo audita en EventLog (más arriba) para no romper la voz de Laia.
            with _tasks_lock:
                _background_tasks[task_id].update(status="failed", summary=str(e), ended_at=now_utc().isoformat())
    threading.Thread(target=_run, daemon=True).start()
    return task_id

@app.get("/api/v1/tasks")
def list_tasks(scope: str = Depends(tenant_scope)) -> List[Dict[str, Any]]:
    with _tasks_lock:
        return [dict(t) for t in _background_tasks.values() if t.get("tenant_id") == scope]

@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest, scope: str = Depends(tenant_scope)) -> ChatResponse:
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
    if req.conversation_id:
        try:
            _append_message_to_conversation(req.conversation_id, "user", message, scope)
        except HTTPException:
            pass
    # Knowledge base por tenant: compartida + carpeta del tenant (si existe)
    tenant_knowledge_dir = TENANTS_DATA_DIR / scope / "knowledge"
    kb_arg = tenant_knowledge_dir if scope != _DEFAULT_SCOPE else None
    try:
        reply = _front_assistant.answer(message, tenant_knowledge_dir=kb_arg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"El asistente no pudo responder: {e}")
    if req.conversation_id:
        try:
            _append_message_to_conversation(req.conversation_id, "assistant", reply, scope)
        except HTTPException:
            pass
    task_id = _start_orchestration_task(message, conversation_id=req.conversation_id, tenant_id=scope)
    return ChatResponse(reply=reply, processing=True, task_id=task_id)

def _iter_conversation_paths(scope: str):
    """Conversaciones visibles para un tenant: su carpeta + legacy con su tenant_id."""
    for path in _tenant_conv_dir(scope).glob("*.json"):
        yield path
    for path in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                conv = json.load(f)
        except Exception:
            continue
        if conv.get("tenant_id", "system") == scope:
            yield path

@app.get("/api/v1/conversations", response_model=List[ConversationSummary])
def list_conversations(scope: str = Depends(tenant_scope)) -> List[ConversationSummary]:
    summaries = []
    seen = set()
    for path in _iter_conversation_paths(scope):
        try:
            with open(path, "r", encoding="utf-8") as f:
                conv = json.load(f)
            if conv["id"] in seen:
                continue
            seen.add(conv["id"])
            summaries.append(ConversationSummary(
                id=conv["id"], title=conv["title"], created_at=conv["created_at"],
                updated_at=conv["updated_at"], message_count=len(conv["messages"]),
                tenant_id=conv.get("tenant_id", "system"),
            ))
        except Exception:
            continue
    summaries.sort(key=lambda c: c.updated_at, reverse=True)
    return summaries

@app.post("/api/v1/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(scope: str = Depends(tenant_scope)) -> ConversationOut:
    now = now_utc().isoformat()
    conv = {"id": str(uuid.uuid4()), "tenant_id": scope, "title": "Nueva conversación", "created_at": now, "updated_at": now, "messages": []}
    _save_conversation(conv)
    return ConversationOut(**conv)

@app.get("/api/v1/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(conv_id: str, scope: str = Depends(tenant_scope)) -> ConversationOut:
    conv = _load_conversation(conv_id, scope)
    return ConversationOut(**conv)

@app.post("/api/v1/conversations/{conv_id}/messages", response_model=ConversationOut)
def add_message(conv_id: str, msg: MessageOut, scope: str = Depends(tenant_scope)) -> ConversationOut:
    conv = _load_conversation(conv_id, scope)
    conv["messages"].append({"role": msg.role, "content": msg.content})
    if len(conv["messages"]) == 1:
        conv["title"] = msg.content[:50] + ("..." if len(msg.content) > 50 else "")
    conv["updated_at"] = now_utc().isoformat()
    _save_conversation(conv)
    return ConversationOut(**conv)

@app.delete("/api/v1/conversations/{conv_id}")
def delete_conversation(conv_id: str, scope: str = Depends(tenant_scope)) -> Dict[str, str]:
    path = _find_conv_path(conv_id, scope)
    if path is None:
        # 404 genérico: no revela si existe en otro tenant
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    path.unlink()
    return {"status": "deleted", "id": conv_id}

_tenant_registry = TenantRegistry()
_policy_engine = PolicyEngine()

# FASE 6: scheduler real por tenant. El trigger ejecuta el pipeline con el
# registry/executor del módulo (resuelto en runtime, no en import).
_scheduler = Scheduler(data_dir=DATA_DIR, event_log=_event_log, on_trigger=None)

def _run_scheduled_pipeline(
    pipeline_id,
    tenant_id,
    correlation_id=None,
    command_id=None,
):
    """Callback del scheduler: si hay Temporal, encola workflow. Si no, fallback directo."""
    import os
    import asyncio

    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant no encontrado",
        )

    # Intenta via Temporal si hay env var
    temporal_host = os.getenv("TEMPORAL_HOST")
    if temporal_host:
        try:
            from agentic_os.orchestration.temporal.client import start_pipeline

            async def _start():
                return await start_pipeline(
                    pipeline_id=pipeline_id,
                    tenant_id=tenant_id,
                    params={"correlation_id": correlation_id, "command_id": command_id}
                )

            # Scheduler corre en thread, necesita nuevo loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Estamos en thread de APScheduler, no hay loop corriendo
                    wf_id = asyncio.run(_start())
                else:
                    wf_id = loop.run_until_complete(_start())
            except RuntimeError:
                wf_id = asyncio.run(_start())

            _event_log.append(
                Event(
                    kind="ScheduledPipelineEnqueued",
                    entity_id=f"pipeline://{pipeline_id}",
                    tenant_id=tenant_id,
                    actor_id="scheduler",
                    payload={
                        "pipeline_id": pipeline_id,
                        "workflow_id": wf_id,
                        "via": "temporal",
                    },
                    correlation_id=correlation_id,
                    command_id=command_id,
                )
            )
            return {"status": "ENQUEUED", "workflow_id": wf_id, "via": "temporal"}

        except Exception as e:
            # Fail-open a directo si Temporal no responde, pero audita
            _event_log.append(
                Event(
                    kind="TemporalEnqueueFailedFallback",
                    entity_id=f"pipeline://{pipeline_id}",
                    tenant_id=tenant_id,
                    actor_id="scheduler",
                    payload={"error": str(e)[:300], "fallback": "direct"},
                    correlation_id=correlation_id,
                    command_id=command_id,
                )
            )

    # Fallback directo (sin Temporal / dev local)
    result = _orchestrator.handle_pipeline(
        pipeline_id=pipeline_id,
        tenant_id=tenant_id,
        executor=_executor,
        registry=_executor.registry,
        correlation_id=correlation_id,
        command_id=command_id,
    )

    _event_log.append(
        Event(
            kind="ScheduledPipelineFinished",
            entity_id=f"pipeline://{pipeline_id}",
            tenant_id=tenant_id,
            actor_id="scheduler",
            payload={
                "pipeline_id": pipeline_id,
                "status": result.get("status"),
                "via": "direct",
            },
            correlation_id=correlation_id,
            command_id=command_id,
        )
    )

    return result

_scheduler.on_trigger = _run_scheduled_pipeline
_executor = Executor(registry=build_default_registry(scheduler=_scheduler), policy_engine=_policy_engine, event_log=_event_log)

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
    tenant_id: Optional[str] = None  # DEPRECATED (FASE 4): ignorado; el tenant se resuelve por cabecera X-Tenant-Id
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

@app.get("/api/v1/tenants", response_model=List[TenantOut])
def list_tenants(_: bool = Depends(admin_scope)) -> List[TenantOut]:
    return [TenantOut(id=t.id, name=t.config.name, slug=t.slug, config=TenantConfigPublic.from_config(t.config).model_dump(), created_at=t.created_at.isoformat()) for t in _tenant_registry.list_all()]

@app.post("/api/v1/tenants", response_model=TenantOut, status_code=201)
def create_tenant(req: TenantCreate, _: bool = Depends(admin_scope)) -> TenantOut:
    try:
        tenant = _tenant_registry.create(name=req.name, slug=req.slug, config=req.config or {})
        (EVENTLOG_DIR / f"{tenant.id}.jsonl").touch(exist_ok=True)
        (POLICIES_DIR / f"{tenant.id}.json").touch(exist_ok=True)
        # FASE 4: espacios de datos del tenant (conversaciones + knowledge)
        _tenant_conv_dir(tenant.id)
        (TENANTS_DATA_DIR / tenant.id / "knowledge").mkdir(parents=True, exist_ok=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TenantOut(
        id=tenant.id,
        name=tenant.config.name,
        slug=tenant.slug,
        config=TenantConfigPublic.from_config(tenant.config).model_dump(),
        created_at=tenant.created_at.isoformat(),
    )

@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, _: bool = Depends(admin_scope)) -> TenantOut:
    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return TenantOut(id=tenant.id, name=tenant.config.name, slug=tenant.slug, config=TenantConfigPublic.from_config(tenant.config).model_dump(), created_at=tenant.created_at.isoformat())

@app.patch("/api/v1/tenants/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: str, req: TenantUpdate, _: bool = Depends(admin_scope)) -> TenantOut:
    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    new_config = tenant.config
    if req.name is not None:
        new_config = new_config.model_copy(update={"name": req.name})
    if req.config is not None:
        # Sanitizar para evitar sobreescritura arbitraria de data_dir a rutas peligrosas
        sanitized_cfg = dict(req.config)
        sanitized_cfg.pop("data_dir", None)
        merged = tenant.config.model_dump()
        merged.update(sanitized_cfg)
        new_config = TenantConfig(**merged)
    updated = Tenant(id=tenant.id, slug=tenant.slug, config=new_config, created_at=tenant.created_at)
    _tenant_registry.update(updated)
    return TenantOut(id=updated.id, name=updated.config.name, slug=updated.slug, config=TenantConfigPublic.from_config(updated.config).model_dump(), created_at=updated.created_at.isoformat())

@app.delete("/api/v1/tenants/{tenant_id}")
def delete_tenant(tenant_id: str, _: bool = Depends(admin_scope)) -> Dict[str, str]:
    if not _tenant_registry.delete(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return {"status": "deleted", "id": tenant_id}

@app.get("/api/v1/skills", response_model=List[SkillOut])
def list_skills() -> List[SkillOut]:
    items = SKILLS.values() if hasattr(SKILLS, "values") else SKILLS
    return [SkillOut(name=s.name, description=s.description, steps=[step.name for step in s.steps]) for s in items]

@app.get("/api/v1/tools", response_model=List[ToolOut])
def list_tools() -> List[ToolOut]:
    return [ToolOut(name=t.name) for t in _executor.registry.tools.values()]

@app.post("/api/v1/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest, scope: str = Depends(tenant_scope)) -> ExecuteResponse:
    # FASE 4: el tenant SIEMPRE viene de la cabecera, nunca del body
    tenant = _tenant_registry.get(scope)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    try:
        result = _executor.execute(
            action=req.action,
            params=req.params,
            context=TenantContext(tenant=tenant),
            tenant_id=tenant.id,
        )
        if not result.get("success", False):
            return ExecuteResponse(
                success=False,
                result=None,
                error=result.get("error", f"Acción '{req.action}' denegada o fallida"),
            )
        return ExecuteResponse(success=True, result=result.get("output", result))
    except Exception:
        return ExecuteResponse(success=False, result=None, error="execution failed")


# ---------------------------------------------------------------- FASE 6 ----
# Scheduler (jobs por tenant) y artefactos/drafts por tenant.

class ScheduleCreate(BaseModel):
    pipeline_id: str
    interval_minutes: Optional[int] = None
    hour: Optional[int] = None


class ScheduleOut(BaseModel):
    id: str
    tenant_id: str
    pipeline_id: str
    kind: str
    hour: Optional[int] = None
    minutes: Optional[int] = None


@app.get("/api/v1/schedules", response_model=List[ScheduleOut])
def list_schedules(scope: str = Depends(tenant_scope)) -> List[ScheduleOut]:
    """Schedules del tenant de la petición — nunca de otros tenants."""
    return [
        ScheduleOut(
            id=s["id"],
            tenant_id=s["tenant_id"],
            pipeline_id=s["pipeline_id"],
            kind=s["kind"],
            hour=s.get("hour"),
            minutes=s.get("minutes"),
        )
        for s in _scheduler.list_schedules(scope)
    ]


@app.post("/api/v1/schedules", response_model=ScheduleOut, status_code=201)
def create_schedule(req: ScheduleCreate, scope: str = Depends(tenant_scope)) -> ScheduleOut:
    if not req.pipeline_id:
        raise HTTPException(status_code=400, detail="pipeline_id es obligatorio")
    if (req.interval_minutes is None) == (req.hour is None):
        raise HTTPException(status_code=400, detail="indica interval_minutes o hour (no ambos/ninguno)")
    if req.hour is not None:
        record = _scheduler.schedule_daily(scope, req.pipeline_id, int(req.hour))
    else:
        record = _scheduler.schedule_interval(scope, req.pipeline_id, int(req.interval_minutes or 0))
    return ScheduleOut(
        id=record["id"], tenant_id=record["tenant_id"], pipeline_id=record["pipeline_id"],
        kind=record["kind"], hour=record.get("hour"), minutes=record.get("minutes"),
    )


@app.delete("/api/v1/schedules/{schedule_id}")
def delete_schedule(schedule_id: str, scope: str = Depends(tenant_scope)) -> Dict[str, Any]:
    if not _scheduler.remove_schedule(scope, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule no encontrado")
    return {"status": "deleted", "id": schedule_id}


@app.get("/api/v1/drafts")
def list_drafts(scope: str = Depends(tenant_scope)) -> List[Dict[str, Any]]:
    """Drafts de email del tenant (creados por pipelines SIMULADOS)."""
    drafts_dir = TENANTS_DATA_DIR / scope / "drafts"
    drafts: List[Dict[str, Any]] = []
    if drafts_dir.exists():
        for p in sorted(drafts_dir.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    drafts.append(json.load(fh))
            except (OSError, json.JSONDecodeError):
                continue
    return drafts


@app.get("/api/v1/artifacts")
def list_artifacts(scope: str = Depends(tenant_scope)) -> List[Dict[str, Any]]:
    """Lista artefactos del tenant (pipeline daily_social etc)."""
    artifacts_dir = TENANTS_DATA_DIR / scope / "artifacts"
    out: List[Dict[str, Any]] = []
    if artifacts_dir.exists():
        for p in sorted(artifacts_dir.rglob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    out.append(json.load(fh))
            except (OSError, json.JSONDecodeError):
                continue
    return out


@app.get("/api/v1/artifacts/{tenant_id}/{artifact_id}")
def get_artifact(tenant_id: str, artifact_id: str, scope: str = Depends(tenant_scope)) -> Dict[str, Any]:
    """Artefacto de un pipeline. FASE 4: el tenant del path debe coincidir con el scope."""
    if tenant_id != scope:
        raise HTTPException(status_code=403, detail="No autorizado para este tenant")
    artifacts_dir = TENANTS_DATA_DIR / scope / "artifacts"
    for p in artifacts_dir.glob(f"*/*.json"):
        if p.stem == artifact_id:
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
    raise HTTPException(status_code=404, detail="Artefacto no encontrado")

# ---------------------------------------------------------------- COGNITION ----
# Memoria persistente por (tenant, agente) - audit paso 3

try:
    from ...cognition.memory import CognitionRegistry
    _cognition_registry = CognitionRegistry()
except Exception:
    _cognition_registry = None


@app.get("/api/v1/agents/{agent_id}/cognition")
def get_agent_cognition(agent_id: str, scope: str = Depends(tenant_scope)) -> Dict[str, Any]:
    """Vista de las 4 memorias del agente, aisladas por tenant de cabecera.

    - tenant viene de X-Tenant-Id / JWT (tenant_scope)
    - agent_id se valida contra regex del CognitionStore (fail-closed)
    - Nunca expone memoria de otro tenant
    """
    if _cognition_registry is None:
        raise HTTPException(status_code=503, detail="CognitionStore no disponible")
    try:
        store = _cognition_registry.for_agent(scope, agent_id)
        return store.snapshot()
    except Exception as e:
        # Validacion de id invalido -> 400, resto -> 500
        msg = str(e)
        if "inválido" in msg or "invalido" in msg.lower():
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail=f"Error leyendo cognicion: {msg[:300]}")


@app.get("/api/v1/agents/{agent_id}/cognition/context")
def get_agent_cognition_context(agent_id: str, q: str = "", k: int = 5, scope: str = Depends(tenant_scope)) -> Dict[str, Any]:
    """Contexto consolidado para inyeccion en prompt (working+episodic+semantic+procedural)."""
    if _cognition_registry is None:
        raise HTTPException(status_code=503, detail="CognitionStore no disponible")
    try:
        store = _cognition_registry.for_agent(scope, agent_id)
        return store.context(query=q, k=k)
    except Exception as e:
        msg = str(e)
        if "inválido" in msg or "invalido" in msg.lower():
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail=f"Error leyendo contexto: {msg[:300]}")


# ---------------------------------------------------------------- COMPILER ----
# Fase 2 de PLAN_CLINE_AGENTE_COMPILADOR.md: MVP del chat del tenant
# `agentic-compiler`. El compilador trabaja en **modo PLAN**: lee y propone,
# nunca escribe. Toda capability pasa por la Policy antes de darse por buena y
# el unico camino a escritura es `repo.file.write` resuelto por Gate 1 humano.

_COMPILER_SLUG = "agentic-compiler"
_COMPILER_MODE = "plan"
_COMPILER_WRITE_CAPABILITY = "repo.file.write"
_COMPILER_BLUEPRINT_CAPABILITY = "codegen.blueprint.generate"

# Roles del operador del compilador (TenantContext usa ["director"] por defecto).
# Sin rol, la regla de `repo.file.write` no casa y la policy cae en deny.
_COMPILER_OPERATOR_ROLES: Tuple[str, ...] = ("director",)

# Fases que todo blueprint propone (esqueleto estable y comparable entre ideas).
_COMPILER_PHASES: Tuple[str, ...] = (
    "Fase 1 - alta del tenant (registro, policy minima, entidades)",
    "Fase 2 - chat del tenant en modo PLAN",
    "Fase 3 - tools y capacidades del compilador",
    "Fase 4 - pipelines de compilacion",
    "Fase 5 - policy completa con path-guard",
    "Fase 6 - knowledge base del tenant nuevo",
    "Fase 7 - sandbox y CI del codigo generado",
)

# Catalogo deterministico: (keywords que activan, dominio, slug semilla,
# entidades, capabilities). El LLM puede proponer, pero sin API key el
# esqueleto sale de aqui, de modo que el modo offline es util y reproducible
# (nunca una respuesta vacia).
_COMPILER_CATALOG: Tuple[
    Tuple[Tuple[str, ...], str, str, Tuple[str, ...], Tuple[str, ...]], ...
] = (
    (
        ("dental", "clinica", "clinic", "dentista", "odontolog", "podolog"),
        "clinic",
        "clinica",
        (
            "clinic.patient",
            "clinic.appointment",
            "clinic.treatment",
            "clinic.invoice",
        ),
        (
            "calendar.event.create",
            "calendar.event.read",
            "crm.contact.create",
            "crm.contact.read",
            "whatsapp.message.send",
            "payment.link.create",
        ),
    ),
    (
        ("agencia", "marketing", "seo", "web", "leads", "publicidad"),
        "agencia",
        "agencia-digital",
        (
            "agencia.client",
            "agencia.lead",
            "agencia.deal",
            "agencia.quote",
        ),
        (
            "web.seo.audit",
            "web.seo.keywords",
            "crm.lead.create",
            "crm.deal.create",
            "social.post.publish",
            "payment.link.create",
        ),
    ),
    (
        ("tienda", "ecommerce", "e-commerce", "shop", "pedidos", "ventas"),
        "shop",
        "tienda-online",
        (
            "shop.product",
            "shop.order",
            "shop.customer",
            "shop.invoice",
        ),
        (
            "crm.contact.create",
            "crm.contact.read",
            "payment.checkout.create",
            "whatsapp.message.send",
            "calendar.event.create",
        ),
    ),
)

# Familia por defecto si ninguna keyword del catalogo casa:
# (dominio, slug semilla, entidades, capabilities).
_COMPILER_DEFAULT_FAMILY: Tuple[str, str, Tuple[str, ...], Tuple[str, ...]] = (
    "generic",
    "tenant-nuevo",
    ("core.entity", "core.record", "core.task"),
    ("crm.contact.create", "crm.contact.read", "calendar.event.create"),
)

# Palabras de relleno que no aportan al nombre visible del tenant propuesto.
_COMPILER_GENERIC_WORDS: frozenset = frozenset(
    {
        "agentico", "agentic", "sistema", "system", "gestion", "gestionar",
        "idea", "proyecto", "empresa", "negocio", "plataforma", "quiero",
    }
)

# Intents de ESCRITURA/PUBLICACION que el modo PLAN descarta ANTES de la policy
# (el LLM puede proponerlos; el compilador jamas los ejecuta sin Gate 1).
_COMPILER_WRITE_INTENTS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    (
        "repo.file.write",
        ("escribe", "escribir", "crea el fichero", "crear el fichero", "modifica",
         "edita el fichero", "aplica los cambios", "aplicalo", "aplícalo"),
    ),
    ("git.commit", ("haz commit", "commitea", "commitear", "haz el commit")),
    ("git.push", ("haz push", "haz el push", "sube la rama", "sube el codigo")),
    ("git.pr.create", ("abre el pr", "abre una pr", "haz el pr", "pull request")),
)

# Segmentos de capability sin efectos externos: se sugieren como `allow`.
_COMPILER_READONLY_SUFFIXES: Tuple[str, ...] = (
    ".read", ".list", ".search", ".stat", ".audit", ".keywords",
)

# Segmentos que SIEMPRE requieren aprobacion humana (invariante del kernel).
_COMPILER_APPROVAL_SEGMENTS: frozenset = frozenset({"delete", "publish", "push", "create", "send"})


class CompilerChatRequest(BaseModel):
    """Peticion de chat del compilador (nunca trae el tenant: va por cabecera)."""

    message: str
    conversation_id: Optional[str] = None
    tenant_id: Optional[str] = None  # DEPRECATED: el tenant se resuelve por cabecera


class CompilerChatResponse(BaseModel):
    """Respuesta en modo PLAN: propuesta + gate, jamas una ejecucion."""

    reply: str
    mode: str = _COMPILER_MODE
    tenant_id: str
    provider: str = "offline"
    blueprint: Optional[Dict[str, Any]] = None
    gate: Optional[str] = None
    write_decision: Optional[str] = None
    discarded_intents: List[str] = []
    conversation_id: Optional[str] = None
    event_id: Optional[str] = None


# Persona embebida: se usa si el .md del tenant no esta disponible (fail-safe,
# la conversacion nunca se queda sin system instruction).
_COMPILER_PERSONA_FALLBACK = (
    "Eres el arquitecto-compilador de tenants de Agentic OS. Tu producto son "
    "tenants nuevos, no software. El LLM solo propone; la Policy decide; el "
    "Executor ejecuta; el EventLog audita. Estas en modo PLAN: lees y consultas "
    "el repo, pero NO escribes nada. Devuelves un TenantBlueprint propuesto "
    "(entidades, capabilities, policy sugerida, fases) y preguntas por el Gate 1. "
    "Nunca tocas src/agentic_os/kernel/**, docs/INVARIANTS.md ni main."
)


def _compiler_persona() -> str:
    """System instruction del compilador: su .md de knowledge o el fallback."""
    path = TENANTS_DATA_DIR / _COMPILER_SLUG / "knowledge" / "system_compiler.md"
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return _COMPILER_PERSONA_FALLBACK
    return text or _COMPILER_PERSONA_FALLBACK


# Caracteres permitidos en identificadores que acaban en nombre de fichero.
_COMPILER_ID_CHARS: frozenset = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)


def _compiler_safe_id(value: str) -> bool:
    """True si el identificador es seguro como nombre de fichero.

    Se comprueba caracter a caracter (sin regex ni rutas): nada de separadores,
    puntos ni secuencias de traversal.
    """
    if not value or len(value) > 64 or value in (".", ".."):
        return False
    return all(ch in _COMPILER_ID_CHARS for ch in value)


def _compiler_chat_dir(scope: str) -> Path:
    """Conversaciones del compilador: data/tenants/{scope}/chat/ (aisladas)."""
    d = TENANTS_DATA_DIR / scope / "chat"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _compiler_chat_path(scope: str, conv_id: str) -> Path:
    """Ruta de una conversacion, rechazando ids con path traversal (fail-closed)."""
    if not _compiler_safe_id(conv_id):
        raise HTTPException(status_code=400, detail="conversation_id invalido")
    return _compiler_chat_dir(scope) / f"{conv_id}.json"


def _compiler_load_conversation(scope: str, conv_id: str) -> Dict[str, Any]:
    path = _compiler_chat_path(scope, conv_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")


def _compiler_save_conversation(scope: str, conv: Dict[str, Any]) -> None:
    conv["updated_at"] = now_utc().isoformat()
    path = _compiler_chat_path(scope, conv["id"])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(conv, fh, ensure_ascii=False, indent=2)


def _compiler_suggest_effect(capability: str) -> str:
    """Efecto SUGERIDO para una capability del tenant nuevo (determinista).

    Es una propuesta de policy, no una decision: el tenant nuevo resolvera la
    suya. Las lecturas se sugieren `allow`; lo que publica, borra o sale al
    exterior exige aprobacion humana (invariante del kernel); el resto, deny.
    """
    cap = (capability or "").strip().lower()
    if not cap:
        return "deny"
    segments = {seg for seg in cap.split(".") if seg}
    if segments & _COMPILER_APPROVAL_SEGMENTS:
        return "require_approval"
    if cap.endswith(_COMPILER_READONLY_SUFFIXES):
        return "allow"
    return "require_approval"


def _compiler_discarded_intents(message: str) -> List[str]:
    """Intents de escritura/publicacion que el modo PLAN descarta sin ejecutar."""
    text = (message or "").lower()
    return [
        kind
        for kind, triggers in _COMPILER_WRITE_INTENTS
        if any(trigger in text for trigger in triggers)
    ]


def _compiler_llm() -> Optional[Any]:
    """Provider para el compilador: solo si hay LLM real.

    El Mock del director responde con el JSON de Intent del orquestador, que no
    sirve como arquitecto; en ese caso se devuelve None y el endpoint usa el
    esqueleto offline determinista (el compilador funciona sin API key).
    """
    if isinstance(_llm, MockLLMProvider):
        return None
    return _llm


def _compiler_catalog_match(
    idea: str,
) -> Tuple[str, str, Tuple[str, ...], Tuple[str, ...]]:
    """Familia de negocio mas probable de la idea (determinista, sin LLM).

    Devuelve ``(dominio, slug semilla, entidades, capabilities)``.
    """
    tokens = set(idea_keywords(idea, limit=60))
    for keywords, domain, slug, entities, capabilities in _COMPILER_CATALOG:
        if tokens & set(keywords):
            return domain, slug, entities, capabilities
    return _COMPILER_DEFAULT_FAMILY


def _compiler_tenant_name(idea: str, slug_seed: str) -> str:
    """Nombre visible del tenant propuesto (determinista, sin LLM).

    Parte del slug semilla de la familia y le añade la primera palabra
    significativa de la idea («clinica» + «dental» -> «Clinica Dental»).
    """
    base = slug_seed.replace("-", " ").capitalize()
    head = slug_seed.split("-")[0]
    words = [
        w
        for w in idea_keywords(idea, limit=12)
        if w not in _COMPILER_GENERIC_WORDS and w != head
    ]
    if words:
        return f"{base} {words[0].capitalize()}"
    return base


def _compiler_build_blueprint(
    idea_nl: str,
    tenant_id: str,
    *,
    entities: Optional[List[str]] = None,
    capabilities: Optional[List[str]] = None,
    domain: str = "generic",
    tenant_name: Optional[str] = None,
    slug: Optional[str] = None,
    mode: str = _COMPILER_MODE,
) -> TenantBlueprint:
    """Construye el TenantBlueprint estricto (fuente unica de verdad).

    La entidad valida fail-closed: si algo no cuadra, la construccion lanza y
    el endpoint responde con el esqueleto offline en lugar de inventar datos.
    """
    if entities is None or capabilities is None:
        family_domain, family_slug, family_entities, family_capabilities = (
            _compiler_catalog_match(idea_nl)
        )
        if entities is None:
            entities = list(family_entities)
        if capabilities is None:
            capabilities = list(family_capabilities)
        if slug is None:
            slug = family_slug
        if domain == "generic":
            domain = family_domain
    idea = TenantIdea(tenant_id=tenant_id, idea_nl=idea_nl, domain_hint=domain)
    slug = slug or idea.slug_hint or "tenant-nuevo"
    return TenantBlueprint(
        tenant_id=tenant_id,
        idea_id=idea.id,
        idea_nl=idea.idea_normalizada,
        slug=slug,
        tenant_name=tenant_name or _compiler_tenant_name(idea_nl, slug),
        domain=domain,
        entities=list(entities),
        capabilities=list(capabilities),
        policy={c: _compiler_suggest_effect(c) for c in capabilities},
        phases=list(_COMPILER_PHASES),
        mode=mode,
    )


def _compiler_offline_blueprint(idea_nl: str, tenant_id: str) -> TenantBlueprint:
    """Esqueleto deterministico sin LLM: el compilador funciona sin API key."""
    return _compiler_build_blueprint(idea_nl, tenant_id)


# Contrato de salida del LLM: JSON estricto, sin markdown ni adornos.
_COMPILER_LLM_CONTRACT = (
    "Responde EXCLUSIVAMENTE con un objeto JSON con las claves: "
    '"slug" (minusculas y guiones), "tenant_name", "domain", "entities" (lista), '
    '"capabilities" (lista). Sin markdown, sin explicaciones, sin texto adicional.'
)


def _compiler_llm_blueprint(llm: Any, idea_nl: str, tenant_id: str) -> TenantBlueprint:
    """Blueprint propuesto por el LLM real, normalizado y validado.

    El LLM propone; el kernel valida. Una salida que no valide se descarta en
    el caller y se cae al esqueleto offline (fail-closed, nunca basura).
    """
    raw = llm.generate(
        prompt=idea_nl,
        system_instruction=_compiler_persona() + "\n\n" + _COMPILER_LLM_CONTRACT,
    )
    data = json.loads(raw or "{}")
    if not isinstance(data, dict):
        raise ValueError("el LLM no devolvio un objeto JSON")
    entities = [str(e).strip() for e in (data.get("entities") or []) if str(e).strip()]
    capabilities = [
        str(c).strip() for c in (data.get("capabilities") or []) if str(c).strip()
    ]
    if not entities or not capabilities:
        raise ValueError("el LLM no propuso entidades/capabilities utilizables")
    return _compiler_build_blueprint(
        idea_nl,
        tenant_id,
        entities=entities,
        capabilities=capabilities,
        domain=str(data.get("domain") or "generic").strip() or "generic",
        tenant_name=str(data.get("tenant_name") or "").strip() or None,
        slug=str(data.get("slug") or "").strip() or None,
    )


def _compiler_reply(
    blueprint: TenantBlueprint,
    *,
    provider: str,
    discarded: List[str],
    write_decision: str,
) -> str:
    """Respuesta en modo PLAN: esqueleto del blueprint + pregunta de Gate 1."""
    lines: List[str] = []
    if discarded:
        lines.append(
            "Modo PLAN: descartados sin ejecutar los intents de escritura ["
            + ", ".join(discarded)
            + "]. Nada se ha escrito."
        )
        lines.append("")
    lines.append(f"Idea recibida: {blueprint.idea_nl}")
    lines.append("")
    lines.append(f"Slug propuesto: {blueprint.slug} · dominio: {blueprint.domain}")
    lines.append("")
    lines.append("Entidades propuestas:")
    lines.extend(f"  - {entity}" for entity in blueprint.entities)
    lines.append("")
    lines.append("Capabilities propuestas y efecto sugerido:")
    lines.extend(
        f"  - {cap} -> {blueprint.policy.get(cap, 'deny')}"
        for cap in blueprint.capabilities
    )
    lines.append("")
    lines.append("Fases propuestas:")
    lines.extend(f"  - {phase}" for phase in blueprint.phases)
    lines.append("")
    lines.append("Zonas del repo que tocaria (solo lectura hasta Gate 1):")
    lines.append(f"  - src/agentic_os/domains/{blueprint.slug}/")
    lines.append(f"  - data/tenants/{blueprint.slug}/")
    lines.append(f"  - data/policies/{blueprint.slug}.json")
    lines.append(f"  - tests/tenants/test_{blueprint.slug.replace('-', '_')}.py")
    lines.append("")
    lines.append(
        "Preguntas para cerrar el blueprint: 1) que entidades faltan, "
        "2) que integraciones reales usara el cliente, "
        "3) quien resuelve el Gate 1."
    )
    lines.append("")
    lines.append(
        f"Gate 1: PENDIENTE (repo.file.write -> {write_decision}). "
        "Sin Gate 1 y rol director no se escribe nada."
    )
    lines.append(f"Proveedor: {provider}")
    return "\n".join(lines)


@app.post("/api/v1/tenants/{tenant}/chat", response_model=CompilerChatResponse)
def compiler_chat(
    tenant: str,
    req: CompilerChatRequest,
    scope: str = Depends(tenant_scope),
) -> CompilerChatResponse:
    """Chat del tenant compilador (Fase 2): modo PLAN, sin escribir nada.

    Aislamiento: el tenant del path DEBE coincidir con el resuelto por cabecera
    (X-Tenant-Id / JWT / X-Admin-Key). Sin coincidencia -> 403: nunca se
    conversa con el compilador en nombre de otro tenant.
    """
    requested = _tenant_registry.get(tenant)
    if requested is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    # `tenant_scope` resuelve el tenant de la cabecera y devuelve su id interno
    # (o el slug): se aceptan ambos y se canoniza al slug, que es la clave
    # estable del registry y del data_dir del compilador.
    if scope not in (requested.id, requested.slug):
        raise HTTPException(status_code=403, detail="No autorizado para este tenant")
    if requested.slug != _COMPILER_SLUG:
        raise HTTPException(
            status_code=404,
            detail="Chat de tenant no disponible para este tenant",
        )
    tenant_key = requested.slug
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacio")

    # 1. Policy: generar el blueprint debe estar PERMITIDO (fail-closed).
    decision = _policy_engine.decide(
        tenant_key,
        _COMPILER_BLUEPRINT_CAPABILITY,
        roles=list(_COMPILER_OPERATOR_ROLES),
    )
    if decision.effect != "allow":
        raise HTTPException(
            status_code=403,
            detail=(
                f"policy deniega '{_COMPILER_BLUEPRINT_CAPABILITY}': "
                f"{decision.reason}"
            ),
        )

    # 2. Gate 1: el unico camino a escritura es `require_approval` resuelto.
    write_decision = _policy_engine.decide(
        tenant_key,
        _COMPILER_WRITE_CAPABILITY,
        roles=list(_COMPILER_OPERATOR_ROLES),
    )

    # 3. Blueprint: LLM real si existe; si no (o si su salida no valida), el
    #    esqueleto offline determinista. El compilador nunca se queda mudo.
    provider_name = "offline"
    blueprint: Optional[TenantBlueprint] = None
    llm = _compiler_llm()
    if llm is not None:
        try:
            blueprint = _compiler_llm_blueprint(llm, message, tenant_key)
            provider_name = type(llm).__name__
        except Exception as exc:
            blueprint = None
            logger.warning("compilador: salida LLM no valida, uso offline: %s", exc)
    if blueprint is None:
        blueprint = _compiler_offline_blueprint(message, tenant_key)

    # 4. Modo PLAN: los intents de escritura se descartan ANTES de la policy.
    discarded = _compiler_discarded_intents(message)

    # 5. Persistencia aislada en data/tenants/{tenant}/chat/.
    conv_id = req.conversation_id
    if conv_id:
        conv = _compiler_load_conversation(tenant_key, conv_id)
    else:
        conv_id = f"chat_{uuid.uuid4().hex[:12]}"
        now = now_utc().isoformat()
        conv = {
            "id": conv_id,
            "tenant_id": tenant_key,
            "mode": _COMPILER_MODE,
            "title": message[:50] + ("..." if len(message) > 50 else ""),
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
    reply = _compiler_reply(
        blueprint,
        provider=provider_name,
        discarded=discarded,
        write_decision=write_decision.effect,
    )
    conv["messages"].append({"role": "user", "content": message})
    conv["messages"].append({"role": "assistant", "content": reply})
    _compiler_save_conversation(tenant_key, conv)

    # 6. Auditoria: la consulta al compilador queda trazada en su EventLog.
    event = Event(
        kind="CompilerChatAnswered",
        entity_id=f"compiler://{blueprint.id}",
        payload={
            "conversation_id": conv_id,
            "mode": _COMPILER_MODE,
            "provider": provider_name,
            "slug": blueprint.slug,
            "write_decision": write_decision.effect,
            "discarded_intents": discarded,
        },
        actor_id="compiler",
        tenant_id=tenant_key,
    )
    _event_log.append(event)

    return CompilerChatResponse(
        reply=reply,
        mode=_COMPILER_MODE,
        tenant_id=tenant_key,
        provider=provider_name,
        blueprint=blueprint.model_dump(mode="json"),
        gate=blueprint.gate,
        write_decision=write_decision.effect,
        discarded_intents=discarded,
        conversation_id=conv_id,
        event_id=getattr(event, "id", None),
    )


# ------------------------------------------------- COMPILER READ-ONLY TOOLS ----
# FASE 3 de PLAN_CLINE_AGENTE_COMPILADOR.md: el compilador trabaja con
# herramientas de LECTURA del repo (registradas en el ToolRegistry como
# `repo_scan`/`repo_file_list`/`repo_file_read`/`repo_search`). La tabla declara
# la capability REAL de cada una, que es lo que evalua la Policy; sin regla
# explicita en la policy del tenant, la capability cae en deny (fail-closed).
_COMPILER_READ_ONLY_TOOLS: Tuple[Tuple[str, str], ...] = (
    ("repo_scan", "repo.file.list"),
    ("repo_file_list", "repo.file.list"),
    ("repo_file_read", "repo.file.read"),
    ("repo_search", "repo.search"),
)


def _compiler_tenant_key(tenant: str, scope: str) -> str:
    """Valida el acceso al compilador y devuelve su slug canonico.

    Contrato unico (compartido por el chat y el catalogo de tools):

    1. tenant del path inexistente -> 404;
    2. tenant de la cabecera distinto del path -> 403 (nunca se actua en
       nombre de otro tenant);
    3. tenant valido pero distinto de `agentic-compiler` -> 404: el compilador
       no es un chat generico de tenant.
    """
    requested = _tenant_registry.get(tenant)
    if requested is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    if scope not in (requested.id, requested.slug):
        raise HTTPException(status_code=403, detail="No autorizado para este tenant")
    if requested.slug != _COMPILER_SLUG:
        raise HTTPException(
            status_code=404,
            detail="Chat de tenant no disponible para este tenant",
        )
    return requested.slug


class CompilerToolOut(BaseModel):
    """Tool de LECTURA del repo disponible para el compilador."""

    name: str
    capability: str
    policy: str
    read_only: bool = True


class CompilerToolsOut(BaseModel):
    """Catalogo de herramientas read-only resuelto contra la Policy del tenant."""

    tenant_id: str
    mode: str
    write_capability: str
    write_decision: str
    tools: List[CompilerToolOut]


@app.get(
    "/api/v1/tenants/{tenant}/compiler/tools",
    response_model=CompilerToolsOut,
)
def compiler_tools(
    tenant: str,
    scope: str = Depends(tenant_scope),
) -> CompilerToolsOut:
    """Catalogo de tools READ-ONLY del compilador (Fase 3), sin ejecutar nada.

    Informativo y fail-closed: cada entrada trae el efecto que la Policy del
    tenant resuelve HOY para esa capability (``allow``/``deny``/
    ``require_approval``). El endpoint no lee el repo ni escribe nada: dice que
    PODRIA ejecutarse, nunca ejecuta.

    Aislamiento: mismo contrato que el chat del compilador — el tenant del path
    debe coincidir con el resuelto por cabecera y ser ``agentic-compiler``.
    """
    tenant_key = _compiler_tenant_key(tenant, scope)
    tools = [
        CompilerToolOut(
            name=name,
            capability=capability,
            policy=_policy_engine.decide(
                tenant_key,
                capability,
                roles=list(_COMPILER_OPERATOR_ROLES),
            ).effect,
        )
        for name, capability in _COMPILER_READ_ONLY_TOOLS
    ]
    write_decision = _policy_engine.decide(
        tenant_key,
        _COMPILER_WRITE_CAPABILITY,
        roles=list(_COMPILER_OPERATOR_ROLES),
    )
    return CompilerToolsOut(
        tenant_id=tenant_key,
        mode=_COMPILER_MODE,
        write_capability=_COMPILER_WRITE_CAPABILITY,
        write_decision=write_decision.effect,
        tools=tools,
    )