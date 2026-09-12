import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from.workflows import PipelineWorkflow
from.activities import execute_action_activity, audit_event_activity

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="agentic-os-queue",
        workflows=[PipelineWorkflow],
        activities=[execute_action_activity, audit_event_activity]
    )
    print("Worker Agentic OS corriendo en agentic-os-queue...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
