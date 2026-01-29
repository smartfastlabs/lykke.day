"""Miscellaneous background worker tasks."""

from loguru import logger

from lykke.infrastructure.workers.config import broker
from lykke.presentation.utils.structured_logging import structured_task


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
@structured_task()
async def heartbeat_task() -> None:
    """Heartbeat task that runs every minute.

    This is a simple example of a scheduled task that logs a message.
    Useful for verifying that the worker is running and processing tasks.
    """
    logger.info("💓 Heartbeat: Worker is alive and processing tasks")


@broker.task  # type: ignore[untyped-decorator]
@structured_task()
async def example_triggered_task(message: str) -> dict[str, str]:
    """Example task that can be triggered via API.

    This demonstrates a task that can be enqueued on-demand from an API endpoint.

    Args:
        message: A message to include in the task output.

    Returns:
        A dictionary with the task result.
    """
    logger.info(f"Example triggered task received message: {message}")
    return {"status": "completed", "message": message}
