from temporalio.client import Client

_client = None

async def get_client():
    global _client
    if _client is None:
        _client = await Client.connect("localhost:7233")
    return _client

async def start_pipeline(pipeline_id: str, tenant_id: str, params: dict = {}):
    client = await get_client()
    handle = await client.start_workflow(
        "PipelineWorkflow",
        args=[pipeline_id, tenant_id, params],
        id=f"{tenant_id}-{pipeline_id}",
        task_queue="agentic-os-queue",
    )
    return handle.id
