from temporalio import activity
from...execution.tools import build_default_registry
from...execution.executor import Executor
from...interfaces.llm.provider import MockLLMProvider
from..pipelines.runner import PipelineRunner

@activity.defn
async def execute_action_activity(pipeline_id: str, tenant_id: str, params: dict):
    registry = build_default_registry()
    executor = Executor(registry=registry)
    runner = PipelineRunner(executor=executor, llm=MockLLMProvider())
    return runner.run(pipeline_id=pipeline_id, tenant_id=tenant_id, params=params)

@activity.defn
async def audit_event_activity(tenant_id: str, pipeline_id: str, result: dict):
    return {"audited": True}
