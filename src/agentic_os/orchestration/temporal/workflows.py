from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn
class PipelineWorkflow:
    @workflow.run
    async def run(self, pipeline_id: str, tenant_id: str, params: dict = {}):
        result = await workflow.execute_activity(
            "execute_action_activity",
            args=[pipeline_id, tenant_id, params],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        return result
