from __future__ import annotations

import hmac
import json
import logging
import threading
import uuid
from datetime import timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ...cognition.beliefs.belief import Belief
from ...cognition.planning.intent import Intent
from ...cognition.skills.library import SKILLS
from ...execution.executor import Executor
from ...execution.tools import build_default_registry
from ...infrastructure.config.settings import settings
from ...infrastructure.persistence import get_eventlog_repo
from ...infrastructure.tenancy import Tenant, TenantConfig, TenantConfigPublic, TenantContext, TenantRegistry
from ...interfaces.llm.chat import FrontAssistant
from ...interfaces.llm.provider import BaseLLMProvider, FallbackLLMProvider, GeminiProvider, GroqProvider, MockLLMProvider
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


def _secret_matches(provided: Optional[str], expected: Optional[str]) -> bool:
    return provided is not None and expected is not None and hmac.compare_digest(provided, expected)


def _credentials_expired(tenant: Tenant) -> bool:
    expires_at = tenant.config.credentials_expires_at
    if expires_at is None:
        return False
    now = now_utc()
    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = expires_at.astimezone(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    return now > expires_at


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
                if _credentials_expired(tenant):
                    raise HTTPException(
                        status_code=401,
                        detail="Credenciales del tenant expiradas: contacta al administrador",
                    )
                return tenant.id
            logger.warning(
                "JWT tenant_id '%s' no registrado; usando scope por defecto",
                tenant_id,
            )
        return _DEFAULT_SCOPE

    if not x_tenant_id:
        return _DEFAULT_SCOPE
    tenant = _tenant_registry.get(x_tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if _credentials_expired(tenant):
        raise HTTPException(
            status_code=401,
            detail="Credenciales del tenant expiradas: contacta al administrador",
        )

    if settings.admin_api_key and (
        _secret_matches(x_admin_key, settings.admin_api_key)
        or _secret_matches(x_api_key, settings.admin_api_key)
    ):
        return tenant.id

    expected_key = tenant.config.credentials.get("api_key")
    if expected_key:
        if not _secret_matches(x_api_key, str(expected_key)):
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
    if _secret_matches(x_admin_key, admin_key) or _secret_matches(x_api_key, admin_key):
        return True
    raise HTTPException(status_code=401, detail="Admin API key requerida o inválida")

_event_log = get_eventlog_repo()

def _build_llm(
    model_name: str,
    fallback_model_name: str,
    mock_response: str = "{}",
) -> BaseLLMProvider:
    primary = None
    fallback = None
    if settings.gemini_api_key:
        try:
            primary = GeminiProvider(api_key=settings.gemini_api_key, model=model_name)
        except Exception:
            primary = None
    groq_key = getattr(settings, 'groq_api_key', None) or getattr(settings, 'GROQ_API_KEY', None)
    if groq_key:
        try:
            fallback = GroqProvider(api_key=groq_key, model=fallback_model_name)
        except Exception:
            fallback = None
    if primary and fallback:
        return FallbackLLMProvider(primary=primary, fallback=fallback)
    if primary:
        return primary
    if fallback:
        return fallback
    return MockLLMProvider(default_response=mock_response)


_chat_mock_response = (
    "Hola, soy el asistente de AGENTE OS (modo mock). "
    "Configura GEMINI_API_KEY o GROQ_API_KEY para respuestas reales."
)
_orchestrator_mock_response = json.dumps({
    "intents": [{
        "goal": "responder al usuario",
        "kind": "reply_to_user",
        "entity_id": "n/a",
        "payload": {},
        "rationale": "mock sin API key",
        "reply_to_user": _chat_mock_response,
        "confidence": 1.0,
        "requires_approval": False,
        "risk_level": "low",
        "source_belief_ids": [],
    }]
})
_chat_llm = _build_llm(
    settings.gemini_chat_model,
    settings.groq_chat_model,
    mock_response=_chat_mock_response,
)
_llm = _build_llm(
    settings.gemini_model,
    settings.groq_model,
    mock_response=_orchestrator_mock_response,
)
_orchestrator = Orchestrator(log=_event_log, llm=_llm)
_front_assistant = FrontAssistant(
    model_name=settings.gemini_chat_model,
    api_key=None,
    temperature=settings.gemini_temperature,
    provider=_chat_llm,
)

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
}

def _map_kind_to_action(kind: Optional[str]) -> Optional[str]:
    """Resuelve el kind canónico de un Intent a su action del Executor.

    Determinista: lookup exacto en ACTION_BY_KIND (normalizado). Un kind
    desconocido → None (no se ejecuta nada; fail-closed).
    """
    return ACTION_BY_KIND.get((kind or "").strip().lower())


_ASSISTANT_AGENT_ID = "front_assistant"


def _cognition_store(tenant_id: str) -> Any:
    if _cognition_registry is None:
        return None
    return _cognition_registry.for_agent(tenant_id, _ASSISTANT_AGENT_ID)


def _belief(
    kind: str,
    key: Optional[str],
    content: Dict[str, Any],
    confidence: Any,
    source_id: Optional[str],
    agent_id: str,
) -> Belief:
    try:
        score = float(confidence)
    except (TypeError, ValueError):
        score = 0.5
    return Belief(
        kind=kind,
        key=key,
        content=content,
        confidence=max(0.0, min(1.0, score)),
        source_observation_id=source_id,
        source_agent_id=agent_id,
    )


def _memory_beliefs(store: Any, query: str) -> List[Belief]:
    if store is None:
        return []
    context = store.context(query=query, k=10)
    beliefs: List[Belief] = []
    for item in context.get("working", []):
        beliefs.append(_belief(
            "working",
            f"working:{item.get('id')}",
            {"content": item.get("content", ""), "metadata": item.get("metadata", {})},
            item.get("metadata", {}).get("confidence", 0.8),
            item.get("id"),
            _ASSISTANT_AGENT_ID,
        ))
    for event in context.get("episodic_recent", []):
        beliefs.append(_belief(
            "episodic",
            f"episodic:{event.get('id')}",
            {"event_type": event.get("event_type", ""), "payload": event.get("payload", {})},
            0.9,
            event.get("id"),
            _ASSISTANT_AGENT_ID,
        ))
    for fact in context.get("semantic", []):
        beliefs.append(_belief(
            "semantic",
            fact.get("key"),
            {"value": fact.get("value")},
            fact.get("confidence", 1.0),
            fact.get("source_belief_id") or fact.get("id"),
            _ASSISTANT_AGENT_ID,
        ))
    for skill in context.get("procedural", []):
        beliefs.append(_belief(
            "procedural",
            f"procedure:{skill.get('name')}",
            {
                "name": skill.get("name", ""),
                "description": skill.get("description", ""),
                "steps": skill.get("steps", []),
                "version": skill.get("version", 1),
            },
            1.0,
            skill.get("id"),
            _ASSISTANT_AGENT_ID,
        ))
    return beliefs


def _memory_domain_context(store: Any, query: str) -> Optional[str]:
    if store is None:
        return None
    context = store.context(query=query, k=10)
    return json.dumps({
        "semantic": context.get("semantic", []),
        "procedural": context.get("procedural", []),
    }, ensure_ascii=False, default=str)


def _remember_chat(
    tenant_id: str,
    message: str,
    reply: str,
    conversation_id: Optional[str],
    correlation_id: str,
) -> None:
    store = _cognition_store(tenant_id)
    if store is None:
        return
    try:
        store.working_add(
            f"User: {message}\nAssistant: {reply}",
            metadata={"conversation_id": conversation_id, "source": "chat"},
        )
        store.episodic_append(
            "chat_turn",
            payload={
                "user_message": message,
                "assistant_reply": reply,
                "conversation_id": conversation_id,
            },
            correlation_id=correlation_id,
        )
    except Exception as exc:
        logger.warning("no se pudo persistir memoria de chat: %s", exc)


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, default=str))
    except Exception:
        return str(value)


