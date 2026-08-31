"""Scheduler real con APScheduler (FASE 6)."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ..kernel.world.events import Event

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


class Scheduler:
    """Programa pipelines por tenant (diario o por intervalo) usando APScheduler.

    Persistencia: data/tenants/{tenant_id}/schedules.json (sin Redis).
    Al disparar, llama a un callback (p.ej. orchestrator.handle_pipeline) y
    deja un evento ScheduledPipelineStarted en el EventLog.
    Todo es per-tenant: nunca lee/escribe schedules de otro tenant.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        event_log: Any = None,
        on_trigger: Optional[Callable[[str, str], Any]] = None,
    ):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.event_log = event_log
        self.on_trigger = on_trigger

        try:
            from apscheduler.schedulers.background import BackgroundScheduler as _BS

            self._scheduler = _BS(daemon=True)
            self._aps_available = True
        except Exception as exc:  # pragma: no cover - apscheduler ausente en tests aislados
            logger.warning(
                "APScheduler no disponible (%s); los schedules se persisten pero no se disparan", exc
            )
            self._scheduler = None
            self._aps_available = False
        self._running = False

    # ------------------------------------------------------------------ paths
    def _tenant_dir(self, tenant_id: str) -> Path:
        d = self.data_dir / "tenants" / tenant_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _schedules_file(self, tenant_id: str) -> Path:
        return self._tenant_dir(tenant_id) / "schedules.json"

    def _load(self, tenant_id: str) -> list:
        f = self._schedules_file(tenant_id)
        if not f.exists():
            return []
        try:
            with open(f, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, tenant_id: str, schedules: list) -> None:
        f = self._schedules_file(tenant_id)
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(schedules, fh, ensure_ascii=False, indent=2)
# ------------------------------------------------------------- scheduling
    def _emit(self, kind: str, tenant_id: str, pipeline_id: str, payload: Dict[str, Any]) -> None:
        if self.event_log is None:
            return
        try:
            self.event_log.append(
                Event(
                    kind=kind,
                    entity_id=f"scheduler://{pipeline_id}",
                    tenant_id=tenant_id,
                    actor_id="scheduler",
                    payload=payload,
                )
            )
        except Exception:  # noqa: BLE001 - auditar nunca rompe
            pass

    def _fire(self, tenant_id: str, pipeline_id: str, schedule_id: str) -> None:
        """Ejecutado por APScheduler cuando toca. Nunca rompe el hilo."""
        self._emit(
            "ScheduledPipelineStarted", tenant_id, pipeline_id,
            {"schedule_id": schedule_id, "pipeline_id": pipeline_id},
        )
        if self.on_trigger is not None:
            try:
                self.on_trigger(pipeline_id, tenant_id)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Pipeline %s falló para tenant %s", pipeline_id, tenant_id)
                self._emit(
                    "ScheduledPipelineFailed", tenant_id, pipeline_id, {"error": str(exc)[:300]}
                )

    def schedule_daily(self, tenant_id: str, pipeline_id: str, hour: int) -> dict:
        """Programa un pipeline a la misma hora cada día (hora local del servidor)."""
        schedule_id = self._new_id()
        if self._aps_available:
            self._scheduler.add_job(
                self._fire,
                trigger="cron",
                hour=hour,
                minute=0,
                id=schedule_id,
                args=[tenant_id, pipeline_id, schedule_id],
                replace_existing=True,
            )
        record = {
            "id": schedule_id,
            "tenant_id": tenant_id,
            "pipeline_id": pipeline_id,
            "kind": "daily",
            "hour": int(hour),
            "created_at": datetime.utcnow().isoformat(),
        }
        self._save(tenant_id, self._load(tenant_id) + [record])
        return record

    def schedule_interval(self, tenant_id: str, pipeline_id: str, minutes: int) -> dict:
        """Programa un pipeline cada N minutos."""
        schedule_id = self._new_id()
        if self._aps_available:
            self._scheduler.add_job(
                self._fire,
                trigger="interval",
                minutes=int(minutes),
                id=schedule_id,
                args=[tenant_id, pipeline_id, schedule_id],
                replace_existing=True,
            )
        record = {
            "id": schedule_id,
            "tenant_id": tenant_id,
            "pipeline_id": pipeline_id,
            "kind": "interval",
            "minutes": int(minutes),
            "created_at": datetime.utcnow().isoformat(),
        }
        self._save(tenant_id, self._load(tenant_id) + [record])
        return record

    def list_schedules(self, tenant_id: str) -> list:
        return self._load(tenant_id)

    def remove_schedule(self, tenant_id: str, schedule_id: str) -> bool:
        before = self._load(tenant_id)
        schedules = [s for s in before if s.get("id") != schedule_id]
        if len(schedules) == len(before):
            return False
        if self._aps_available:
            try:
                self._scheduler.remove_job(schedule_id)
            except Exception:  # noqa: BLE001 - el job puede no existir ya
                pass
        self._save(tenant_id, schedules)
        return True

    def start(self) -> None:
        if self._aps_available and not self._running:
            self._scheduler.start()
            self._running = True

    def shutdown(self) -> None:
        if self._aps_available and self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False

    @staticmethod
    def _new_id() -> str:
        return f"sch_{uuid.uuid4().hex[:10]}"
