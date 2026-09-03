from __future__ import annotations

import json
import logging
import uuid
from ..kernel.types.time import now_utc
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ..kernel.world.events import Event

logger = logging.getLogger(__name__)

DATA_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
    .parent
    / "data"
)


class Scheduler:

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        event_log: Any = None,
        on_trigger: Optional[Callable] = None,
    ):

        self.data_dir = (
            Path(data_dir)
            if data_dir
            else DATA_DIR
        )

        self.event_log = event_log
        self.on_trigger = on_trigger

        try:
            from apscheduler.schedulers.background import (
                BackgroundScheduler,
            )

            self._scheduler = BackgroundScheduler(
                daemon=True
            )

            self._aps_available = True

        except Exception:
            self._scheduler = None
            self._aps_available = False

        self._running = False

    def _tenant_dir(
        self,
        tenant_id: str,
    ) -> Path:

        path = (
            self.data_dir
            / "tenants"
            / tenant_id
        )

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def _schedules_file(
        self,
        tenant_id: str,
    ) -> Path:

        return (
            self._tenant_dir(tenant_id)
            / "schedules.json"
        )

    def _load(
        self,
        tenant_id: str,
    ) -> list:

        path = self._schedules_file(
            tenant_id
        )

        if not path.exists():
            return []

        try:
            return json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return []

    def _save(
        self,
        tenant_id: str,
        schedules: list,
    ) -> None:

        path = self._schedules_file(
            tenant_id
        )

        tmp = path.with_suffix(
            ".tmp"
        )

        tmp.write_text(
            json.dumps(
                schedules,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        tmp.replace(path)

    def _emit(
        self,
        kind: str,
        tenant_id: str,
        pipeline_id: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> None:

        if self.event_log is None:
            return

        self.event_log.append(
            Event(
                kind=kind,
                entity_id=(
                    f"scheduler://"
                    f"{pipeline_id}"
                ),
                tenant_id=tenant_id,
                actor_id="scheduler",
                payload=payload,
                correlation_id=correlation_id,
                command_id=command_id,
            )
        )

    def _fire(
        self,
        tenant_id: str,
        pipeline_id: str,
        schedule_id: str,
    ) -> None:

        correlation_id = (
            f"sched-{uuid.uuid4().hex}"
        )

        command_id = (
            f"cmd-{uuid.uuid4().hex}"
        )

        self._emit(
            "ScheduledPipelineStarted",
            tenant_id,
            pipeline_id,
            {
                "schedule_id": schedule_id,
                "pipeline_id": pipeline_id,
            },
            correlation_id,
            command_id,
        )

        if self.on_trigger is None:
            return

        try:

            self.on_trigger(
                pipeline_id,
                tenant_id,
                correlation_id,
                command_id,
            )

        except Exception as error:

            logger.exception(
                "Scheduled pipeline failed"
            )

            self._emit(
                "ScheduledPipelineFailed",
                tenant_id,
                pipeline_id,
                {
                    "schedule_id": schedule_id,
                    "error": str(error)[:300],
                },
                correlation_id,
                command_id,
            )

    def schedule_daily(
        self,
        tenant_id: str,
        pipeline_id: str,
        hour: int,
    ) -> dict:

        if not 0 <= hour <= 23:
            raise ValueError(
                "hour debe estar entre 0 y 23"
            )

        schedule_id = self._new_id()

        if self._aps_available:

            self._scheduler.add_job(
                self._fire,
                trigger="cron",
                hour=hour,
                minute=0,
                id=schedule_id,
                args=[
                    tenant_id,
                    pipeline_id,
                    schedule_id,
                ],
                replace_existing=True,
            )

        record = {
            "id": schedule_id,
            "tenant_id": tenant_id,
            "pipeline_id": pipeline_id,
            "kind": "daily",
            "hour": hour,
            "created_at": (
                now_utc().isoformat()
            ),
        }

        self._save(
            tenant_id,
            self._load(tenant_id)
            + [record],
        )

        return record

    def schedule_interval(
        self,
        tenant_id: str,
        pipeline_id: str,
        minutes: int,
    ) -> dict:

        if minutes < 1:
            raise ValueError(
                "minutes debe ser >= 1"
            )

        schedule_id = self._new_id()

        if self._aps_available:

            self._scheduler.add_job(
                self._fire,
                trigger="interval",
                minutes=minutes,
                id=schedule_id,
                args=[
                    tenant_id,
                    pipeline_id,
                    schedule_id,
                ],
                replace_existing=True,
            )

        record = {
            "id": schedule_id,
            "tenant_id": tenant_id,
            "pipeline_id": pipeline_id,
            "kind": "interval",
            "minutes": minutes,
            "created_at": (
                now_utc().isoformat()
            ),
        }

        self._save(
            tenant_id,
            self._load(tenant_id)
            + [record],
        )

        return record

    def list_schedules(
        self,
        tenant_id: str,
    ) -> list:

        return self._load(
            tenant_id
        )

    def remove_schedule(
        self,
        tenant_id: str,
        schedule_id: str,
    ) -> bool:

        before = self._load(
            tenant_id
        )

        after = [
            item
            for item in before
            if item.get("id")
            != schedule_id
        ]

        if len(before) == len(after):
            return False

        if self._aps_available:

            try:
                self._scheduler.remove_job(
                    schedule_id
                )
            except Exception as exc:  # noqa: BLE001
                # El job puede no existir en APS (p.ej. creado antes de start):
                # el borrado del store (abajo) es la fuente de verdad, pero el
                # fallo no se silencia.
                logger.warning(
                    "remove_job(%s) falló en APScheduler: %s",
                    schedule_id,
                    exc,
                )

        self._save(
            tenant_id,
            after,
        )

        return True

    def start(self) -> None:

        if (
            self._aps_available
            and not self._running
        ):
            self._scheduler.start()
            self._running = True

    def shutdown(self) -> None:

        if (
            self._aps_available
            and self._running
        ):
            self._scheduler.shutdown(
                wait=False
            )
            self._running = False

    @staticmethod
    def _new_id() -> str:
        return (
            f"sch_"
            f"{uuid.uuid4().hex[:12]}"
        )
