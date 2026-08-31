"""Tools de Scheduler para el ToolRegistry (FASE 6).

`SchedulerCreateJobTool` es la tool que expone `scheduler_create_job` al
orquestador. Requiere una instancia de `Scheduler` (inyectada por rest.py);
si no hay scheduler, lanza ToolValidationError (contrato FASE 3.3: nunca un
dict con clave "error").
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import Tool, ToolValidationError


class SchedulerCreateJobTool(Tool):
    """Crea un job programado (diario o por intervalo) para un pipeline de un tenant."""

    name = "scheduler_create_job"

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._scheduler is None:
            raise ToolValidationError("scheduler no disponible: no se puede crear job")
        pipeline_id = params.get("pipeline_id", "")
        tenant_id = params.get("tenant_id", "")
        interval_minutes = params.get("interval_minutes")
        hour = params.get("hour")
        if not pipeline_id:
            raise ToolValidationError("faltan campos: pipeline_id es obligatorio")
        if not tenant_id:
            raise ToolValidationError("faltan campos: tenant_id es obligatorio")

        if interval_minutes is not None:
            record = self._scheduler.schedule_interval(
                tenant_id=tenant_id, pipeline_id=pipeline_id, minutes=int(interval_minutes)
            )
        elif hour is not None:
            record = self._scheduler.schedule_daily(
                tenant_id=tenant_id, pipeline_id=pipeline_id, hour=int(hour)
            )
        else:
            raise ToolValidationError("se necesita interval_minutes o hour para crear el job")

        return {
            "status": "SIMULATED",
            "real_execution": False,
            "record": record,
        }


class SchedulerListJobsTool(Tool):
    """Lista los jobs programados de un tenant."""

    name = "scheduler_list_jobs"

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._scheduler is None:
            raise ToolValidationError("scheduler no disponible: no se puede listar jobs")
        tenant_id = params.get("tenant_id", "")
        if not tenant_id:
            raise ToolValidationError("faltan campos: tenant_id es obligatorio")
        return {
            "status": "SIMULATED",
            "real_execution": False,
            "tenant_id": tenant_id,
            "schedules": self._scheduler.list_schedules(tenant_id),
        }


class SchedulerDeleteJobTool(Tool):
    """Elimina un job programado de un tenant."""

    name = "scheduler_delete_job"

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._scheduler is None:
            raise ToolValidationError("scheduler no disponible: no se puede eliminar job")
        tenant_id = params.get("tenant_id", "")
        schedule_id = params.get("schedule_id", "")
        if not tenant_id or not schedule_id:
            raise ToolValidationError(
                "faltan campos: tenant_id y schedule_id son obligatorios"
            )
        removed = self._scheduler.remove_schedule(tenant_id, schedule_id)
        return {
            "status": "SIMULATED",
            "real_execution": False,
            "removed": removed,
        }