def _remember_orchestration_result(
    tenant_id: str,
    intent_data: Dict[str, Any],
    outcome: Dict[str, Any],
    correlation_id: str,
) -> None:
    store = _cognition_store(tenant_id)
    if store is None:
        return
    try:
        store.episodic_append(
            "intent_processed",
            payload={
                "intent": intent_data,
                "action": outcome.get("action"),
                "policy_effect": outcome.get("policy_effect"),
                "note": outcome.get("note"),
            },
            correlation_id=correlation_id,
        )
        store.working_add(
            f"Intent {intent_data.get('kind')}: {outcome.get('note') or 'processed'}",
            metadata={
                "action": outcome.get("action"),
                "policy_effect": outcome.get("policy_effect"),
                "correlation_id": correlation_id,
            },
        )
    except Exception as exc:
        logger.warning("no se pudo persistir resultado de orquestacion: %s", exc)


def _execute_intent(
    intent: Intent,
    tenant_id: str,
    correlation_id: str,
    command_id: str,
) -> Dict[str, Any]:
    action = _map_kind_to_action(intent.kind)
    if action is None:
        return {
            "action": None,
            "policy_effect": "not_mapped",
            "reason": f"sin tool para '{intent.kind}'",
            "result": None,
            "note": f"sin tool para '{intent.kind}'",
        }

    tenant = _tenant_registry.get(tenant_id)
    if tenant is None:
        return {
            "action": action,
            "policy_effect": "deny",
            "reason": f"tenant {tenant_id} no registrado",
            "result": None,
            "note": f"tenant {tenant_id} no registrado",
        }

    try:
        decision = _policy_engine.decide(
            tenant_id=tenant.id,
            capability=action,
            resource_kind=intent.kind,
            roles=["director"],
        )
    except Exception as exc:
        return {
            "action": action,
            "policy_effect": "deny",
            "reason": f"policy error: {exc}",
            "result": None,
            "note": f"policy error: {exc}",
        }

    if decision.effect != "allow":
        kind = "ApprovalRequired" if decision.effect == "require_approval" else "ActionDenied"
        _event_log.append(
            Event(
                kind=kind,
                entity_id=intent.id,
                payload={
                    "action": action,
                    "intent_id": intent.id,
                    "reason": decision.reason,
                },
                actor_id="orchestrator",
                tenant_id=tenant.id,
                correlation_id=correlation_id,
                command_id=command_id,
            )
        )
        return {
            "action": action,
            "policy_effect": decision.effect,
            "reason": decision.reason,
            "result": None,
            "note": f"{decision.effect}: {decision.reason}",
        }

    if intent.requires_approval or intent.risk_level != "low":
        _event_log.append(
            Event(
                kind="ApprovalRequired",
                entity_id=intent.id,
                payload={
                    "action": action,
                    "intent_id": intent.id,
                    "reason": "intent marca aprobación o riesgo no bajo",
                    "risk_level": intent.risk_level,
                },
                actor_id="orchestrator",
                tenant_id=tenant.id,
                correlation_id=correlation_id,
                command_id=command_id,
            )
        )
        return {
            "action": action,
            "policy_effect": "require_approval",
            "reason": "intent requiere aprobación o tiene riesgo no bajo",
            "result": None,
            "note": "requiere aprobación humana",
        }

    params = dict(intent.payload)
    params.pop("tenant_id", None)
    params["rationale"] = intent.rationale
    result = _executor.execute(
        action=action,
        params=params,
        context=TenantContext(tenant=tenant),
        tenant_id=tenant.id,
        roles=["director"],
        correlation_id=correlation_id,
        command_id=command_id,
        actor_id="orchestrator",
    )
    if not result.get("success"):
        note = f"rechazada/fallo '{action}': {result.get('error')}"
    else:
        note = f"ejecutada '{action}'"
    return {
        "action": action,
        "policy_effect": decision.effect,
        "reason": None,
        "result": result,
        "note": note,
    }


