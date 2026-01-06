"""Utility endpoints for testing and debugging."""

from fastapi import APIRouter

from planned.presentation.workers.client import enqueue_example_task

router = APIRouter()


@router.get("/trigger-example-task")
async def trigger_example_task(message: str = "Hello from API") -> dict[str, str]:
    """Trigger an example background task.

    This endpoint enqueues an example task to demonstrate triggering
    TaskIQ jobs from API endpoints.

    Args:
        message: Optional message to include in the task (query param).

    Returns:
        A confirmation that the task was enqueued.
    """
    await enqueue_example_task(message=message)
    return {"status": "enqueued", "message": message}

