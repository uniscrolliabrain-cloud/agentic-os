import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from.workflows import PipelineWorkflow
from.activities import execute_action_activity, audit_event_activity

async def main():
    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(host)
    worker = Worker(
        client,
        task_queue="agentic-os-queue",
        workflows=[PipelineWorkflow],
        activities=[execute_action_activity, audit_event_activity]
    )
    print(f"Worker Agentic OS corriendo en {host} / agentic-os-queue...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
