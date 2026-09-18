"""Endpoints de missions (spec 17_OBSERVABILITY.md).

Una mision = conjunto de eventos del EventLog con el mismo correlation_id.
Se deriva del log sin tocar el esquema (determinista, sin LLM).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from .rest import tenant_scope

router = APIRouter(prefix="/api/v1/missions", tags=["missions"])


class MissionSummary(BaseModel):
    model_config = ConfigDict(frozen=True)
    correlation_id: str
    tenant_id: str
    event_count: int
    first_at: str
    last_at: str
    kinds: List[str]


class MissionTrace(BaseModel):
    model_config = ConfigDict(frozen=True)
    correlation_id: str
    tenant_id: str
    events: List[Dict[str, Any]]


def _events_for(scope: str) -> List[Any]:
    """Import lazy para ver monkeypatches de rest._event_log."""
    from . import rest as rest_mod
    return rest_mod._event_log.list_for_tenant(scope)


@router.get("", response_model=List[MissionSummary])
def list_missions(scope: str = Depends(tenant_scope)) -> List[MissionSummary]:
    events = _events_for(scope)
    groups: Dict[str, List[Any]] = defaultdict(list)
    for e in events:
        if e.correlation_id:
            groups[e.correlation_id].append(e)
    out: List[MissionSummary] = []
    for cid, evs in groups.items():
        kinds = sorted({(e.kind or e.event_type or "") for e in evs})
        out.append(MissionSummary(
            correlation_id=cid,
            tenant_id=scope,
            event_count=len(evs),
            first_at=min(e.at for e in evs).isoformat(),
            last_at=max(e.at for e in evs).isoformat(),
            kinds=kinds,
        ))
    return sorted(out, key=lambda m: m.last_at, reverse=True)


@router.get("/{correlation_id}/trace", response_model=MissionTrace)
def get_trace(
    correlation_id: str,
    scope: str = Depends(tenant_scope),
) -> MissionTrace:
    events = _events_for(scope)
    matched = [e for e in events if e.correlation_id == correlation_id]
    if not matched:
        raise HTTPException(status_code=404, detail="Mision no encontrada")
    return MissionTrace(
        correlation_id=correlation_id,
        tenant_id=scope,
        events=[
            {
                "id": e.id,
                "kind": e.kind or e.event_type,
                "entity_id": e.entity_id,
                "actor_id": e.actor_id,
                "at": e.at.isoformat(),
                "payload": e.payload or {},
                "command_id": e.command_id,
            }
            for e in sorted(matched, key=lambda e: e.at)
        ],
    )