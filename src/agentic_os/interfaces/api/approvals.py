"""Endpoints de aprobacion humana (spec 14_HUMAN_APPROVAL.md).

Contrato:
- El LLM nunca se auto-aprueba: la resolucion solo viene de este endpoint,
  gobernado por tenant_scope (cabecera X-Tenant-Id / JWT / X-Admin-Key).
- Cada creacion emite ApprovalRequested; cada resolucion emite
  ApprovalGranted o ApprovalRejected en el EventLog del tenant.
- El mailbox en memoria es Fase 1: si el proceso reinicia se pierden los
  pendientes. La fuente de verdad a largo plazo es el EventLog (Fase 2).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from threading import RLock
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ...kernel.types.time import now_utc
from ...kernel.world.events import Event
from .rest import tenant_scope

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


class ApprovalRequestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    tenant_id: str
    actor_id: str
    capability: str
    resource_id: Optional[str] = None
    reason: str = ""
    created_at: datetime
    status: str = "pending"          # pending | approved | rejected
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    note: Optional[str] = None


class DecisionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str = Field(pattern="^(approve|reject)$")
    note: str = ""


# Mailbox en memoria (Fase 1). Fase 2: derivar del EventLog.
_store: Dict[str, ApprovalRequestModel] = {}
_lock = RLock()


def _emit_event(kind: str, payload: Dict[str, Any], tenant_id: str, entity_id: str) -> None:
    """Emite un evento en el EventLog del tenant (lazy import para permitir
    monkeypatch en tests via rest._event_log)."""
    from . import rest as rest_mod

    try:
        rest_mod._event_log.append(
            Event(
                kind=kind,
                entity_id=entity_id,
                tenant_id=tenant_id,
                actor_id="human",
                payload=payload,
            )
        )
    except Exception:
        # El EventLog no debe bloquear la decision de aprobacion.
        pass


def create_approval(
    tenant_id: str,
    actor_id: str,
    capability: str,
    resource_id: Optional[str] = None,
    reason: str = "",
) -> ApprovalRequestModel:
    """Registra una solicitud pendiente. Uso interno y por endpoints."""
    req = ApprovalRequestModel(
        id=f"apr_{uuid.uuid4().hex[:12]}",
        tenant_id=tenant_id,
        actor_id=actor_id,
        capability=capability,
        resource_id=resource_id,
        reason=reason,
        created_at=now_utc(),
    )
    with _lock:
        _store[req.id] = req
    _emit_event(
        "ApprovalRequested",
        {
            "approval_id": req.id,
            "capability": req.capability,
            "resource_id": req.resource_id,
            "reason": req.reason,
        },
        tenant_id=tenant_id,
        entity_id=req.id,
    )
    return req


@router.get("/pending", response_model=List[ApprovalRequestModel])
def list_pending(scope: str = Depends(tenant_scope)) -> List[ApprovalRequestModel]:
    with _lock:
        return [
            r for r in _store.values()
            if r.tenant_id == scope and r.status == "pending"
        ]


@router.post("/{approval_id}/decision", response_model=ApprovalRequestModel)
def decide(
    approval_id: str,
    body: DecisionBody,
    scope: str = Depends(tenant_scope),
) -> ApprovalRequestModel:
    with _lock:
        req = _store.get(approval_id)
        # 404 generico: no revela si existe en otro tenant.
        if req is None or req.tenant_id != scope:
            raise HTTPException(status_code=404, detail="Aprobacion no encontrada")
        if req.status != "pending":
            raise HTTPException(
                status_code=409,
                detail=f"Aprobacion ya resuelta ({req.status})",
            )
        resolved = req.model_copy(update={
            "status": "approved" if body.decision == "approve" else "rejected",
            "resolved_at": now_utc(),
            "resolved_by": "human",   # TODO(auth): extraer del JWT cuando exista
            "note": body.note,
        })
        _store[approval_id] = resolved

    _emit_event(
        "ApprovalGranted" if body.decision == "approve" else "ApprovalRejected",
        {
            "approval_id": resolved.id,
            "capability": resolved.capability,
            "decision": body.decision,
            "note": body.note,
        },
        tenant_id=scope,
        entity_id=resolved.id,
    )
    return resolved