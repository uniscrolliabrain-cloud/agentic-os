from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from typing import Any, Dict, List, Optional
from ..types.ids import new_id
from ..types.time import now_utc
from datetime import datetime
import threading

class Event(BaseModel):
    """
    Evento inmutable del sistema.
    INVARIANTE: todo evento pertenece a un tenant. No existe evento sin tenant_id.
    """
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    kind: str
    entity_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    at: datetime = Field(default_factory=now_utc)
    actor_id: Optional[str] = None
    # NUEVO - cimiento multi-tenant (hallazgo GPT + Claude)
    tenant_id: str = Field(description="Tenant al que pertenece el evento. Obligatorio para aislamiento")

    def __str__(self) -> str:
        return f"Event[{self.tenant_id}:{self.kind}:{self.entity_id}]"

class EventLog(BaseModel):
    """
    Lista en memoria de eventos.
    NOTA: Esta clase ahora es solo para tests y compatibilidad.
    En producción usaremos EventLogRepository (Jsonl/Postgres) que es thread-safe y persistente.
    Mantenemos RLock aquí para no romper nada mientras migramos.
    """
    events: List[Event] = Field(default_factory=list)
    _lock: threading.RLock = PrivateAttr(default_factory=threading.RLock)

    def append(self, e: Event) -> None:
        # Thread-safe append (FASE 0.5)
        with self._lock:
            # Validación de cimiento: no permitir evento sin tenant_id
            if not e.tenant_id:
                raise ValueError("Event sin tenant_id rechazado - viola invariante multi-tenant")
            self.events.append(e)

    def for_tenant(self, tenant_id: str) -> List[Event]:
        """Filtro por tenant - evita mezclar empresas ficticias"""
        with self._lock:
            return [ev for ev in self.events if ev.tenant_id == tenant_id]

    def all_events(self) -> List[Event]:
        """FASE 3.1: método común de la interfaz EventLogRepository.

        Bugfix de tipo en kernel/ (no feature): antes replay() leía
        `.events` directamente, atributo que no existe en JsonlEventLog ni
        en PostgresEventLog -> AttributeError en runtime. Devuelve copia.
        """
        with self._lock:
            return list(self.events)

    def __len__(self):
        with self._lock:
            return len(self.events)