def _try_execute(action: Optional[str], intent: Intent, tenant_id: str) -> str:
    if action is None:
        return "sin herramienta concreta"
    outcome = _execute_intent(
        intent,
        tenant_id,
        correlation_id=f"corr-{uuid.uuid4().hex}",
        command_id=f"cmd-{uuid.uuid4().hex}",
    )
    return str(outcome["note"])

def _start_orchestration_task(
    message: str,
    conversation_id: Optional[str] = None,
    tenant_id: str = "system",
    correlation_id: Optional[str] = None,
    command_id: Optional[str] = None,
    beliefs: Optional[List[Belief]] = None,
    domain_context: Optional[str] = None,
) -> str:
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    correlation_id = correlation_id or f"corr-{uuid.uuid4().hex}"
    command_id = command_id or f"cmd-{uuid.uuid4().hex}"
    store = _cognition_store(tenant_id)
    beliefs = beliefs if beliefs is not None else _memory_beliefs(store, message)
    domain_context = domain_context if domain_context is not None else _memory_domain_context(store, message)
    with _tasks_lock:
        _background_tasks[task_id] = {
            "id": task_id,
            "tenant_id": tenant_id,
            "status": "running",
            "message": message,
            "summary": "",
            "correlation_id": correlation_id,
            "command_id": command_id,
            "started_at": now_utc().isoformat(),
        }

    def _run() -> None:
        try:
            intent = _orchestrator.handle_user_message(
                message,
                tenant_id=tenant_id,
                beliefs=beliefs,
                domain_context=domain_context,
                correlation_id=correlation_id,
                command_id=command_id,
            )
            intent_data = intent.model_dump(mode="json")
            if intent.kind == "reply_to_user":
                outcome = {
                    "action": None,
                    "policy_effect": "not_applicable",
                    "reason": None,
                    "result": None,
                    "note": intent.reply_to_user or "respuesta conversacional; sin accion",
                }
            else:
                outcome = _execute_intent(
                    intent,
                    tenant_id,
                    correlation_id,
                    command_id,
                )
            _remember_orchestration_result(
                tenant_id,
                intent_data,
                outcome,
                correlation_id,
            )
            routing = "deterministic" if intent.rationale == "deterministic router" else "llm"
            summary = f"Intent '{intent.kind}' procesado"
            if outcome.get("note"):
                summary += f" · {outcome['note']}"
            _event_log.append(
                Event(
                    kind="BackgroundProcessingDone",
                    entity_id=task_id,
                    payload={
                        "task_id": task_id,
                        "intent": intent_data,
                        "intent_kind": intent.kind,
                        "reply_to_user": intent.reply_to_user,
                        "routing": routing,
                        "action": outcome.get("action"),
                        "policy_effect": outcome.get("policy_effect"),
                        "result": _json_safe(outcome.get("result")),
                        "note": outcome.get("note"),
                    },
                    actor_id="orchestrator",
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                    command_id=command_id,
                )
            )
            with _tasks_lock:
                _background_tasks[task_id].update(
                    status="completed",
                    summary=summary,
                    intent=intent_data,
                    reply_to_user=intent.reply_to_user,
                    action=outcome.get("action"),
                    policy_effect=outcome.get("policy_effect"),
                    result=_json_safe(outcome.get("result")),
                    note=outcome.get("note"),
                    ended_at=now_utc().isoformat(),
                )
        except Exception as e:
            store = _cognition_store(tenant_id)
            if store is not None:
                try:
                    store.episodic_append(
                        "orchestration_failed",
                        payload={"error": str(e)},
                        correlation_id=correlation_id,
                    )
                except Exception:
                    pass
            _event_log.append(
                Event(
                    kind="BackgroundProcessingFailed",
                    entity_id=task_id,
                    payload={"task_id": task_id, "error": str(e)},
                    actor_id="orchestrator",
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                    command_id=command_id,
                )
            )
            with _tasks_lock:
                _background_tasks[task_id].update(
                    status="failed",
                    summary=str(e),
                    ended_at=now_utc().isoformat(),
                )

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
    store = _cognition_store(scope)
    try:
        memory_context = store.context(query=message, k=5) if store is not None else None
    except Exception:
        memory_context = None
    try:
        reply = _front_assistant.answer(
            message,
            tenant_knowledge_dir=kb_arg,
            memory_context=memory_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"El asistente no pudo responder: {e}")
    if req.conversation_id:
        try:
            _append_message_to_conversation(req.conversation_id, "assistant", reply, scope)
        except HTTPException:
            pass
    correlation_id = f"corr-{uuid.uuid4().hex}"
    command_id = f"cmd-{uuid.uuid4().hex}"
    store = _cognition_store(scope)
    beliefs = _memory_beliefs(store, message)
    domain_context = _memory_domain_context(store, message)
    task_id = _start_orchestration_task(
        message,
        conversation_id=req.conversation_id,
        tenant_id=scope,
        correlation_id=correlation_id,
        command_id=command_id,
        beliefs=beliefs,
        domain_context=domain_context,
    )
    _remember_chat(
        tenant_id=scope,
        message=message,
        reply=reply,
        conversation_id=req.conversation_id,
        correlation_id=correlation_id,
    )
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

            try:
                wf_id = asyncio.run(_start())
            except RuntimeError:
                wf_id = None
            if wf_id is None:
                raise RuntimeError("no se pudo ejecutar Temporal desde el scheduler")

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
    _cognition_registry = CognitionRegistry(base_dir=DATA_DIR)
    _cognition_registry._base_dir = DATA_DIR
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

