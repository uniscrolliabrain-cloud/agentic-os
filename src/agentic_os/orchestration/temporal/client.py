import os
import uuid
from temporalio.client import Client

_client = None

async def get_client():
    global _client
    if _client is None:
        host = os.getenv("TEMPORAL_HOST", "localhost:7233")
        _client = await Client.connect(host)
    return _client

async def start_pipeline(pipeline_id: str, tenant_id: str, params: dict | None = None):
    client = await get_client()
    wf_id = f"{tenant_id}-{pipeline_id}-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        "PipelineWorkflow",
        args=[pipeline_id, tenant_id, params or {}],
        id=wf_id,
        task_queue="agentic-os-queue",
    )
    return handle.id
