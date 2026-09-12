from __future__ import annotations

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Importa el nombre de la activity, no la funcion directamente para evitar ciclos
# Workflow solo conoce strings

@workflow.defn
class PipelineWorkflow:
    @workflow.run
    async def run(self, pipeline_id: str, tenant_id: str, params: dict | None = None):
        params = params or {}

        # Retry durable por step
        retry = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=2))

        # 1. Ejecuta el pipeline (cada tool dentro ya tiene su propia auditoria en EventLog)
        result = await workflow.execute_activity(
            "execute_action_activity",
            args=[pipeline_id, tenant_id, params],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry,
        )

        # 2. Audit final (no bloqueante si falla)
        try:
            await workflow.execute_activity(
                "audit_event_activity",
                args=[tenant_id, pipeline_id, result],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
        except Exception:
            # No falla el workflow por audit
            pass

        return result
