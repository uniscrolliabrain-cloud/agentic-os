from __future__ import annotations

from temporalio import activity

from agentic_os.execution.tools import build_default_registry
from agentic_os.execution.executor import Executor
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.infrastructure.persistence import get_eventlog_repo
from agentic_os.interfaces.llm.provider import MockLLMProvider
from agentic_os.orchestration.pipelines.runner import PipelineRunner

@activity.defn
async def execute_action_activity(pipeline_id: str, tenant_id: str, params: dict):
    # Estos se instancian dentro de la activity porque no son serializables fuera
    registry = build_default_registry()
    event_log = get_eventlog_repo()
    policy = PolicyEngine()
    executor = Executor(registry=registry, event_log=event_log, policy_engine=policy)
    
    # Usa Mock por ahora, luego inyectas GeminiProvider con settings
    runner = PipelineRunner(executor=executor, llm=MockLLMProvider())
    
    activity.logger.info(f"Ejecutando pipeline {pipeline_id} para tenant {tenant_id}")
    
    result = runner.run(pipeline_id=pipeline_id, tenant_id=tenant_id, params=params)
    return result

@activity.defn
async def audit_event_activity(tenant_id: str, pipeline_id: str, result: dict):
    activity.logger.info(f"Audit {tenant_id}/{pipeline_id}: {result.get('status')}")
    return {"audited": True, "tenant_id": tenant_id, "pipeline_id": pipeline_id}
