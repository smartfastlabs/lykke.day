"""Client for enqueueing background tasks."""

from uuid import UUID

from planned.presentation.workers.tasks import sync_calendar_task


async def enqueue_sync_calendar(user_id: UUID) -> None:
    """Enqueue a calendar sync task for a user.

    Args:
        user_id: The user ID to sync calendars for.
    """
    # In Taskiq, calling the decorated task function enqueues it
    # Dependencies are injected automatically, only pass user_id
    await sync_calendar_task.kiq(user_id=user_id)  # type: ignore[call-overload]
